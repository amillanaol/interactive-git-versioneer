"""
Funciones de visualización para versiones y commits.

Contiene funciones para mostrar información en la interfaz de usuario.
"""

from typing import List, Optional

import git

from ..core.git_ops import get_next_version, parse_version
from ..core.models import Commit
from ..core.ui import (
    Colors,
    clear_screen,
    print_header,
    print_info,
    wait_for_enter,
)


def show_commit_details(repo: git.Repo, commit: Commit) -> None:
    """Muestra información detallada de un commit."""
    clear_screen()
    print_header("DETALLES DEL COMMIT")

    print_info("Hash:", commit.hash, Colors.CYAN)
    print_info("Mensaje:", commit.message, Colors.CYAN)
    print_info("Autor:", commit.author, Colors.CYAN)
    print_info("Fecha:", commit.date, Colors.CYAN)

    if commit.version_type:
        print_info("Tipo:", commit.version_type, Colors.GREEN)
    else:
        print_info("Tipo:", "No asignado", Colors.YELLOW)

    if commit.version_type:
        next_version = get_next_version(repo, commit.version_type)
        print_info("Etiqueta:", next_version, Colors.GREEN)
    else:
        print_info("Etiqueta:", "Pendiente", Colors.YELLOW)

    if commit.custom_message:
        print_info("Mensaje personalizado:", commit.custom_message, Colors.CYAN)

    print_header("")


def show_commit_list(
    repo: git.Repo, commits: List[Commit], items_per_page: int = 10
) -> None:
    """Muestra la lista de commits sin etiquetar con paginación.

    Muestra una vista previa con: commit_id, autor, mensaje y estado del tag.

    Args:
        repo: Repositorio Git
        commits: Lista de commits
        items_per_page: Cantidad de commits por página
    """
    if not commits:
        clear_screen()
        print_header("VISTA PREVIA DE COMMITS")
        print()
        print(f"{Colors.GREEN}✓ No hay commits sin etiquetar{Colors.RESET}")
        print()
        return

    total_commits = len(commits)
    total_pages = (total_commits + items_per_page - 1) // items_per_page
    current_page = 1

    while True:
        clear_screen()
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_commits)

        print_header(f"COMMITS POR REVISAR - Página {current_page}/{total_pages}")
        print()

        # Encabezado de tabla
        print(
            f"  {Colors.WHITE}{'#':>3}  {'COMMIT':<9} {'AUTOR':<15} {'MENSAJE':<35} {'TAG'}{Colors.RESET}"
        )
        print(f"  {Colors.WHITE}{'─' * 80}{Colors.RESET}")

        for i, commit in enumerate(commits[start_idx:end_idx], start=start_idx + 1):
            # Estado del tag
            if commit.version_type:
                tag_status = (
                    f"{Colors.GREEN}[{commit.version_type.upper()}]{Colors.RESET}"
                )
            else:
                tag_status = f"{Colors.YELLOW}[pendiente]{Colors.RESET}"

            # Truncar autor y mensaje si son muy largos
            author = (
                commit.author[:14] + "…" if len(commit.author) > 15 else commit.author
            )
            message = (
                commit.message[:34] + "…"
                if len(commit.message) > 35
                else commit.message
            )

            print(
                f"  {Colors.CYAN}{i:>3}{Colors.RESET}  "
                f"{Colors.WHITE}{commit.hash[:7]}{Colors.RESET}   "
                f"{Colors.CYAN}{author:<15}{Colors.RESET} "
                f"{message:<35} "
                f"{tag_status}"
            )

        print()
        print(f"  {Colors.WHITE}{'─' * 80}{Colors.RESET}")
        print()

        # Leyenda
        print(
            f"  {Colors.GREEN}[MAJOR/MINOR/PATCH]{Colors.RESET} = Tag asignado  |  "
            f"{Colors.YELLOW}[pendiente]{Colors.RESET} = Falta asignar tag"
        )
        print()

        # Navegación
        options = []
        if current_page > 1:
            options.append(f"{Colors.CYAN}[p]{Colors.RESET} Anterior")
        if current_page < total_pages:
            options.append(f"{Colors.CYAN}[n]{Colors.RESET} Siguiente")
        options.append(f"{Colors.CYAN}[0]{Colors.RESET} Volver")

        print(f"  {' | '.join(options)}")
        print()

        try:
            choice = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            print()
            break

        if choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif choice == "q" or choice == "0" or choice == "":
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < total_commits:
                    show_commit_details(repo, commits[idx])
                    wait_for_enter()
                else:
                    print(f"{Colors.RED}Número fuera de rango.{Colors.RESET}")
                    input(f"{Colors.WHITE}Presione Enter...{Colors.RESET}")
            except ValueError:
                pass


