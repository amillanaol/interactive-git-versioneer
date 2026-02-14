"""
Menús interactivos para gestión de versiones.

Contiene los menús y submenús para la interfaz de usuario.
"""

from typing import List

import git

from ..core.git_ops import get_last_tag, get_next_version
from ..core.models import Commit
from ..core.ui import (
    Colors,
    Menu,
    clear_screen,
    get_menu_input,
    print_subheader,
    wait_for_enter,
)
from ..releases.changelog_actions import get_latest_changelog_section
from .actions import (
    apply_tags,
    change_last_tag,
    clean_all_tags,
    push_tags_to_remote,
    sync_tags_from_remote,
)
from .ai import auto_generate_all_with_ai, generate_ai_message
from .views import (
    select_commit_from_list,
    show_commit_details,
    show_commit_list,
    show_local_tags,
    show_remote_tags,
    show_tag_preview,
)


def show_commit_submenu(
    repo: git.Repo, commit: Commit, commit_index: int, all_commits: List[Commit]
) -> None:
    """Menú para procesar un commit individual."""
    try:
        while True:
            clear_screen()
            print_subheader(
                f"PROCESANDO COMMIT [{commit_index + 1}/{len(all_commits)}]"
            )

            display_message = commit.custom_message or commit.message
            print(
                f"Commit: {Colors.CYAN}{commit.hash[:7]} - {display_message}{Colors.RESET}"
            )
            print()
            print(f"{Colors.WHITE}1. Ver detalles completos{Colors.RESET}")
            print(
                f"{Colors.WHITE}2. Asignar tipo: MAJOR (versión principal){Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}3. Asignar tipo: MINOR (nueva funcionalidad){Colors.RESET}"
            )
            print(f"{Colors.WHITE}4. Asignar tipo: PATCH (corrección){Colors.RESET}")
            print(f"{Colors.WHITE}5. Asignar mensaje personalizado{Colors.RESET}")
            print(f"{Colors.WHITE}6. Marcar como procesado{Colors.RESET}")
            print(f"{Colors.WHITE}7. Generar tag con IA (Groq/OpenAI){Colors.RESET}")
            print(f"{Colors.WHITE}0. Volver{Colors.RESET}")
            print()

            choice = get_menu_input(
                f"{Colors.WHITE}Seleccione opción: {Colors.RESET}"
            ).strip()

            # Salir al menú principal con q
            if choice == "-quit-" or choice == "q":
                import sys

                print()
                print(f"{Colors.YELLOW}Volviendo al menú principal...{Colors.RESET}")
                raise KeyboardInterrupt  # Propagar para salir de todos los submenús

            if choice == "-exit-" or choice == "-back-":
                return

            if choice == "1":
                show_commit_details(repo, commit)
                wait_for_enter()

            elif choice == "2":
                commit.version_type = "major"
                next_ver = get_next_version(repo, "major")
                print(f"{Colors.GREEN}Tipo asignado: MAJOR - {next_ver}{Colors.RESET}")

            elif choice == "3":
                commit.version_type = "minor"
                next_ver = get_next_version(repo, "minor")
                print(f"{Colors.GREEN}Tipo asignado: MINOR - {next_ver}{Colors.RESET}")

            elif choice == "4":
                commit.version_type = "patch"
                next_ver = get_next_version(repo, "patch")
                print(f"{Colors.GREEN}Tipo asignado: PATCH - {next_ver}{Colors.RESET}")

            elif choice == "5":
                display_message = commit.custom_message or commit.message
                print()
                print(f"Mensaje actual: {Colors.CYAN}{display_message}{Colors.RESET}")
                try:
                    custom_msg = input(
                        f"{Colors.WHITE}Ingrese mensaje personalizado (o Enter para mantener): {Colors.RESET}"
                    ).strip()
                    if custom_msg:
                        commit.custom_message = custom_msg
                        print(
                            f"{Colors.GREEN}Mensaje personalizado asignado{Colors.RESET}"
                        )
                except KeyboardInterrupt:
                    print()
                    print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")

            elif choice == "6":
                if commit.version_type:
                    commit.processed = True
                    print(f"{Colors.GREEN}Commit marcado como procesado{Colors.RESET}")
                    return
                else:
                    print(
                        f"{Colors.RED}Error: Debe asignar un tipo de versión primero{Colors.RESET}"
                    )

            elif choice == "7":
                ai_message = generate_ai_message(repo, commit)
                if ai_message:
                    print()
                    print(f"{Colors.GREEN}Mensaje generado:{Colors.RESET}")
                    print(f"{Colors.CYAN}{ai_message}{Colors.RESET}")
                    print()
                    try:
                        use_message = (
                            input(
                                f"{Colors.WHITE}¿Usar este mensaje? (s/n): {Colors.RESET}"
                            )
                            .strip()
                            .lower()
                        )
                        if use_message == "s":
                            commit.custom_message = ai_message
                            print(f"{Colors.GREEN}Mensaje asignado{Colors.RESET}")
                    except KeyboardInterrupt:
                        print()
                        print(f"{Colors.YELLOW}Cancelado.{Colors.RESET}")

            elif choice == "0":
                return

            else:
                print(f"{Colors.RED}Opción inválida{Colors.RESET}")
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")


