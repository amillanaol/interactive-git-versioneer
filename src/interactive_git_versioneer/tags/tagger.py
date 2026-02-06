"""
Módulo principal del tagger interactivo.

Coordina los submenús de Tags y Releases usando el sistema de menú modular.
"""

import re
from typing import List, Optional

import git

from .. import __version__
from ..config import run_config_menu
from ..core.git_ops import (
    get_commit_diff,
    get_git_repo,
    get_last_tag,
    get_next_version,
    get_untagged_commits,
    parse_version,
)
from ..core.models import Commit
from ..core.ui import (
    Colors,
    Menu,
    clear_screen,
    get_menu_input,
    print_header,
    print_info,
    wait_for_enter,
)
from ..releases import run_changelog_submenu, run_releases_menu
from .actions import apply_tags, clean_all_tags, push_tags_to_remote
from .ai import auto_generate_all_with_ai
from .menus import run_commits_submenu
from .views import show_local_tags, show_remote_tags

# Re-exportar para compatibilidad hacia atrás
__all__ = [
    "run_interactive_tagger",
    "run_auto_tagger",
    "Commit",
    "get_git_repo",
    "get_last_tag",
    "get_untagged_commits",
    "get_next_version",
    "apply_tags",
    "parse_version",
]


def select_tag_from_list(
    repo: git.Repo, tags: List[git.TagReference], items_per_page: int = 10
) -> Optional[git.TagReference]:
    """Permite al usuario seleccionar un tag de una lista paginada.

    Args:
        repo: Repositorio Git.
        tags: Lista de objetos git.TagReference.
        items_per_page: Cantidad de tags por página.

    Returns:
        Optional[git.TagReference]: Objeto TagReference seleccionado, o None si cancela.
    """
    if not tags:
        print(f"{Colors.YELLOW}No hay tags disponibles para seleccionar.{Colors.RESET}")
        wait_for_enter()
        return None

    total_tags = len(tags)
    total_pages = (total_tags + items_per_page - 1) // items_per_page
    current_page = 1

    while True:
        clear_screen()
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_tags)

        print_header(
            f"SELECCIONAR TAG ({total_tags} encontrados) - Página {current_page}/{total_pages}"
        )
        print()

        for i, tag in enumerate(tags[start_idx:end_idx], start=start_idx + 1):
            tag_commit = tag.commit
            message = tag_commit.message.split("\n")[0]
            date = tag_commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
            print(
                f"{Colors.CYAN}{i:3}. {tag.name:<15}{Colors.RESET} - {tag_commit.hexsha[:7]} - {date} - {Colors.WHITE}{message}{Colors.RESET}"
            )

        print()
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

        nav_options = []
        if current_page > 1:
            nav_options.append(f"{Colors.YELLOW}p{Colors.WHITE}=anterior")
        if current_page < total_pages:
            nav_options.append(f"{Colors.YELLOW}n{Colors.WHITE}=siguiente")
        nav_options.append(f"{Colors.YELLOW}0{Colors.WHITE}=cancelar")

        print(f"{Colors.WHITE}Navegación: {' | '.join(nav_options)}{Colors.RESET}")
        print(f"{Colors.WHITE}Ingrese número del tag para seleccionar:{Colors.RESET}")

        choice = get_menu_input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()

        if choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif (
            choice == "0"
            or choice == "-back-"
            or choice == "-exit-"
            or choice == "-quit-"
            or choice == ""
        ):
            return None
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < total_tags:
                    return tags[idx]
                else:
                    print(f"{Colors.RED}Número fuera de rango.{Colors.RESET}")
                    wait_for_enter()
            except ValueError:
                pass


