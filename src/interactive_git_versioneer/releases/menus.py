"""Menús interactivos (entry points del paquete releases)."""

import os
import sys

try:
    import git
except ImportError:
    print("Error: GitPython is not installed")
    print("Install it with: pip install GitPython")
    sys.exit(1)

try:
    from packaging.version import parse as parse_version
except ImportError:
    parse_version = None

from ..core.git_ops import get_last_tag, get_untagged_commits
from ..core.ui import Colors, Menu, wait_for_enter
from ..core.version_ops import action_update_project_version
from .changelog_actions import (
    action_generate_all_changelogs_with_ai,
    edit_changelog_file,
    save_changelog_from_progress,
    show_generate_changelog,
    view_local_changelog,
)
from .changelog_progress import _load_changelog_progress
from .gh_auth import auth_github_cli, check_gh_auth
from .gh_releases import (
    create_github_release,
    delete_github_release,
    edit_github_release,
    get_releases,
    list_releases,
    select_release_from_list,
)
from .sync import sync_with_remote


def action_select_and_delete_release() -> bool:
    """Permite al usuario seleccionar y eliminar un release de GitHub."""
    # clear_screen() # The select_release_from_list already clears the screen
    selected_tag = select_release_from_list()
    if selected_tag:
        delete_github_release(selected_tag)
    return False


def action_select_and_edit_release() -> bool:
    """Permite al usuario seleccionar y editar un release de GitHub."""
    # clear_screen() # The select_release_from_list already clears the screen
    selected_tag = select_release_from_list()
    if selected_tag:
        edit_github_release(selected_tag)
    return False