def run_commits_submenu(
    repo: git.Repo, commits: List[Commit], dry_run: bool = False, push: bool = False
) -> bool:
    """Ejecuta el submenú de gestión de commits.

    Args:
        repo: Repositorio Git
        commits: Lista de commits sin etiquetar
        dry_run: Modo prueba
        push: Subir tags automáticamente

    Returns:
        bool: False para permanecer en el menú de tags
    """

    def show_commits_status():
        """Muestra el estado actual de commits."""
        print(f"{Colors.WHITE}Commits sin etiquetar: {len(commits)}{Colors.RESET}")
        processed_count = len([c for c in commits if c.version_type])
        print(
            f"{Colors.WHITE}Commits generados en esta sesión: {processed_count}{Colors.RESET}"
        )

    def action_view_commits():
        show_commit_list(repo, commits)
        return False

    def action_modify_commits():
        """Muestra listado paginado de commits con indicador de estado de tag."""
        ITEMS_PER_PAGE = 10
        current_page = 0

        while True:
            clear_screen()
            total_commits = len(commits)
            total_pages = max(1, (total_commits + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            print_subheader(
                f"MODIFICAR COMMITS - Página {current_page + 1}/{total_pages}"
            )
            print()

            if total_commits == 0:
                print(f"{Colors.GREEN}✓ No hay commits sin etiquetar{Colors.RESET}")
                wait_for_enter()
                return False

            start_idx = current_page * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, total_commits)

            for i in range(start_idx, end_idx):
                commit = commits[i]
                # Indicador de estado
                if commit.version_type:
                    status = f"{Colors.GREEN}✓{Colors.RESET}"
                    tag_info = (
                        f"{Colors.GREEN}[{commit.version_type.upper()}]{Colors.RESET}"
                    )
                else:
                    status = f"{Colors.YELLOW}○{Colors.RESET}"
                    tag_info = f"{Colors.YELLOW}[pendiente]{Colors.RESET}"

                print(
                    f"  {status} {Colors.CYAN}{i + 1:3}.{Colors.RESET} {commit.hash[:7]} - {commit.message[:45]}{'...' if len(commit.message) > 45 else ''} {tag_info}"
                )

            print()
            print(f"{Colors.WHITE}─" * 60 + f"{Colors.RESET}")
            print()

            # Leyenda
            print(
                f"  {Colors.GREEN}✓{Colors.RESET} = Tag asignado  |  {Colors.YELLOW}○{Colors.RESET} = Falta asignar tag"
            )
            print()

            # Navegación
            nav_options = []
            if current_page > 0:
                nav_options.append(f"{Colors.CYAN}[p]{Colors.RESET} Anterior")
            if current_page < total_pages - 1:
                nav_options.append(f"{Colors.CYAN}[n]{Colors.RESET} Siguiente")
            nav_options.append(f"{Colors.CYAN}[0]{Colors.RESET} Volver")

            print(f"  {' | '.join(nav_options)}")
            print()

            try:
                choice = (
                    get_menu_input(
                        f"{Colors.WHITE}Seleccione número de commit o navegue: {Colors.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except KeyboardInterrupt:
                print()
                return False

            # Salir al menú principal con q
            if choice == "-quit-" or choice == "q":
                print()
                print(f"{Colors.YELLOW}Volviendo al menú principal...{Colors.RESET}")
                raise KeyboardInterrupt

            if (
                choice == "-exit-"
                or choice == "-back-"
                or choice == "0"
                or choice == ""
            ):
                return False
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < total_commits:
                    show_commit_submenu(repo, commits[idx], idx, commits)
            else:
                pass  # Opción inválida, simplemente refrescar

        return False

    def action_view_preview():
        show_tag_preview(repo, commits)
        wait_for_enter()
        return False

    def action_auto_generate():
        auto_generate_all_with_ai(repo, commits)
        wait_for_enter()
        return False

    def action_apply_tags():
        nonlocal commits
        print()
        print(f"{Colors.YELLOW}¿Desea aplicar las etiquetas?{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Esta acción no puede deshacerse fácilmente{Colors.RESET}"
        )
        try:
            confirm = (
                input(f"{Colors.WHITE}¿Continuar? (s/n): {Colors.RESET}")
                .strip()
                .lower()
            )
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            wait_for_enter()
            return False

        if confirm == "s":
            success = apply_tags(repo, commits, dry_run, push)
            if success and not dry_run:
                # Filtrar commits que ya tienen tags creados
                from ..core.git_ops import get_untagged_commits

                commits = get_untagged_commits(repo)
                print()
                print(f"{Colors.GREEN}Etiquetas aplicadas correctamente{Colors.RESET}")

                # Preguntar si desea subir los tags al remoto
                if not push:
                    print()
                    try:
                        push_confirm = (
                            input(
                                f"{Colors.WHITE}¿Subir tags al repositorio remoto? (s/n): {Colors.RESET}"
                            )
                            .strip()
                            .lower()
                        )
                        if push_confirm == "s":
                            print(
                                f"{Colors.CYAN}Subiendo tags al remoto...{Colors.RESET}"
                            )
                            try:
                                repo.remotes.origin.push(tags=True)
                                print(
                                    f"{Colors.GREEN}✓ Tags subidos exitosamente{Colors.RESET}"
                                )
                            except Exception as e:
                                print(
                                    f"{Colors.RED}✗ Error al subir tags: {e}{Colors.RESET}"
                                )
                    except KeyboardInterrupt:
                        print()
                        print(f"{Colors.YELLOW}Push cancelado.{Colors.RESET}")
            wait_for_enter()
        return False

    def action_back():
        return True

    menu = Menu("GESTIÓN DE COMMITS")
    menu.set_status_callback(show_commits_status)
    menu.add_item("1", "Ver lista de commits", action_view_commits)
    menu.add_item("2", "Modificar commits", action_modify_commits)
    menu.add_item("3", "Generar tags faltantes con IA", action_auto_generate)
    menu.add_item("4", "Ver tags generados en esta sesión", action_view_preview)
    menu.add_item("5", "Aplicar tags", action_apply_tags)
    menu.add_item("0", "Volver", action_back)

    menu.run()
    return False


def run_tags_menu(
    repo: git.Repo, commits: List[Commit], dry_run: bool = False, push: bool = False
) -> bool:
    """Ejecuta el submenú de gestión de tags.

    Args:
        repo: Repositorio Git
        commits: Lista de commits sin etiquetar
        dry_run: Modo prueba
        push: Subir tags automáticamente

    Returns:
        bool: True si se debe volver al menú principal
    """

    def show_tags_status():
        """Muestra el estado actual de tags."""
        current_last_tag = get_last_tag(repo)
        local_count = len(list(repo.tags))
        print(f"{Colors.WHITE}Tags locales: {local_count}{Colors.RESET}")

        try:
            remote = repo.remotes.origin
            ls_remote = repo.git.ls_remote("--tags", remote.name)
            remote_tags = []
            for line in ls_remote.split("\n"):
                if line.strip() and not line.endswith("^{}"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].startswith("refs/tags/"):
                        remote_tags.append(parts[1].replace("refs/tags/", ""))
            print(f"{Colors.WHITE}Tags remotos: {len(remote_tags)}{Colors.RESET}")
        except Exception:
            print(
                f"{Colors.WHITE}Tags remotos: {Colors.YELLOW}(no disponible){Colors.RESET}"
            )

        print(f"{Colors.WHITE}Commits sin etiquetar: {len(commits)}{Colors.RESET}")
        if current_last_tag:
            print(f"{Colors.WHITE}Última etiqueta: {current_last_tag}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}No hay etiquetas previas{Colors.RESET}")

        print()
        print_subheader("ÚLTIMO CHANGELOG REGISTRADO")
        changelog_section = get_latest_changelog_section(repo)
        print(f"{Colors.CYAN}{changelog_section}{Colors.RESET}")

    def action_manage_commits():
        run_commits_submenu(repo, commits, dry_run, push)
        return False

    def action_view_local_tags():
        show_local_tags(repo)
        wait_for_enter()
        return False

    def action_view_remote_tags():
        show_remote_tags(repo)
        wait_for_enter()
        return False

    def action_change_last_tag():
        change_last_tag(repo)
        wait_for_enter()
        return False

    def action_push_tags():
        push_tags_to_remote(repo)
        wait_for_enter()
        return False

    def action_sync_tags():
        sync_tags_from_remote(repo)
        wait_for_enter()
        return False

    def action_clean_tags():
        clean_all_tags(repo, include_remote=True)
        wait_for_enter()
        return False

    def action_back():
        return True

    menu = Menu("GESTIÓN DE TAGS")
    menu.set_status_callback(show_tags_status)
    menu.add_item("1", "Gestionar commits", action_manage_commits)
    menu.add_item("2", "Ver tags locales", action_view_local_tags)
    menu.add_item("3", "Ver tags remotos", action_view_remote_tags)
    menu.add_item("4", "Cambiar el último tag", action_change_last_tag)
    menu.add_item("5", "Sincronizar tags desde remoto", action_sync_tags)
    menu.add_item("6", "Subir tags a GitHub", action_push_tags)
    menu.add_item("c", "Limpiar TODOS los tags (local y remoto)", action_clean_tags)
    menu.add_item("0", "Volver al menú principal", action_back)

    menu.run()
    return True