def manage_tags_interactive(repo, dry_run=False, push=False):
    """Interfaz interactiva para gestionar y modificar tags existentes."""
    while True:
        all_tags = sorted(repo.tags, key=lambda t: parse_version(t.name), reverse=True)

        if not all_tags:
            clear_screen()
            print_header("GESTIONAR TAGS")
            print(f"{Colors.YELLOW}No hay tags para gestionar.{Colors.RESET}")
            print("Puede generarlos automáticamente continuando con el proceso.")
            wait_for_enter()
            return

        clear_screen()
        print_header("GESTIONAR TAGS EXISTENTES")
        print(f"{Colors.WHITE}Tags encontrados: {len(all_tags)}{Colors.RESET}\n")

        print(f"{Colors.WHITE}1. Ver tags en lista paginada{Colors.RESET}")
        print(f"{Colors.WHITE}2. Modificar un tag existente{Colors.RESET}")
        print(f"{Colors.WHITE}0. Volver{Colors.RESET}")

        choice = get_menu_input("Seleccione una opción: ")

        if choice == "1":
            # Usar select_tag_from_list como visor paginado
            select_tag_from_list(repo, all_tags)
        elif choice == "2":
            selected_tag = select_tag_from_list(repo, all_tags)
            if selected_tag:
                print_info("Tag seleccionado:", selected_tag.name, Colors.CYAN)
                new_tag_name = get_menu_input(
                    f"Nuevo nombre para '{selected_tag.name}': "
                )

                if not new_tag_name:
                    print(
                        f"{Colors.RED}El nombre del tag no puede estar vacío.{Colors.RESET}"
                    )
                    wait_for_enter()
                    continue

                if dry_run:
                    print(
                        f"{Colors.YELLOW}[DRY-RUN] Renombrar tag '{selected_tag.name}' a '{new_tag_name}'{Colors.RESET}"
                    )
                    print(
                        f"{Colors.YELLOW}[DRY-RUN] Comando: git tag {new_tag_name} {selected_tag.commit.hexsha}{Colors.RESET}"
                    )
                    print(
                        f"{Colors.YELLOW}[DRY-RUN] Comando: git tag -d {selected_tag.name}{Colors.RESET}"
                    )
                    if push:
                        print(
                            f"{Colors.YELLOW}[DRY-RUN] Comando: git push origin :{selected_tag.name} {new_tag_name}{Colors.RESET}"
                        )
                    wait_for_enter()
                    continue

                # Crear nuevo tag y borrar el antiguo
                try:
                    new_tag = repo.create_tag(
                        new_tag_name,
                        ref=selected_tag.commit,
                        message=selected_tag.commit.message,
                    )
                    repo.delete_tag(selected_tag)

                    print(
                        f"{Colors.GREEN}Tag '{selected_tag.name}' renombrado a '{new_tag.name}'{Colors.RESET}"
                    )

                    if push:
                        print("Actualizando remoto...")
                        try:
                            repo.remotes.origin.push(f":{selected_tag.name}")
                            repo.remotes.origin.push(new_tag.name)
                            print(f"{Colors.GREEN}Remoto actualizado.{Colors.RESET}")
                        except Exception as e:
                            print(
                                f"{Colors.RED}Error actualizando el remoto: {e}{Colors.RESET}"
                            )

                    wait_for_enter()
                except Exception as e:
                    print(f"{Colors.RED}Error al renombrar tag: {e}{Colors.RESET}")
                    wait_for_enter()
        elif (
            choice == "0"
            or choice == "-back-"
            or choice == "-exit-"
            or choice == "-quit-"
        ):
            return
        else:
            print(f"{Colors.RED}Opción inválida.{Colors.RESET}")
            wait_for_enter()


