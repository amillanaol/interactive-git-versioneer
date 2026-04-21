"""
Main menu for interactive-git-versioneer.

Contains the main menu with options for Commits, Tags, Releases, Changelogs, and Config.
"""

import os
import re

from .. import __version__
from ..config import run_config_menu
from ..core.git_ops import get_last_tag, get_untagged_commits
from ..core.ui import (
    Colors,
    Menu,
    clear_screen,
    print_header,
    wait_for_enter,
)
from ..releases.changelog_actions import get_latest_changelog_section
from ..releases.gh_releases import check_release_exists
from ..releases.menus import run_releases_menu
from ..tags.actions import push_tags_to_remote, sync_tags_from_remote
from ..tags.ai import auto_generate_all_with_ai
from ..tags.menus import run_commits_submenu, run_tag_settings_menu
from ..tags.tagger import run_tag_management_submenu
from ..tags.views import show_commit_list


def run_main_menu(repo, dry_run=False, push=False) -> bool:
    """Run the main interactive menu.

    Args:
        repo: Git repository object
        dry_run: If True, show what would be done without executing
        push: If True, push tags to remote after creation

    Returns:
        bool: True if should exit, False otherwise
    """

    def show_main_status():
        """Muestra el estado actual del repositorio con dashboard avanzado."""
        current_untagged = get_untagged_commits(repo)

        print(
            f"{Colors.CYAN}────────────────────────────────────────────────────────────{Colors.RESET}"
        )
        print(f"{Colors.WHITE}  ESTADO DEL REPOSITORIO{Colors.RESET}")
        print(
            f"{Colors.CYAN}────────────────────────────────────────────────────────────{Colors.RESET}"
        )

        if len(current_untagged) == 0:
            print(
                f"  {Colors.GREEN}✓{Colors.RESET} {Colors.WHITE}Commits:{Colors.RESET} {Colors.GREEN}Sin pendientes{Colors.RESET}"
            )
        else:
            print(
                f"  {Colors.YELLOW}●{Colors.RESET} {Colors.WHITE}Commits:{Colors.RESET} {Colors.YELLOW}{len(current_untagged)} pendiente(s) por etiquetar{Colors.RESET}"
            )

        last_tag = get_last_tag(repo)

        changelog_version = None
        repo_root = repo.working_dir
        changelog_path = os.path.join(repo_root, "CHANGELOG.md")
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(r"##\s*\[([^\]]+)\]", content)
                if match:
                    changelog_version = match.group(1)
            except Exception:
                pass

        if last_tag:
            has_release = False
            try:
                has_release = check_release_exists(last_tag)
            except Exception:
                pass

            release_indicator = (
                f"{Colors.GREEN}✓ Release{Colors.RESET}"
                if has_release
                else f"{Colors.YELLOW}○ Sin release{Colors.RESET}"
            )

            changelog_indicator = ""
            if changelog_version:
                if last_tag == changelog_version:
                    changelog_indicator = f"{Colors.GREEN} ✓ Changelog OK{Colors.RESET}"
                else:
                    changelog_indicator = f"{Colors.YELLOW} ⚠ Desactualizado ({changelog_version}){Colors.RESET}"

            print(
                f"  {Colors.CYAN}●{Colors.RESET} {Colors.WHITE}Versión actual:{Colors.RESET} {Colors.CYAN}{last_tag}{Colors.RESET} {release_indicator}{changelog_indicator}"
            )
        else:
            print(
                f"  {Colors.YELLOW}○{Colors.RESET} {Colors.WHITE}Versión actual:{Colors.RESET} {Colors.YELLOW}(sin versionado){Colors.RESET}"
            )

        print(
            f"{Colors.CYAN}────────────────────────────────────────────────────────────{Colors.RESET}"
        )

    def get_current_author() -> str:
        """Obtiene el autor actual desde múltiples fuentes."""
        # 1. Intentar desde pyproject.toml
        try:
            pyproject_path = os.path.join(repo.working_dir, "pyproject.toml")
            with open(pyproject_path, "rb") as f:
                import tomli

                pyproject = tomli.load(f)
            project_info = pyproject.get("project", {})
            authors = project_info.get("authors", [])
            if authors:
                author_name = authors[0].get("name")
                if author_name:
                    return author_name
        except Exception:
            pass

        # 2. Intentar desde git config global
        try:
            git_author = repo.git.config("--global", "user.name")
            if git_author:
                return git_author
        except Exception:
            pass

        # 3. Fallback: intentar obtener del último commit
        try:
            commits = list(repo.iter_commits(max_count=1))
            if commits:
                return commits[0].author.name
        except Exception:
            pass

        return "amillanaol"

    def get_footer_status() -> str:
        """Retorna el string de estado para el footer del menú."""
        import tomli

        # Obtener versión desde pyproject.toml
        try:
            pyproject_path = os.path.join(repo.working_dir, "pyproject.toml")
            with open(pyproject_path, "rb") as f:
                pyproject = tomli.load(f)
            project_info = pyproject.get("project", {})
            version_from_toml = project_info.get("version", "unknown")
        except Exception:
            version_from_toml = __version__

        author_name = get_current_author()

        version_label = (
            version_from_toml if version_from_toml != "unknown" else get_last_tag(repo)
        )
        if not version_label:
            version_label = version_from_toml
        if not version_label.startswith("v"):
            version_label = f"v{version_label}"

        return f"{Colors.WHITE}● {author_name} | igv {version_label}{Colors.RESET}"

    def action_manage_commits():
        """Abre el submenú de gestión de commits."""
        nonlocal repo
        commits = get_untagged_commits(repo)
        run_commits_submenu(repo, commits, dry_run, push)
        return False

    def action_open_tags_submenu():
        """Abre el submenú de gestión de tags."""
        nonlocal repo
        commits = get_untagged_commits(repo)
        run_tag_management_submenu(repo, commits, dry_run, push)
        return False

    def action_manage_releases():
        """Abre el submenú de gestión de releases."""
        run_releases_menu(repo)
        return False

    def action_manage_changelogs():
        """Abre el submenú de generación de changelogs."""
        from ..releases.menus import run_changelog_submenu

        run_changelog_submenu(repo)
        return False

    def action_config():
        """Abre el menú de configuración."""
        run_config_menu()
        return False

    def action_back():
        """Salir del programa."""
        return True

    # Crear menú principal
    main_menu = Menu("INTERACTIVE GIT VERSIONEER")
    main_menu.set_status_callback(show_main_status)
    main_menu.set_footer_callback(get_footer_status)

    main_menu.add_item(
        "1", "Commits   → Revisar y etiquetar cambios", action_manage_commits
    )
    main_menu.add_item(
        "2", "Tags      → Gestionar versiones semánticas", action_open_tags_submenu
    )
    main_menu.add_item(
        "3", "Releases  → Publicar en GitHub/GitLab", action_manage_releases
    )
    main_menu.add_item(
        "4", "Changelogs→ Documentar cambios del proyecto", action_manage_changelogs
    )
    main_menu.add_item("5", "Config    → Ajustes de API y preferencias", action_config)
    main_menu.add_item("0", "Salir     → Cerrar aplicación", action_back)

    return main_menu.run(is_main_menu=True)