def select_commit_from_list(
    repo: git.Repo, commits: List[Commit], items_per_page: int = 10
) -> Optional[int]:
    """Permite al usuario seleccionar un commit de una lista con paginación.

    Args:
        repo: Repositorio Git
        commits: Lista de commits
        items_per_page: Cantidad de commits por página

    Returns:
        Optional[int]: Índice del commit seleccionado, o None si cancela
    """
    if not commits:
        clear_screen()
        print_header("SELECCIONAR COMMIT")
        print()
        print(f"{Colors.GREEN}✓ No hay commits sin etiquetar{Colors.RESET}")
        print()
        wait_for_enter()
        return None

    total_commits = len(commits)
    total_pages = (total_commits + items_per_page - 1) // items_per_page
    current_page = 1

    while True:
        clear_screen()
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_commits)

        print_header(
            f"SELECCIONAR COMMIT ({total_commits} encontrados) - Página {current_page}/{total_pages}"
        )
        print()

        for i, commit in enumerate(commits[start_idx:end_idx], start=start_idx + 1):
            status_icon = "✓" if commit.processed else "○"
            status_color = Colors.GREEN if commit.processed else Colors.YELLOW

            print(
                f"{status_color}{status_icon} {Colors.WHITE}{i:3}. {Colors.CYAN}{commit.hash[:7]}{Colors.RESET} - {commit.message[:50]}"
            )

            if commit.version_type:
                next_ver = get_next_version(repo, commit.version_type)
                print(
                    f"      {Colors.GREEN}→ {commit.version_type.upper()} ({next_ver}){Colors.RESET}"
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
        print(f"{Colors.WHITE}Ingrese número de commit para procesar:{Colors.RESET}")

        try:
            choice = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            return None

        if choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif choice == "0" or choice == "q" or choice == "":
            return None
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < total_commits:
                    return idx
                else:
                    print(f"{Colors.RED}Número fuera de rango.{Colors.RESET}")
                    input(
                        f"{Colors.WHITE}Presione Enter para continuar...{Colors.RESET}"
                    )
            except ValueError:
                pass


def show_tag_preview(repo: git.Repo, commits: List[Commit]) -> None:
    """Muestra preview de los tags que se crearán."""
    clear_screen()
    processed_commits = [c for c in commits if c.version_type]

    if not processed_commits:
        print()
        print(
            f"{Colors.YELLOW}No hay commits procesados para crear etiquetas.{Colors.RESET}"
        )
        print()
        return

    print_header("PREVIEW DE ETIQUETAS A CREAR")

    for commit in processed_commits:
        next_ver = get_next_version(repo, commit.version_type)
        message = commit.custom_message or commit.message

        print()
        print_info("Etiqueta:", next_ver, Colors.GREEN)
        print_info("Commit:", commit.hash[:7], Colors.CYAN)
        print_info("Mensaje:", message, Colors.CYAN)

    print()
    print(f"{Colors.CYAN}{'=' * 41}{Colors.RESET}")
    print(
        f"Total de etiquetas a crear: {Colors.GREEN}{len(processed_commits)}{Colors.RESET}"
    )
    print(f"{Colors.CYAN}{'=' * 41}{Colors.RESET}")
    print()


def paginate_items(items: List[tuple], header: str, items_per_page: int = 10) -> None:
    """Muestra items con paginación interactiva.

    Args:
        items: Lista de tuplas (nombre, hash, fecha, mensaje)
        header: Encabezado a mostrar
        items_per_page: Cantidad de items por página
    """
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = 1

    while current_page <= total_pages:
        clear_screen()
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = items[start_idx:end_idx]

        print_header(f"{header} (Página {current_page}/{total_pages})")

        for i, (name, commit_hash, date, message) in enumerate(
            page_items, start=start_idx + 1
        ):
            print(f"{Colors.CYAN}{i:2d}. {name:<15}{Colors.RESET}", end="")
            print(f"{Colors.CYAN}{commit_hash[:7]}{Colors.RESET}", end="")
            print(f"  {date:<17} ", end="")
            print(f"{Colors.WHITE}{message}{Colors.RESET}")

        print()
        print(f"{Colors.CYAN}{'=' * 41}{Colors.RESET}")

        if total_pages > 1:
            print(f"{Colors.YELLOW}Página {current_page}/{total_pages}{Colors.RESET}")
            if current_page < total_pages:
                print(
                    f"{Colors.WHITE}Presiona {Colors.YELLOW}n{Colors.WHITE} para siguiente página, {Colors.YELLOW}q{Colors.WHITE} para salir{Colors.RESET}"
                )
                choice = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()
            else:
                print(
                    f"{Colors.WHITE}Presiona {Colors.YELLOW}q{Colors.WHITE} para salir{Colors.RESET}"
                )
                choice = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()

            if choice == "n" and current_page < total_pages:
                current_page += 1
            elif choice == "q" or choice == "":
                break
        else:
            wait_for_enter()
            break


def show_local_tags(repo: git.Repo) -> None:
    """Muestra todos los tags locales del repositorio con paginación.

    Args:
        repo: Repositorio Git
    """
    local_tags = sorted(repo.tags, key=lambda t: parse_version(t.name), reverse=True)

    if not local_tags:
        clear_screen()
        print()
        print(f"{Colors.YELLOW}No hay tags locales en este repositorio.{Colors.RESET}")
        print()
        wait_for_enter()
        return

    items = []
    for tag in local_tags:
        tag_commit = tag.commit
        message = tag_commit.message.split("\n")[0]
        date = tag_commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
        items.append((tag.name, tag_commit.hexsha, date, message))

    paginate_items(items, f"TAGS LOCALES ({len(items)} encontrados)")


def show_remote_tags(repo: git.Repo) -> None:
    """Muestra todos los tags remotos del repositorio con paginación.

    Args:
        repo: Repositorio Git
    """
    clear_screen()

    try:
        if not repo.remotes:
            print()
            print(
                f"{Colors.YELLOW}No hay remotos configurados en este repositorio.{Colors.RESET}"
            )
            print()
            wait_for_enter()
            return

        origin = repo.remotes.origin if repo.remotes.origin else repo.remotes[0]

        print_header("SINCRONIZANDO TAGS REMOTOS...")
        print(f"{Colors.YELLOW}Actualizando información del remoto...{Colors.RESET}")
        origin.fetch(tags=True, force=True)
        print(f"{Colors.GREEN}Actualización completada.{Colors.RESET}")
        print()
        wait_for_enter()

        try:
            git_cmd = repo.git
            ls_remote_output = git_cmd.ls_remote("--tags", "origin")

            if not ls_remote_output:
                clear_screen()
                print()
                print(
                    f"{Colors.YELLOW}No hay tags remotos en {origin.url}.{Colors.RESET}"
                )
                print()
                wait_for_enter()
                return

            remote_tags_dict = {}
            for line in ls_remote_output.split("\n"):
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    commit_hash = parts[0]
                    ref_path = parts[1]

                    if ref_path.endswith("^{}"):
                        continue

                    if ref_path.startswith("refs/tags/"):
                        tag_name = ref_path.replace("refs/tags/", "")
                        if tag_name not in remote_tags_dict:
                            remote_tags_dict[tag_name] = commit_hash

            if not remote_tags_dict:
                clear_screen()
                print()
                print(
                    f"{Colors.YELLOW}No hay tags remotos en {origin.url}.{Colors.RESET}"
                )
                print()
                wait_for_enter()
                return

            sorted_tags = sorted(
                remote_tags_dict.items(),
                key=lambda x: parse_version(x[0]),
                reverse=True,
            )

            items = []
            for tag_name, commit_hash in sorted_tags:
                try:
                    commit_obj = repo.commit(commit_hash)
                    message = (
                        commit_obj.message.split("\n")[0]
                        if commit_obj.message
                        else "Sin mensaje"
                    )
                    date = commit_obj.committed_datetime.strftime("%Y-%m-%d %H:%M")
                    items.append((tag_name, commit_hash, date, message))
                except Exception:
                    items.append(
                        (tag_name, commit_hash, "No disponible", "Sin mensaje")
                    )

            paginate_items(items, f"TAGS REMOTOS ({len(items)} encontrados)")

        except Exception as e:
            clear_screen()
            print()
            print(f"{Colors.YELLOW}No hay tags remotos disponibles.{Colors.RESET}")
            if str(e):
                print(f"{Colors.YELLOW}Detalle: {str(e)}{Colors.RESET}")
            print()
            wait_for_enter()

    except Exception as e:
        clear_screen()
        print()
        print(f"{Colors.RED}Error al consultar tags remotos: {str(e)}{Colors.RESET}")
        print()
        wait_for_enter()