def run_modify_tag_submenu(repo):
    """Submenú para modificar tags con lista paginada."""

    ITEMS_PER_PAGE = 10

    while True:
        all_tags = sorted(repo.tags, key=lambda t: parse_version(t.name), reverse=True)

        if not all_tags:
            clear_screen()
            print_header("MODIFICAR TAG")
            print(f"{Colors.YELLOW}No hay tags en el repositorio.{Colors.RESET}")
            wait_for_enter()
            return

        total_pages = (len(all_tags) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        current_page = 0
        selected_tag = None

        # Bucle de selección de tag con paginación
        while selected_tag is None:
            clear_screen()
            print_header("MODIFICAR TAG - Seleccionar")
            print(
                f"{Colors.WHITE}Total de tags: {len(all_tags)} | Página {current_page + 1}/{total_pages}{Colors.RESET}"
            )
            print()

            start_idx = current_page * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, len(all_tags))
            page_tags = all_tags[start_idx:end_idx]

            for i, tag in enumerate(page_tags, 1):
                try:
                    commit = tag.commit
                    date_str = commit.committed_datetime.strftime("%Y-%m-%d")
                    print(f"  {Colors.CYAN}{i}.{Colors.RESET} {tag.name} ({date_str})")
                except:
                    print(f"  {Colors.CYAN}{i}.{Colors.RESET} {tag.name}")

            print()
            if total_pages > 1:
                print(
                    f"{Colors.WHITE}[n] Siguiente | [p] Anterior | [0] Volver{Colors.RESET}"
                )
            else:
                print(f"{Colors.WHITE}[0] Volver{Colors.RESET}")
            print()

            choice = get_menu_input("Seleccione tag (número) o navegue: ")

            if choice == "0" or choice == "-back-" or choice == "-exit-":
                return
            elif choice.lower() == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice.lower() == "p" and current_page > 0:
                current_page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_tags):
                    selected_tag = page_tags[idx]

        # Submenú de modificación del tag seleccionado
        while True:
            clear_screen()
            print_header(f"MODIFICAR TAG: {selected_tag.name}")

            try:
                tag_obj = selected_tag
                commit = tag_obj.commit
                print(f"{Colors.WHITE}Información actual:{Colors.RESET}")
                print(f"  {Colors.GREEN}Tag:{Colors.RESET} {tag_obj.name}")
                print(f"  {Colors.CYAN}Commit:{Colors.RESET} {commit.hexsha[:7]}")
                print(
                    f"  {Colors.CYAN}Fecha:{Colors.RESET} {commit.committed_datetime}"
                )
                if tag_obj.tag and tag_obj.tag.message:
                    print(
                        f"  {Colors.CYAN}Mensaje:{Colors.RESET} {tag_obj.tag.message.strip()}"
                    )
            except Exception as e:
                print(f"{Colors.RED}Error al obtener información: {e}{Colors.RESET}")

            print()
            print(f"{Colors.WHITE}1. Cambiar nombre del tag{Colors.RESET}")
            print(f"{Colors.WHITE}2. Cambiar mensaje del tag{Colors.RESET}")
            print(f"{Colors.WHITE}3. Cambiar nombre y mensaje{Colors.RESET}")
            print(f"{Colors.WHITE}0. Volver a la lista{Colors.RESET}")
            print()

            action = get_menu_input("Seleccione opción: ")

            if action == "0" or action == "-back-":
                break

            old_name = selected_tag.name
            old_message = (
                selected_tag.tag.message.strip()
                if selected_tag.tag and selected_tag.tag.message
                else old_name
            )
            commit_ref = selected_tag.commit.hexsha

            new_name = old_name
            new_message = old_message

            if action == "1" or action == "3":
                print()
                input_name = get_menu_input(f"Nuevo nombre (actual: {old_name}): ")
                if input_name and input_name != "0":
                    if not input_name.startswith("v"):
                        input_name = f"v{input_name}"
                    if re.match(r"^v\d+\.\d+\.\d+", input_name):
                        new_name = input_name
                    else:
                        print(
                            f"{Colors.RED}Formato inválido. Use: v<major>.<minor>.<patch>{Colors.RESET}"
                        )
                        wait_for_enter()
                        continue

            if action == "2" or action == "3":
                print()
                input_msg = get_menu_input(
                    f"Nuevo mensaje (Enter para mantener actual): "
                )
                if input_msg:
                    new_message = input_msg

            if new_name == old_name and new_message == old_message:
                print(f"{Colors.YELLOW}No hay cambios que aplicar.{Colors.RESET}")
                wait_for_enter()
                continue

            print()
            print(f"{Colors.YELLOW}Resumen del cambio:{Colors.RESET}")
            if new_name != old_name:
                print(
                    f"  Nombre: {Colors.RED}{old_name}{Colors.RESET} → {Colors.GREEN}{new_name}{Colors.RESET}"
                )
            if new_message != old_message:
                print(
                    f"  Mensaje: {Colors.CYAN}{new_message[:50]}{'...' if len(new_message) > 50 else ''}{Colors.RESET}"
                )
            print()

            confirm = get_menu_input("¿Confirmar cambios? (s/n): ")
            if confirm.lower() == "s":
                try:
                    repo.delete_tag(old_name)
                    repo.create_tag(new_name, ref=commit_ref, message=new_message)
                    print(f"{Colors.GREEN}✓ Tag modificado exitosamente{Colors.RESET}")
                    wait_for_enter()
                    break  # Volver a la lista ya que el tag cambió
                except Exception as e:
                    print(f"{Colors.RED}Error al modificar tag: {e}{Colors.RESET}")
                    wait_for_enter()
            else:
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                wait_for_enter()