def run_changelog_submenu(repo: git.Repo) -> bool:
    """Ejecuta el submenú de generación de changelogs.

    Args:
        repo: Repositorio Git

    Returns:
        bool: False para permanecer en el menú de releases
    """
    from ..core.logger import get_logger

    logger = get_logger()
    logger.function_enter("run_changelog_submenu")

    def show_changelog_status():
        """Muestra el estado actual para changelogs."""
        import re

        last_tag = get_last_tag(repo)

        # Contar total de tags en el repositorio (excluyendo "Unreleased")
        total_tags = len([t for t in repo.tags if t.name != "Unreleased"])

        # Contar commits sin etiquetar
        untagged_commits = get_untagged_commits(repo)
        num_untagged = len(untagged_commits)

        # Obtener último changelog en el archivo CHANGELOG.md
        repo_root = repo.working_dir
        changelog_path = os.path.join(repo_root, "CHANGELOG.md")
        last_file_changelog = None
        last_file_changelog_date = None
        total_changelogs_in_file = 0
        has_unreleased_entry = False
        unreleased_date = None
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Contar todas las versiones en el archivo (con fecha)
                all_versions_with_dates = re.findall(
                    r"##\s*\[([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})", content
                )
                # Filtrar "Unreleased" ya que es una entrada temporal para commits pendientes
                tagged_versions = [
                    (ver, date)
                    for ver, date in all_versions_with_dates
                    if ver != "Unreleased"
                ]
                # Buscar entrada Unreleased (commits sin tag pendientes)
                unreleased_versions = [
                    (ver, date)
                    for ver, date in all_versions_with_dates
                    if ver == "Unreleased"
                ]
                has_unreleased_entry = len(unreleased_versions) > 0
                unreleased_date = (
                    unreleased_versions[0][1] if unreleased_versions else None
                )
                total_changelogs_in_file = len(tagged_versions)
                if tagged_versions:
                    last_file_changelog = tagged_versions[0][0]
                    last_file_changelog_date = tagged_versions[0][1]
            except Exception:
                pass

        # Calcular changelogs pendientes
        # Si existe entrada "Unreleased", los commits sin tag ya están documentados
        # y no cuentan como pendientes
        pending_tags = (
            total_tags - total_changelogs_in_file
            if total_tags > total_changelogs_in_file
            else 0
        )
        pending_untagged = 0 if has_unreleased_entry else num_untagged
        total_pending = pending_tags + pending_untagged
        # Total esperado: tags actuales + commits sin tag (solo si no hay Unreleased)
        total_expected = total_tags + pending_untagged

        # El changelog está completo si no hay tags pendientes
        # (los commits sin tag cubiertos por Unreleased no son "pendientes")
        is_complete = total_pending == 0

        # Mostrar changelogs registrados primero
        if total_changelogs_in_file > 0:
            if is_complete:
                print(
                    f"{Colors.WHITE}Changelogs registrados: {total_changelogs_in_file}/{total_expected} {Colors.GREEN}✓ completo{Colors.RESET}"
                )
            elif total_pending > 0:
                print(
                    f"{Colors.WHITE}Changelogs registrados: {total_changelogs_in_file}/{total_expected} {Colors.YELLOW}⚠ {total_pending} pendiente(s){Colors.RESET}"
                )
            else:
                print(
                    f"{Colors.WHITE}Changelogs registrados: {total_changelogs_in_file}/{total_expected} {Colors.YELLOW}⚠ incompleto{Colors.RESET}"
                )
        else:
            print(
                f"{Colors.WHITE}Changelogs registrados: 0/{total_expected} {Colors.YELLOW}⚠ {total_expected} pendiente(s){Colors.RESET}"
            )

        # Mostrar último changelog en el archivo
        if last_file_changelog:
            date_str = (
                f" ({last_file_changelog_date})" if last_file_changelog_date else ""
            )
            if last_tag:
                if last_file_changelog == last_tag:
                    print(
                        f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str} {Colors.GREEN}✓ sincronizado con tag{Colors.RESET}"
                    )
                else:
                    # Comparar versiones para determinar si está adelantado o atrasado
                    if parse_version:
                        try:
                            file_ver = parse_version(last_file_changelog)
                            tag_ver = parse_version(last_tag)
                            if file_ver > tag_ver:
                                print(
                                    f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str} {Colors.CYAN}→ registro adelantado{Colors.RESET}"
                                )
                            else:
                                print(
                                    f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str} {Colors.YELLOW}⚠ desactualizado{Colors.RESET}"
                                )
                        except Exception:
                            print(
                                f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str} {Colors.YELLOW}⚠ desactualizado{Colors.RESET}"
                            )
                    else:
                        print(
                            f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str} {Colors.YELLOW}⚠ desactualizado{Colors.RESET}"
                        )
            else:
                print(
                    f"{Colors.WHITE}Último changelog (archivo): {last_file_changelog}{date_str}{Colors.RESET}"
                )
        else:
            print(
                f"{Colors.WHITE}Último changelog (archivo): {Colors.YELLOW}(ninguno){Colors.RESET}"
            )

        # Mostrar entrada Unreleased si existe (commits sin tag pendientes)
        if has_unreleased_entry:
            unreleased_str = f" ({unreleased_date})" if unreleased_date else ""
            print(
                f"{Colors.WHITE}Changelog pendiente: Unreleased{unreleased_str} {Colors.CYAN}→ commits sin etiquetar{Colors.RESET}"
            )

        # Mostrar último tag
        if last_tag:
            print(f"{Colors.WHITE}Último tag: {last_tag}{Colors.RESET}")
        else:
            print(f"{Colors.WHITE}Último tag: {Colors.YELLOW}(ninguno){Colors.RESET}")

        # Mostrar commits sin etiquetar
        if num_untagged > 0:
            print(
                f"{Colors.WHITE}Commits sin tag: {Colors.YELLOW}{num_untagged} pendiente(s) de etiquetar{Colors.RESET}"
            )

    def action_preview():
        view_local_changelog(repo)
        return False

    def action_manual():
        show_generate_changelog(repo)
        wait_for_enter()
        return False

    def action_auto_ai():
        from ..core.logger import get_logger

        logger = get_logger()
        logger.function_enter(
            "action_auto_ai", menu="GESTIÓN DE CHANGELOGS", option="3"
        )
        action_generate_all_changelogs_with_ai(repo, rebuild=False)
        logger.function_exit("action_auto_ai", return_value=False)
        return False

    def action_edit():
        edit_changelog_file(repo)
        return False

    def action_rebuild_with_ai():
        # Preguntar confirmación antes de eliminar
        print()
        print(
            f"{Colors.RED}⚠️  Esta opción eliminará el archivo CHANGELOG.md actual{Colors.RESET}"
        )
        print(
            f"{Colors.RED}    y regenerará todos los changelogs desde cero con IA.{Colors.RESET}"
        )
        print()
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
            # Eliminar archivo changelog existente
            repo_root = repo.working_dir
            changelog_path = os.path.join(repo_root, "CHANGELOG.md")
            if os.path.exists(changelog_path):
                try:
                    os.remove(changelog_path)
                    print(
                        f"{Colors.YELLOW}Archivo CHANGELOG.md eliminado.{Colors.RESET}"
                    )
                except Exception as e:
                    print(f"{Colors.RED}Error al eliminar archivo: {e}{Colors.RESET}")

            # Generar todos los changelogs con IA
            action_generate_all_changelogs_with_ai(repo, rebuild=True)

            # Guardar los changelogs generados en el archivo CHANGELOG.md
            print()
            print(f"{Colors.CYAN}Guardando changelogs en archivo...{Colors.RESET}")
            save_changelog_from_progress(repo, changelog_path)
            print()
            print(
                f"{Colors.YELLOW}Recuerda hacer commit del archivo para persistir los cambios.{Colors.RESET}"
            )
            wait_for_enter()
        else:
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            wait_for_enter()
        return False

    def action_save_to_file():
        """Guarda los changelogs generados al archivo CHANGELOG.md."""
        print()
        repo_root = repo.working_dir
        changelog_path = os.path.join(repo_root, "CHANGELOG.md")

        progress = _load_changelog_progress(repo)
        if not progress:
            print(
                f"{Colors.YELLOW}No hay changelogs generados en progreso para guardar.{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}Primero genera changelogs con '3. Continuar changelog (automático con IA)' o '6. Reconstruir todos los changelogs (con IA)'.{Colors.RESET}"
            )
            wait_for_enter()
            return False

        last_tag = get_last_tag(repo)
        if last_tag and not any(key.endswith(f"→{last_tag}") for key in progress):
            print(
                f"{Colors.YELLOW}⚠️  El progreso no incluye el último tag ({last_tag}).{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}Genera el changelog pendiente con la opción 3 o 6 para incluirlo.{Colors.RESET}"
            )
            print()
            try:
                proceed = (
                    input(
                        f"{Colors.WHITE}¿Guardar igualmente con el progreso actual? (s/n): {Colors.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except KeyboardInterrupt:
                print()
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                wait_for_enter()
                return False

            if proceed != "s":
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                wait_for_enter()
                return False

        # Verificar si existe el archivo
        if os.path.exists(changelog_path):
            print(f"{Colors.YELLOW}⚠️  El archivo CHANGELOG.md ya existe.{Colors.RESET}")
            print(
                f"{Colors.YELLOW}   Se sobrescribirá con los changelogs generados.{Colors.RESET}"
            )
            print()
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

            if confirm != "s":
                print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
                wait_for_enter()
                return False

        if save_changelog_from_progress(repo, changelog_path):
            print()
            print(
                f"{Colors.GREEN}✓ Changelogs guardados exitosamente en CHANGELOG.md{Colors.RESET}"
            )
            print()
            print(
                f"{Colors.YELLOW}Recuerda hacer commit del archivo para persistir los cambios.{Colors.RESET}"
            )
        else:
            print()
            print(f"{Colors.RED}✗ No se pudieron guardar los changelogs.{Colors.RESET}")
            print()
            print(
                f"{Colors.WHITE}Asegúrate de haber generado changelogs primero usando la opción '3. Continuar changelog (automático con IA)'.{Colors.RESET}"
            )
        wait_for_enter()
        return False

    def action_back():
        return True

    menu = Menu("GESTIÓN DE CHANGELOGS")
    menu.set_status_callback(show_changelog_status)
    menu.add_item("1", "Previsualizar changelog", action_preview)
    menu.add_item("2", "Continuar changelog (manualmente)", action_manual)
    menu.add_item("3", "Continuar changelog (automático con IA)", action_auto_ai)
    menu.add_item("4", "Modificar changelogs", action_edit)
    menu.add_item("5", "Guardar en archivo CHANGELOG.md", action_save_to_file)
    menu.add_item(
        "6", "Reconstruir todos los changelogs (con IA)", action_rebuild_with_ai
    )
    menu.add_item("0", "Volver", action_back)

    logger.info("Ejecutando menú de changelogs...")
    menu.run()
    logger.function_exit("run_changelog_submenu", return_value=False)
    return False


def run_releases_menu(repo: git.Repo) -> bool:
    """Ejecuta el submenú de gestión de releases.

    Args:
        repo: Repositorio Git

    Returns:
        bool: True si se debe volver al menú principal
    """

    def show_releases_status():
        """Muestra el estado actual de releases."""
        # Proveedor y origen de releases
        releases_url = None
        try:
            remote_url = repo.remotes.origin.url
            # Detectar proveedor
            if "github.com" in remote_url:
                provider = "GitHub"
            elif "gitlab.com" in remote_url:
                provider = "GitLab"
            elif "bitbucket.org" in remote_url:
                provider = "Bitbucket"
            else:
                provider = "Git"
            # Convertir SSH a HTTPS si es necesario
            if remote_url.startswith("git@github.com:"):
                remote_url = remote_url.replace(
                    "git@github.com:", "https://github.com/"
                )
            elif remote_url.startswith("git@gitlab.com:"):
                remote_url = remote_url.replace(
                    "git@gitlab.com:", "https://gitlab.com/"
                )
            elif remote_url.startswith("git@bitbucket.org:"):
                remote_url = remote_url.replace(
                    "git@bitbucket.org:", "https://bitbucket.org/"
                )
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            releases_url = f"{remote_url}/releases"
            print(f"{Colors.WHITE}Proveedor: {provider}{Colors.RESET}")
        except Exception:
            print(
                f"{Colors.WHITE}Proveedor: {Colors.YELLOW}(no configurado){Colors.RESET}"
            )

        # Usuario autenticado
        is_authenticated, user_or_error = check_gh_auth()
        if is_authenticated:
            print(f"{Colors.WHITE}Usuario: {user_or_error}{Colors.RESET}")

        # Último release en remoto
        last_remote_release = None
        if is_authenticated:
            releases, error = get_releases(limit=1)
            if releases and not error:
                last_remote_release = releases[0]["tag"]
                print(
                    f"{Colors.WHITE}Último release (remoto): {last_remote_release}{Colors.RESET}"
                )
            elif not error:
                print(
                    f"{Colors.WHITE}Último release (remoto): {Colors.YELLOW}(ninguno){Colors.RESET}"
                )
        else:
            print(
                f"{Colors.WHITE}Último release (remoto): {Colors.YELLOW}(no autenticado){Colors.RESET}"
            )

        # Mostrar último tag local
        last_tag = get_last_tag(repo)
        if last_tag:
            # Mostrar si tiene release vinculado
            if last_remote_release and last_tag == last_remote_release:
                print(
                    f"{Colors.WHITE}Último tag: {last_tag} {Colors.GREEN}✓ con release{Colors.RESET}"
                )
            else:
                print(
                    f"{Colors.WHITE}Último tag: {last_tag} {Colors.YELLOW}⚠ sin release vinculado{Colors.RESET}"
                )
        else:
            print(f"{Colors.WHITE}Último tag: {Colors.YELLOW}(ninguno){Colors.RESET}")

        # Mostrar último changelog registrado en el archivo
        repo_root = repo.working_dir
        changelog_path = os.path.join(repo_root, "CHANGELOG.md")
        if os.path.exists(changelog_path):
            try:
                import re

                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Buscar la primera versión en el formato ## [vX.X.X]
                match = re.search(r"##\s*\[([^\]]+)\]", content)
                if match:
                    last_changelog_version = match.group(1)
                    print(
                        f"{Colors.WHITE}Último changelog: {last_changelog_version}{Colors.RESET}"
                    )
                else:
                    print(
                        f"{Colors.WHITE}Último changelog: {Colors.YELLOW}(ninguno){Colors.RESET}"
                    )
            except Exception:
                print(
                    f"{Colors.WHITE}Último changelog: {Colors.RED}(error al leer){Colors.RESET}"
                )
        else:
            print(
                f"{Colors.WHITE}Último changelog: {Colors.YELLOW}(archivo no existe){Colors.RESET}"
            )

        # Mostrar link al final
        if releases_url:
            print(f"{Colors.CYAN}{releases_url}{Colors.RESET}")

    def action_authenticate():
        auth_github_cli()
        wait_for_enter()
        return False

    def action_create_release():
        create_github_release(repo)
        wait_for_enter()
        return False

    def action_list_releases():
        list_releases()
        wait_for_enter()
        return False

    def action_edit_release():
        selected_tag = select_release_from_list()
        if selected_tag:
            edit_github_release(selected_tag)
            wait_for_enter()
        # Si se canceló, select_release_from_list ya llamó wait_for_enter
        return False

    def action_delete_release():
        selected_tag = select_release_from_list()
        if selected_tag:
            delete_github_release(selected_tag)
        # delete_github_release y select_release_from_list ya llaman wait_for_enter
        return False

    def action_update_version():
        action_update_project_version(repo)
        return False

    def action_sync():
        sync_with_remote(repo)
        return False

    def action_back():
        return True

    menu = Menu("GESTIÓN DE RELEASES")
    menu.set_status_callback(show_releases_status)
    menu.add_item("1", "Autenticar con GitHub", action_authenticate)
    menu.add_item("2", "Crear release en GitHub", action_create_release)
    menu.add_item("3", "Ver releases existentes", action_list_releases)
    menu.add_item("4", "Modificar un release existente", action_edit_release)
    menu.add_item("5", "Eliminar un release existente", action_delete_release)
    menu.add_item("6", "Actualizar versión del proyecto", action_update_version)
    menu.add_item("7", "Sincronizar con remoto", action_sync)
    menu.add_item("0", "Volver al menú principal", action_back)

    menu.run()
    return True