def run_tag_management_submenu(repo, untagged_commits, dry_run, push):
    """Muestra el submenú para la gestión de tags."""

    def show_tags_status():
        """Muestra el estado actual de tags."""
        last_tag = get_last_tag(repo)
        local_count = len(list(repo.tags))
        print(f"{Colors.WHITE}Tags locales: {local_count}{Colors.RESET}")

        # Contar tags remotos
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

        if last_tag:
            print(f"{Colors.WHITE}Último tag: {last_tag}{Colors.RESET}")

            # Verificar si el último commit tiene tag
            try:
                head_commit = repo.head.commit
                tag_obj = repo.tags[last_tag]
                if tag_obj.commit.hexsha == head_commit.hexsha:
                    print(
                        f"{Colors.WHITE}Último commit: {head_commit.hexsha[:7]} - {head_commit.message.split(chr(10))[0][:40]} {Colors.GREEN}✓{Colors.RESET}"
                    )
                else:
                    print(
                        f"{Colors.WHITE}Último commit: {Colors.YELLOW}Faltan commits por etiquetar{Colors.RESET}"
                    )
            except Exception:
                pass

    def action_view_last_tag():
        """Muestra información del último tag."""
        clear_screen()
        print_header("ÚLTIMO TAG")
        last_tag = get_last_tag(repo)
        if not last_tag:
            print(f"{Colors.YELLOW}No hay tags en el repositorio.{Colors.RESET}")
        else:
            try:
                tag_obj = repo.tags[last_tag]
                commit = tag_obj.commit
                print(f"{Colors.GREEN}Tag:{Colors.RESET} {last_tag}")
                print(f"{Colors.CYAN}Commit:{Colors.RESET} {commit.hexsha[:7]}")
                print(f"{Colors.CYAN}Fecha:{Colors.RESET} {commit.committed_datetime}")
                print(f"{Colors.CYAN}Autor:{Colors.RESET} {commit.author.name}")
                if tag_obj.tag and tag_obj.tag.message:
                    print(
                        f"{Colors.CYAN}Mensaje del tag:{Colors.RESET} {tag_obj.tag.message.strip()}"
                    )
                print(
                    f"{Colors.CYAN}Mensaje del commit:{Colors.RESET} {commit.message.strip()}"
                )
            except Exception as e:
                print(f"{Colors.RED}Error al obtener información: {e}{Colors.RESET}")
        wait_for_enter()
        return False

    def action_view_local_tags():
        """Muestra todos los tags locales."""
        show_local_tags(repo)
        wait_for_enter()
        return False

    def action_view_remote_tags():
        """Muestra los tags en el repositorio remoto."""
        show_remote_tags(repo)
        wait_for_enter()
        return False

    def action_modify_tag():
        """Abre el submenú de modificación de tags."""
        run_modify_tag_submenu(repo)
        return False

    def action_delete_local_tag():
        """Elimina un tag local específico."""
        clear_screen()
        print_header("ELIMINAR TAG LOCAL")
        all_tags = sorted(repo.tags, key=lambda t: parse_version(t.name), reverse=True)
        if not all_tags:
            print(f"{Colors.YELLOW}No hay tags locales para eliminar.{Colors.RESET}")
            wait_for_enter()
            return False

        print(f"{Colors.WHITE}Tags disponibles:{Colors.RESET}")
        for i, tag in enumerate(all_tags[:15], 1):
            print(f"  {i}. {tag.name}")
        if len(all_tags) > 15:
            print(f"  {Colors.YELLOW}... y {len(all_tags) - 15} más{Colors.RESET}")
        print()

        tag_name = get_menu_input("Nombre del tag a eliminar (o 0 para cancelar): ")
        if tag_name == "0" or not tag_name:
            return False

        if tag_name not in [t.name for t in all_tags]:
            print(f"{Colors.RED}Tag '{tag_name}' no encontrado.{Colors.RESET}")
            wait_for_enter()
            return False

        confirm = get_menu_input(f"¿Eliminar tag '{tag_name}'? (s/n): ")
        if confirm.lower() == "s":
            try:
                repo.delete_tag(tag_name)
                print(
                    f"{Colors.GREEN}✓ Tag '{tag_name}' eliminado localmente.{Colors.RESET}"
                )
            except Exception as e:
                print(f"{Colors.RED}Error al eliminar: {e}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        wait_for_enter()
        return False

    def action_delete_remote_tag():
        """Elimina un tag del repositorio remoto."""
        clear_screen()
        print_header("ELIMINAR TAG REMOTO")

        try:
            remote = repo.remotes.origin
        except AttributeError:
            print(f"{Colors.RED}No hay remoto 'origin' configurado.{Colors.RESET}")
            wait_for_enter()
            return False

        print(f"{Colors.CYAN}Obteniendo tags remotos...{Colors.RESET}")
        try:
            ls_remote = repo.git.ls_remote("--tags", remote.name)
            remote_tags = []
            for line in ls_remote.split("\n"):
                if line.strip() and not line.endswith("^{}"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].startswith("refs/tags/"):
                        remote_tags.append(parts[1].replace("refs/tags/", ""))

            if not remote_tags:
                print(f"{Colors.YELLOW}No hay tags en el remoto.{Colors.RESET}")
                wait_for_enter()
                return False

            print(f"\n{Colors.WHITE}Tags remotos:{Colors.RESET}")
            for i, tag in enumerate(sorted(remote_tags, reverse=True)[:15], 1):
                print(f"  {i}. {tag}")
            if len(remote_tags) > 15:
                print(
                    f"  {Colors.YELLOW}... y {len(remote_tags) - 15} más{Colors.RESET}"
                )
            print()

            tag_name = get_menu_input(
                "Nombre del tag a eliminar del remoto (o 0 para cancelar): "
            )
            if tag_name == "0" or not tag_name:
                return False

            if tag_name not in remote_tags:
                print(
                    f"{Colors.RED}Tag '{tag_name}' no encontrado en remoto.{Colors.RESET}"
                )
                wait_for_enter()
                return False

            confirm = get_menu_input(f"¿Eliminar tag '{tag_name}' del REMOTO? (s/n): ")
            if confirm.lower() == "s":
                repo.git.push(remote.name, "--delete", f"refs/tags/{tag_name}")
                print(
                    f"{Colors.GREEN}✓ Tag '{tag_name}' eliminado del remoto.{Colors.RESET}"
                )
            else:
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        wait_for_enter()
        return False

    def action_sync_remote():
        """Sincroniza tags con el repositorio remoto (push)."""
        push_tags_to_remote(repo)
        wait_for_enter()
        return False

    def action_generate_tags_ai():
        """Genera tags automáticamente con IA desde el último tag."""
        if not untagged_commits:
            clear_screen()
            print_header("GENERAR TAGS CON IA")
            print(f"{Colors.GREEN}✓ No hay commits sin etiquetar.{Colors.RESET}")
            wait_for_enter()
            return False
        auto_generate_all_with_ai(repo, untagged_commits)
        wait_for_enter()
        return False

    def action_back():
        """Vuelve al menú principal."""
        return True

    submenu = Menu("GESTIÓN DE TAGS")
    submenu.set_status_callback(show_tags_status)
    submenu.add_item("1", "Ver último tag", action_view_last_tag)
    submenu.add_item("2", "Ver tags locales", action_view_local_tags)
    submenu.add_item("3", "Ver tags remotos", action_view_remote_tags)
    submenu.add_item("4", "Modificar tag", action_modify_tag)
    submenu.add_item("5", "Eliminar tag local", action_delete_local_tag)
    submenu.add_item("6", "Eliminar tag remoto", action_delete_remote_tag)
    submenu.add_item("7", "Sincronizar con repositorio remoto", action_sync_remote)
    submenu.add_item("8", "Generar tags con IA", action_generate_tags_ai)
    submenu.add_item("0", "Volver al menú principal", action_back)

    submenu.run()


def run_interactive_tagger(dry_run: bool = False, push: bool = False) -> int:
    """Ejecuta el tagger interactivo.

    Args:
        dry_run: Si True, solo muestra qué haría sin ejecutar
        push: Si True, sube las etiquetas al remoto después de crearlas

    Returns:
        int: Código de salida (0 = éxito)
    """
    # Limpiar pantalla al iniciar
    clear_screen()

    # Obtener repositorio Git
    repo = get_git_repo()

    # Encabezado inicial
    print()
    print(f"{Colors.CYAN}{'=' * 49}{Colors.RESET}")
    print(f"{Colors.CYAN}{f'GESTOR DE VERSIONES GIT v{__version__}'.center(49)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 49}{Colors.RESET}")
    print()

    if dry_run:
        print(f"{Colors.YELLOW}[MODO PRUEBA ACTIVADO]{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Los comandos git se mostrarán pero NO se ejecutarán{Colors.RESET}"
        )
        print()

    # Obtener información inicial
    untagged_commits = get_untagged_commits(repo)
    last_tag = get_last_tag(repo)

    # Mostrar resumen inicial
    if untagged_commits:
        print(
            f"{Colors.CYAN}Se encontraron {len(untagged_commits)} commits sin etiquetar{Colors.RESET}"
        )
    else:
        print(f"{Colors.GREEN}✓ No hay commits sin etiquetar{Colors.RESET}")

    if last_tag:
        print(f"{Colors.CYAN}Última etiqueta: {last_tag}{Colors.RESET}")
    else:
        print(
            f"{Colors.YELLOW}No hay etiquetas previas en el repositorio{Colors.RESET}"
        )

    print()

    # Funciones de estado y acciones para el menú principal
    def show_main_status():
        """Muestra el estado actual del repositorio."""
        import os
        import re

        # Recalcular valores cada vez para reflejar cambios
        current_untagged = get_untagged_commits(repo)
        current_last_tag = get_last_tag(repo)
        print(
            f"{Colors.WHITE}Commits sin etiquetar: {len(current_untagged)}{Colors.RESET}"
        )

        # Último release (desde tags locales)
        if current_last_tag:
            print(f"{Colors.WHITE}Último release: {current_last_tag}{Colors.RESET}")

        # Último tag
        if current_last_tag:
            print(f"{Colors.WHITE}Último tag: {current_last_tag}{Colors.RESET}")

        # Último changelog
        repo_root = repo.working_dir
        changelog_path = os.path.join(repo_root, "CHANGELOG.md")
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(r"##\s*\[([^\]]+)\]", content)
                if match:
                    last_changelog_version = match.group(1)
                    print(
                        f"{Colors.WHITE}Último changelog: {last_changelog_version}{Colors.RESET}"
                    )
            except Exception:
                pass

    def get_footer_status() -> str:
        """Retorna el string de estado para el footer del menú."""
        from .. import __version__

        try:
            head_commit = repo.head.commit
            author_email = head_commit.author.email
            username = (
                author_email.split("@")[0] if "@" in author_email else author_email
            )
            return f"{Colors.WHITE}Autor: {username} | igv v{__version__}{Colors.RESET}"
        except Exception:
            return f"{Colors.CYAN}igv v{__version__}{Colors.RESET}"

    def action_manage_commits():
        """Abre el submenú de gestión de commits."""
        run_commits_submenu(repo, untagged_commits, dry_run, push)
        return False

    def action_open_tags_submenu():
        """Abre el submenú de gestión de tags."""
        run_tag_management_submenu(repo, untagged_commits, dry_run, push)
        return False

    def action_manage_releases():
        """Abre el submenú de gestión de releases."""
        run_releases_menu(repo)
        return False

    def action_manage_changelogs():
        """Abre el submenú de generación de changelogs."""
        run_changelog_submenu(repo)
        return False

    def action_config():
        """Abre el submenú de configuración."""
        run_config_menu()
        return False

    def action_exit():
        """Sale del programa."""
        print()
        print(f"{Colors.YELLOW}Saliendo...{Colors.RESET}")
        return True

    # Crear y ejecutar menú principal
    main_menu = Menu("GESTOR DE VERSIONES GIT")
    main_menu.set_status_callback(show_main_status)
    main_menu.set_footer_callback(get_footer_status)
    main_menu.add_item("1", "Gestionar Commits", action_manage_commits)
    main_menu.add_item("2", "Gestionar Tags", action_open_tags_submenu)
    main_menu.add_item("3", "Gestionar Releases", action_manage_releases)
    main_menu.add_item("4", "Gestionar Changelogs", action_manage_changelogs)
    main_menu.add_item("5", "Configuración", action_config)
    main_menu.add_item("6", "Salir", action_exit)

    try:
        main_menu.run(is_main_menu=True)
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
        return 1

    print()
    print(f"{Colors.GREEN}Script completado.{Colors.RESET}")
    print()

    return 0


def run_auto_tagger(
    dry_run: bool = False, push: bool = False, version_type: str = "auto"
) -> int:
    """Ejecuta el tagger en modo automático (CI/CD).

    Modo no interactivo para pipelines. Usa IA para generar mensajes
    y determinar tipos de versión automáticamente.

    Args:
        dry_run: Si True, solo muestra qué haría sin ejecutar
        push: Si True, sube las etiquetas al remoto después de crearlas
        version_type: Tipo de versión (major/minor/patch/auto)

    Returns:
        int: Código de salida (0 = éxito)
    """
    from ..config import get_config_value
    from ..core.ai import determine_version_type
    from .ai import generate_ai_message

    print("=" * 50)
    print("INTERACTIVE GIT TAGGER - MODO AUTOMÁTICO (CI/CD)")
    print("=" * 50)
    print()

    if dry_run:
        print("[MODO PRUEBA] Los comandos NO serán ejecutados")
        print()

    # Obtener repositorio
    repo = get_git_repo()

    # Verificar configuración de IA
    api_key = get_config_value("OPENAI.key")
    base_url = get_config_value("OPENAI.baseURL")

    if not api_key or not base_url:
        print("ERROR: Configuración de IA incompleta.")
        print("Configura con:")
        print("  igv config set OPENAI.key <tu-api-key>")
        print("  igv config set OPENAI.baseURL <url>")
        return 1

    # Obtener commits sin etiquetar
    untagged_commits = get_untagged_commits(repo)
    last_tag = get_last_tag(repo)

    print(f"Commits sin etiquetar: {len(untagged_commits)}")
    if last_tag:
        print(f"Última etiqueta: {last_tag}")
    print()

    if not untagged_commits:
        print("No hay commits sin etiquetar. Nada que hacer.")
        return 0

    ai_decides = version_type == "auto"
    print(f"Tipo de versión: {'IA decide' if ai_decides else version_type.upper()}")
    print(f"Procesando {len(untagged_commits)} commits...")
    print()

    # Procesar cada commit
    success_count = 0
    error_count = 0

    for i, commit in enumerate(untagged_commits, 1):
        print(
            f"[{i}/{len(untagged_commits)}] {commit.hash[:7]} - {commit.message[:50]}"
        )

        # Determinar tipo de versión
        if ai_decides:
            try:
                diff = get_commit_diff(repo, commit.hash)
                vtype, reason = determine_version_type(commit.message, diff)
                commit.version_type = vtype
                print(f"  → Tipo: {vtype.upper()} ({reason})")
            except Exception as e:
                error_str = str(e).lower()
                if (
                    "401" in error_str
                    or "invalid_api_key" in error_str
                    or "invalid api key" in error_str
                ):
                    print(
                        f'  → Error: API Key inválida. Configura con: igv config set OPENAI.key "tu_key"'
                    )
                else:
                    print(f"  → Error al determinar tipo: {e}")
                commit.version_type = "patch"
                print(f"  → Usando PATCH por defecto")
        else:
            commit.version_type = version_type

        # Generar mensaje con IA
        try:
            ai_message = generate_ai_message(repo, commit)
            if ai_message:
                commit.custom_message = ai_message
                commit.processed = True
                success_count += 1
                print(f"  ✓ Mensaje generado")
            else:
                commit.custom_message = commit.message
                commit.processed = True
                success_count += 1
                print(f"  → Usando mensaje original del commit")
        except Exception as e:
            error_str = str(e).lower()
            if (
                "401" in error_str
                or "invalid_api_key" in error_str
                or "invalid api key" in error_str
            ):
                print(
                    f'  ✗ Error: API Key inválida. Configura con: igv config set OPENAI.key "tu_key"'
                )
                commit.custom_message = commit.message
                commit.processed = True
                success_count += 1
                print(f"  → Usando mensaje original del commit")
        except Exception as e:
            error_str = str(e).lower()
            if (
                "401" in error_str
                or "invalid_api_key" in error_str
                or "invalid api key" in error_str
            ):
                print(
                    f'  ✗ Error: API Key inválida. Configura con: igv config set OPENAI.key "tu_key"'
                )
                print(
                    f'  ✗ Error: API Key inválida. Configura con: igv config set OPENAI.key "tu_key"'
                )
            else:
                print(f"  ✗ Error: {e}")
            commit.custom_message = commit.message
            commit.processed = True
            error_count += 1

        print()

    print("=" * 50)
    print("APLICANDO ETIQUETAS")
    print("=" * 50)
    print()

    # Aplicar tags
    processed_commits = [c for c in untagged_commits if c.version_type]
    tags_created = 0

    for commit in processed_commits:
        next_ver = get_next_version(repo, commit.version_type)
        message = commit.custom_message or commit.message

        if dry_run:
            print(f"[DRY-RUN] Crearía tag: {next_ver} → {commit.hash[:7]}")
            print(f"          Mensaje: {message[:60]}...")
            tags_created += 1
        else:
            try:
                if next_ver in [tag.name for tag in repo.tags]:
                    print(f"⚠️  Tag {next_ver} ya existe, omitiendo")
                    continue

                repo.create_tag(next_ver, ref=commit.hash, message=message)
                print(f"✓ Tag creado: {next_ver} → {commit.hash[:7]}")
                tags_created += 1
            except Exception as e:
                print(f"✗ Error creando tag {next_ver}: {e}")

    print()

    # Push
    if push and tags_created > 0:
        if dry_run:
            print("[DRY-RUN] Ejecutaría: git push origin --tags")
        else:
            print("Subiendo etiquetas al remoto...")
            try:
                repo.remotes.origin.push(tags=True)
                print("✓ Tags subidos exitosamente")
            except Exception as e:
                print(f"✗ Error al subir tags: {e}")
                return 1

    # Resumen
    print()
    print("=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Commits procesados: {success_count}")
    print(f"Tags {'que se crearían' if dry_run else 'creados'}: {tags_created}")
    if error_count > 0:
        print(f"Errores: {error_count}")

    return 0
