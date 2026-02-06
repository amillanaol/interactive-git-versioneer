"""CRUD de releases en GitHub."""

import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import git
    from git import Repo
except ImportError:
    print("Error: GitPython is not installed")
    print("Install it with: pip install GitPython")
    sys.exit(1)

from ..core.git_ops import parse_version
from ..core.ui import Colors, clear_screen, print_header, print_info, wait_for_enter
from .changelog_gen import generate_changelog
from .gh_auth import auth_github_cli, check_gh_auth, check_gh_cli


def get_changelog_for_tag(repo: Repo, tag_name: str) -> Optional[str]:
    """Extrae el changelog de un tag específico desde el archivo CHANGELOG.md.

    Args:
        repo: El repositorio Git.
        tag_name: El nombre del tag a buscar.

    Returns:
        El contenido del changelog para ese tag, o None si no existe.
    """
    repo_root = repo.working_dir
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")

    if not os.path.exists(changelog_path):
        return None

    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Buscar la sección del tag específico
        # Formato: ## [vX.X.X] - YYYY-MM-DD
        pattern = rf"##\s*\[{re.escape(tag_name)}\][^\n]*\n(.*?)(?=##\s*\[|---|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            changelog_content = match.group(1).strip()
            if changelog_content:
                return changelog_content

        return None
    except Exception:
        return None


def get_releases(limit: int = 10) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Retrieves a list of releases from GitHub.

    Args:
        limit: The maximum number of releases to retrieve.

    Returns:
        Tuple[List[Dict[str, str]], Optional[str]]: A tuple containing a list of release
            dictionaries and an optional error message.
    """
    if not check_gh_cli():
        return [], "GitHub CLI is not installed"

    # Check authentication
    is_auth: bool
    auth_info: str
    is_auth, auth_info = check_gh_auth()
    if not is_auth:
        return [], auth_info

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["gh", "release", "list", "--limit", str(limit)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            if (
                "not authorized" in result.stderr.lower()
                or "permission denied" in result.stderr.lower()
            ):
                return [], "Not authenticated or no permissions. Run: gh auth login"
            if (
                "no releases found" in result.stderr.lower()
                or not result.stdout.strip()
            ):
                return [], None  # Not an error, simply no releases
            return [], result.stderr or "Unknown error"

        releases: List[Dict[str, str]] = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts: List[str] = line.split("\t")
                # gh release list output: TITLE, TYPE (Latest/Draft/Pre-release), TAG, DATE
                if len(parts) >= 3:
                    releases.append(
                        {
                            "title": parts[0],
                            "type": parts[1] if len(parts) > 1 else "",
                            "tag": parts[2] if len(parts) > 2 else "",
                            "date": parts[3] if len(parts) > 3 else "",
                            "is_draft": "Draft" in (parts[1] if len(parts) > 1 else ""),
                        }
                    )
        return releases, None
    except Exception as e:
        return [], str(e)


def list_releases() -> None:
    """Displays the list of existing releases on GitHub with pagination."""
    if not check_gh_cli():
        clear_screen()
        print_header("RELEASES ON GITHUB")
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install it from: https://cli.github.com/{Colors.RESET}")
        print()
        return

    # Check authentication
    is_auth: bool
    auth_info: str
    is_auth, auth_info = check_gh_auth()
    if not is_auth:
        clear_screen()
        print_header("RELEASES ON GITHUB")
        print(f"{Colors.RED}Authentication error: {auth_info}{Colors.RESET}")
        print()
        print(f"{Colors.YELLOW}Do you want to log in now?{Colors.RESET}")
        response: str = input(f"{Colors.WHITE}(y/n): {Colors.RESET}").strip().lower()
        if response == "y":
            auth_github_cli()
        return

    releases: List[Dict[str, str]]
    error: Optional[str]
    releases, error = get_releases(limit=100)

    if error:
        clear_screen()
        print_header("RELEASES ON GITHUB")
        print(f"{Colors.YELLOW}{error}{Colors.RESET}")
        return

    if not releases:
        clear_screen()
        print_header("RELEASES ON GITHUB")
        print(f"{Colors.YELLOW}No releases found.{Colors.RESET}")
        return

    # Pagination
    items_per_page: int = 10
    total_releases: int = len(releases)
    total_pages: int = (total_releases + items_per_page - 1) // items_per_page
    current_page: int = 0

    while True:
        clear_screen()
        print_header(f"RELEASES ON GITHUB - Page {current_page + 1}/{total_pages}")
        print(f"{Colors.WHITE}Total releases: {total_releases}{Colors.RESET}")
        print()

        start_idx: int = current_page * items_per_page
        end_idx: int = min(start_idx + items_per_page, total_releases)

        for idx, release in enumerate(releases[start_idx:end_idx], start=start_idx + 1):
            release_type: str = release.get("type", "")
            status_color: str = (
                Colors.YELLOW if release.get("is_draft") else Colors.GREEN
            )
            status_text: str = f" ({release_type})" if release_type else ""

            print(f"{Colors.WHITE}{idx}. {Colors.RESET}", end="")
            print(f"{status_color}{release['title']}{status_text}{Colors.RESET}")
            print(f"   Tag: {Colors.CYAN}{release['tag']}{Colors.RESET}")
            print(f"   Date: {Colors.WHITE}{release['date']}{Colors.RESET}")
            print()

        # Navigation
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        nav_options: List[str] = []
        if current_page > 0:
            nav_options.append(f"{Colors.YELLOW}p{Colors.WHITE}=anterior")
        if current_page < total_pages - 1:
            nav_options.append(f"{Colors.YELLOW}n{Colors.WHITE}=siguiente")
        nav_options.append(f"{Colors.YELLOW}0{Colors.WHITE}=salir")

        print(f"{Colors.WHITE}Navegación: {' | '.join(nav_options)}{Colors.RESET}")

        try:
            choice: str = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip().lower()

            if (
                choice == "0"
                or choice == "-back-"
                or choice == "-exit-"
                or choice == ""
            ):
                break
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
        except KeyboardInterrupt:
            break


def select_release_from_list() -> Optional[str]:
    """Allows the user to select a release from a list.

    Returns:
        Optional[str]: The tag name of the selected release, or None if canceled or no releases are available.
    """
    releases: List[Dict[str, str]]
    error: Optional[str]
    releases, error = get_releases(limit=50)  # Get more releases for selection
    if error:
        print(f"{Colors.RED}Error getting releases: {error}{Colors.RESET}")
        wait_for_enter()
        return None

    if not releases:
        print(f"{Colors.YELLOW}No releases found on GitHub.{Colors.RESET}")
        wait_for_enter()
        return None

    print_header("SELECT RELEASE")
    for i, release in enumerate(releases, 1):
        release_type: str = release.get("type", "")
        status_text: str = f" ({release_type})" if release_type else ""
        print(
            f"{Colors.WHITE}{i}. {Colors.CYAN}{release['tag']}{Colors.RESET} - {release['title']}{status_text}{Colors.RESET}"
        )
    print()

    try:
        choice: str = input(
            f"{Colors.WHITE}Select the number of the release to operate (0 to cancel): {Colors.RESET}"
        ).strip()
        if choice == "0":
            print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
            wait_for_enter()
            return None

        idx: int = int(choice) - 1
        if 0 <= idx < len(releases):
            return releases[idx]["tag"]
        else:
            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
            wait_for_enter()
            return None
    except ValueError:
        print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")
        wait_for_enter()
        return None
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
        wait_for_enter()
        return None


def create_github_release(repo: Repo) -> bool:
    """Creates a release on GitHub using gh CLI.

    Args:
        repo: The Git repository object.

    Returns:
        bool: True if the release was created successfully, False otherwise.
    """
    clear_screen()
    print_header("CREATE GITHUB RELEASE")

    if not check_gh_cli():
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install it from: https://cli.github.com/{Colors.RESET}")
        print()
        return False

    # Check authentication
    is_auth: bool
    auth_info: str
    is_auth, auth_info = check_gh_auth()
    if not is_auth:
        print(f"{Colors.RED}Error: {auth_info}{Colors.RESET}")
        print()
        print(f"{Colors.YELLOW}Do you want to log in now?{Colors.RESET}")
        response: str = input(f"{Colors.WHITE}(y/n): {Colors.RESET}").strip().lower()
        if response == "y":
            auth_github_cli()
            return False
        return False

    # Get available tags
    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: parse_version(t.name), reverse=True
    )

    if not tags:
        print(f"{Colors.YELLOW}No tags in the repository.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}First create some tags using the Tag Management option.{Colors.RESET}"
        )
        print()
        return False

    # Get existing releases to mark which ones already have a release
    existing_releases: set[str] = set()
    releases_list: List[Dict[str, str]]
    releases_list, _ = get_releases(limit=100)
    for r in releases_list:
        existing_releases.add(r.get("tag", ""))

    page_size: int = 10
    current_page: int = 0
    total_pages: int = (len(tags) + page_size - 1) // page_size

    selected_tag: Optional[str] = None

    while selected_tag is None:
        # Clear screen and display header on each page
        clear_screen()
        print_header("CREATE GITHUB RELEASE")
        print(f"{Colors.GREEN}Authenticated as: {auth_info}{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}Available tags ({len(tags)} total):{Colors.RESET}")
        print(f"{Colors.CYAN}  [✓] = already has release on GitHub{Colors.RESET}")
        print()

        start_idx: int = current_page * page_size
        end_idx: int = min(start_idx + page_size, len(tags))

        for i, tag in enumerate(tags[start_idx:end_idx], start_idx + 1):
            has_release: str = "✓" if tag.name in existing_releases else " "
            tag_date: str = datetime.fromtimestamp(tag.commit.committed_date).strftime(
                "%Y-%m-%d"
            )
            print(
                f"  {Colors.CYAN}{i:3}.{Colors.RESET} [{has_release}] {tag.name} ({tag_date})"
            )

        print()
        print(f"{Colors.WHITE}Page {current_page + 1}/{total_pages}{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Options: [n]next [p]previous [number]select [0]cancel{Colors.RESET}"
        )

        try:
            choice: str = (
                input(f"{Colors.WHITE}Selection: {Colors.RESET}").strip().lower()
            )

            if choice == "0":
                print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
                return False
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
            else:
                try:
                    tag_idx: int = int(choice) - 1
                    if 0 <= tag_idx < len(tags):
                        selected_tag = tags[tag_idx].name
                        if selected_tag in existing_releases:
                            print()
                            print(
                                f"{Colors.YELLOW}⚠ This tag already has a release on GitHub.{Colors.RESET}"
                            )
                            confirm: str = (
                                input(
                                    f"{Colors.WHITE}Create another release for this tag? (y/n): {Colors.RESET}"
                                )
                                .strip()
                                .lower()
                            )
                            if confirm != "y":
                                selected_tag = None
                                continue
                    else:
                        print(
                            f"{Colors.RED}Number out of range. Press Enter...{Colors.RESET}"
                        )
                        input()
                except ValueError:
                    pass  # Invalid option, simply refresh the page
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
            return False

    # Release title
    print()
    default_title: str = f"Release {selected_tag}"
    title_input: str = input(
        f"{Colors.WHITE}Release title (Enter for '{default_title}'): {Colors.RESET}"
    ).strip()
    title: str = title_input if title_input else default_title

    # Generate release notes
    print()

    # Buscar changelog existente en CHANGELOG.md
    existing_changelog: Optional[str] = get_changelog_for_tag(repo, selected_tag)

    notes: str = ""
    generate_notes_flag: bool = False

    if existing_changelog:
        print(
            f"{Colors.GREEN}Se encontró changelog para {selected_tag} en CHANGELOG.md{Colors.RESET}"
        )
        print()
        print(f"{Colors.WHITE}¿Qué notas usar para el release?{Colors.RESET}")
        print(
            f"{Colors.WHITE}1. Usar changelog existente de CHANGELOG.md{Colors.RESET}"
        )
        print(f"{Colors.WHITE}2. Usar notas generadas por GitHub{Colors.RESET}")
        print(f"{Colors.WHITE}3. Ingresar manualmente{Colors.RESET}")
        print()

        notes_choice: str = input(
            f"{Colors.WHITE}Seleccione opción: {Colors.RESET}"
        ).strip()

        if notes_choice == "1":
            notes = existing_changelog
        elif notes_choice == "2":
            generate_notes_flag = True
        elif notes_choice == "3":
            print(
                f"{Colors.WHITE}Ingrese las notas del release (termine con línea vacía):{Colors.RESET}"
            )
            lines: List[str] = []
            while True:
                line: str = input()
                if line == "":
                    break
                lines.append(line)
            notes = "\n".join(lines)
    else:
        print(
            f"{Colors.YELLOW}No se encontró changelog para {selected_tag} en CHANGELOG.md{Colors.RESET}"
        )
        print()
        print(f"{Colors.WHITE}¿Qué notas usar para el release?{Colors.RESET}")
        print(
            f"{Colors.WHITE}1. Generar changelog básico (lista de commits){Colors.RESET}"
        )
        print(f"{Colors.WHITE}2. Usar notas generadas por GitHub{Colors.RESET}")
        print(f"{Colors.WHITE}3. Ingresar manualmente{Colors.RESET}")
        print()

        notes_choice = input(f"{Colors.WHITE}Seleccione opción: {Colors.RESET}").strip()

        if notes_choice == "1":
            # Find previous tag for changelog
            prev_tag: Optional[str] = None
            for i, tag in enumerate(tags):
                if tag.name == selected_tag and i + 1 < len(tags):
                    prev_tag = tags[i + 1].name
                    break
            notes = generate_changelog(repo, prev_tag, selected_tag)
            if not notes:
                print(
                    f"{Colors.YELLOW}No se encontraron commits en el rango. Se usará descripción vacía.{Colors.RESET}"
                )
        elif notes_choice == "2":
            generate_notes_flag = True
        elif notes_choice == "3":
            print(
                f"{Colors.WHITE}Ingrese las notas del release (termine con línea vacía):{Colors.RESET}"
            )
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            notes = "\n".join(lines)

    # Ask if it's draft or prerelease
    print()
    is_draft: bool = (
        input(f"{Colors.WHITE}Create as draft? (y/n): {Colors.RESET}").strip().lower()
        == "y"
    )
    is_prerelease: bool = (
        input(f"{Colors.WHITE}Is it a prerelease? (y/n): {Colors.RESET}")
        .strip()
        .lower()
        == "y"
    )

    # Confirm
    print()
    print_header("CONFIRM RELEASE")
    print_info("Tag:", selected_tag, Colors.GREEN)
    print_info("Title:", title, Colors.CYAN)
    print_info(
        "Draft:",
        "Yes" if is_draft else "No",
        Colors.YELLOW if is_draft else Colors.WHITE,
    )
    print_info(
        "Prerelease:",
        "Yes" if is_prerelease else "No",
        Colors.YELLOW if is_prerelease else Colors.WHITE,
    )

    if notes and not generate_notes_flag:
        print()
        print(f"{Colors.WHITE}Notes:{Colors.RESET}")
        print(notes[:500] + "..." if len(notes) > 500 else notes)

    print()
    confirm = (
        input(f"{Colors.WHITE}Create release? (y/n): {Colors.RESET}").strip().lower()
    )

    if confirm != "y":
        print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
        return False

    # Check if the tag exists on the remote
    print()
    print(f"{Colors.CYAN}Verifying tag on remote repository...{Colors.RESET}")
    try:
        # Check if the tag exists on origin
        check_remote: subprocess.CompletedProcess = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", selected_tag],
            capture_output=True,
            text=True,
            check=False,
        )
        tag_exists_remote: bool = selected_tag in check_remote.stdout

        if not tag_exists_remote:
            print(
                f"{Colors.YELLOW}⚠ The tag '{selected_tag}' does not exist on the remote repository.{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}It is necessary to push the tag before creating the release.{Colors.RESET}"
            )
            print()
            push_confirm: str = (
                input(
                    f"{Colors.WHITE}Push tag '{selected_tag}' to origin? (y/n): {Colors.RESET}"
                )
                .strip()
                .lower()
            )

            if push_confirm != "y":
                print(
                    f"{Colors.YELLOW}Operation canceled. Push the tag manually with:{Colors.RESET}"
                )
                print(f"  git push origin {selected_tag}")
                return False

            # Push the tag
            print(f"{Colors.CYAN}Pushing tag to origin...{Colors.RESET}")
            push_result: subprocess.CompletedProcess = subprocess.run(
                ["git", "push", "origin", selected_tag],
                capture_output=True,
                text=True,
                check=False,
            )

            if push_result.returncode != 0:
                print(f"{Colors.RED}✗ Error pushing tag:{Colors.RESET}")
                print(f"{Colors.RED}{push_result.stderr}{Colors.RESET}")
                return False

            print(f"{Colors.GREEN}✓ Tag pushed successfully{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error verifying remote tag: {e}{Colors.RESET}")
        return False

    # Build command
    cmd: List[str] = ["gh", "release", "create", selected_tag, "--title", title]

    if generate_notes_flag:
        cmd.append("--generate-notes")
    elif notes:
        cmd.extend(["--notes", notes])

    if is_draft:
        cmd.append("--draft")

    if is_prerelease:
        cmd.append("--prerelease")

    # Execute
    print()
    print(f"{Colors.CYAN}Creating release...{Colors.RESET}")

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Release created successfully{Colors.RESET}")
            if result.stdout:
                print(f"{Colors.CYAN}URL: {result.stdout.strip()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}✗ Error creating release:{Colors.RESET}")
            print(f"{Colors.RED}{result.stderr}{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False


def delete_github_release(tag_name: str) -> bool:
    """Deletes a release and its associated tag from GitHub.

    Args:
        tag_name: The name of the tag of the release to delete.

    Returns:
        bool: True if successfully deleted, False otherwise.
    """
    # clear_screen() # Removed to prevent screen from clearing
    print_header("DELETE GITHUB RELEASE")

    if not check_gh_cli():
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install it from: https://cli.github.com/{Colors.RESET}")
        print()
        wait_for_enter()  # Added to allow reading error message
        return False

    is_auth: bool
    auth_info: str
    is_auth, auth_info = check_gh_auth()
    if not is_auth:
        print(f"{Colors.RED}Error: {auth_info}{Colors.RESET}")
        print()
        print(f"{Colors.YELLOW}Do you want to log in now? (y/n): {Colors.RESET}")
        response: str = input().strip().lower()
        if response == "y":
            auth_github_cli()
        wait_for_enter()  # Added to allow reading error message
        return False

    print(
        f"{Colors.WHITE}The release and associated tag '{tag_name}' will be deleted from GitHub.{Colors.RESET}"
    )
    confirm: str = (
        input(
            f"{Colors.RED}Are you sure? This action is irreversible (y/n): {Colors.RESET}"
        )
        .strip()
        .lower()
    )

    if confirm != "y":
        print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
        wait_for_enter()  # Added to allow reading message
        return False

    print(f"{Colors.CYAN}Deleting release '{tag_name}'...{Colors.RESET}")
    try:
        # Command to delete the release and the remote tag
        # gh release delete also deletes the remote tag
        cmd: List[str] = [
            "gh",
            "release",
            "delete",
            tag_name,
            "--yes",
        ]  # --yes to avoid re-prompting

        result: subprocess.CompletedProcess = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print(
                f"{Colors.GREEN}✓ Release and tag '{tag_name}' deleted successfully.{Colors.RESET}"
            )
            if result.stdout:
                print(f"{Colors.CYAN}Output: {result.stdout.strip()}{Colors.RESET}")
            wait_for_enter()  # Added to allow reading success message
            return True
        else:
            print(f"{Colors.RED}✗ Error deleting release '{tag_name}':{Colors.RESET}")
            print(f"{Colors.RED}{result.stderr}{Colors.RESET}")
            if result.stdout:
                print(
                    f"{Colors.YELLOW}Standard output: {result.stdout.strip()}{Colors.RESET}"
                )
            wait_for_enter()  # Added to allow reading error message
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        wait_for_enter()
        return False


def edit_github_release(tag_name: str) -> bool:
    """Edits an existing release on GitHub.

    Args:
        tag_name: The name of the tag of the release to edit.

    Returns:
        bool: True if successfully edited, False otherwise.
    """
    clear_screen()
    print_header("EDIT GITHUB RELEASE")

    if not check_gh_cli():
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install it from: https://cli.github.com/{Colors.RESET}")
        print()
        return False

    is_auth: bool
    auth_info: str
    is_auth, auth_info = check_gh_auth()
    if not is_auth:
        print(f"{Colors.RED}Error: {auth_info}{Colors.RESET}")
        print()
        print(f"{Colors.YELLOW}Do you want to log in now? (y/n): {Colors.RESET}")
        response: str = input().strip().lower()
        if response == "y":
            auth_github_cli()
        return False

    print(
        f"{Colors.WHITE}Editing release for tag: {Colors.CYAN}{tag_name}{Colors.RESET}"
    )
    print(
        f"{Colors.WHITE}You can edit the title, notes, or draft/prerelease properties.{Colors.RESET}"
    )
    print()

    # Get current release information to pre-fill
    current_releases: List[Dict[str, str]]
    _: Optional[str]
    current_releases, _ = get_releases(limit=100)  # Get more to ensure finding the tag
    current_release: Optional[Dict[str, str]] = next(
        (r for r in current_releases if r["tag"] == tag_name), None
    )

    current_title: str = (
        current_release["title"] if current_release else f"Release {tag_name}"
    )
    current_is_draft: bool = current_release["is_draft"] if current_release else False
    # There is no direct way to get if it is prerelease from `gh release list` output
    # but `gh release view` could give more details. For simplicity, we assume non-prerelease
    # if it cannot be easily determined.

    # Ask for new properties
    new_title: str = input(
        f"{Colors.WHITE}New title (Enter for '{current_title}'): {Colors.RESET}"
    ).strip()
    if not new_title:
        new_title = current_title

    # For notes, you can use --notes-file or edit in an external editor.
    # For simplicity, offer option to generate new or leave empty
    print()
    print(f"{Colors.WHITE}How do you want to handle release notes?{Colors.RESET}")
    print(f"{Colors.WHITE}1. Keep current notes (if any){Colors.RESET}")
    print(
        f"{Colors.WHITE}2. Generate notes automatically (based on commits, requires previous tag){Colors.RESET}"
    )
    print(f"{Colors.WHITE}3. Enter notes manually{Colors.RESET}")
    print(f"{Colors.WHITE}4. Open external editor to edit notes{Colors.RESET}")
    print()
    notes_choice: str = input(f"{Colors.WHITE}Select option: {Colors.RESET}").strip()

    notes_cmd_args: List[str] = []
    if notes_choice == "2":
        # We need the repo here, but the function doesn't receive it.
        # This is a design problem. For now, let's simplify.
        # If notes are to be generated, it should have been done upon creation.
        # For editing, it is more likely that existing ones are edited or new ones are entered.
        print(
            f"{Colors.YELLOW}Automatic note generation is not implemented for direct editing here.{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}Please choose another option or edit manually.{Colors.RESET}"
        )
        return False  # Or allow retry

    elif notes_choice == "3":
        print(
            f"{Colors.WHITE}Enter the new release notes (end with empty line):{Colors.RESET}"
        )
        lines: List[str] = []
        while True:
            line: str = input()
            if line == "":
                break
            lines.append(line)
        notes: str = "\n".join(lines)
        if notes:
            notes_cmd_args.extend(["--notes", notes])
    elif notes_choice == "4":
        notes_cmd_args.append(
            "--notes-start-with-tag"
        )  # Opens an editor with notes pre-filled from the tag
        # Or simply "--notes-start-with-empty" if you want to start from scratch

    # Ask if it's draft or prerelease
    # For editing, gh release edit has --draft, --prerelease, --latest
    # and also their counterparts --undraft, --no-prerelease
    print()
    draft_input: str = (
        input(
            f"{Colors.WHITE}Mark as draft? (y/n/keep, current: {{'y' if current_is_draft else 'n'}}): {Colors.RESET}"
        )
        .strip()
        .lower()
    )
    if draft_input == "y":
        new_is_draft: bool = True
    elif draft_input == "n":
        new_is_draft = False
    else:
        new_is_draft = current_is_draft  # Keep

    # We assume we cannot easily know if it's prerelease currently from the `list` command.
    # Editing for prerelease is more complex without the current status.
    # For simplicity, we only ask if it should be MARKED as prerelease or NOT.
    prerelease_input: str = (
        input(f"{Colors.WHITE}Mark as prerelease? (y/n/keep): {Colors.RESET}")
        .strip()
        .lower()
    )
    if prerelease_input == "y":
        new_is_prerelease: bool = True
    elif prerelease_input == "n":
        new_is_prerelease = False
    else:
        new_is_prerelease = (
            False  # Assume no if not specified and we cannot get current status
        )

    # Confirm
    print()
    print_header("CONFIRM RELEASE EDIT")
    print_info("Tag:", tag_name, Colors.GREEN)
    print_info("New Title:", new_title, Colors.CYAN)
    print_info(
        "New Draft:",
        "Yes" if new_is_draft else "No",
        Colors.YELLOW if new_is_draft else Colors.WHITE,
    )
    print_info(
        "New Prerelease:",
        "Yes" if new_is_prerelease else "No",
        Colors.YELLOW if new_is_prerelease else Colors.WHITE,
    )

    print()
    confirm: str = (
        input(f"{Colors.WHITE}Confirm release edit? (y/n): {Colors.RESET}")
        .strip()
        .lower()
    )

    if confirm != "y":
        print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
        return False

    # Build command
    cmd: List[str] = ["gh", "release", "edit", tag_name, "--title", new_title]
    cmd.extend(notes_cmd_args)

    if new_is_draft:
        cmd.append("--draft")
    else:
        cmd.append("--undraft")  # Remove draft status if not wanted

    if new_is_prerelease:
        cmd.append("--prerelease")
    else:
        cmd.append("--no-prerelease")  # Remove prerelease status if not wanted

    # Execute
    print()
    print(f"{Colors.CYAN}Editing release '{tag_name}'...{Colors.RESET}")

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print(
                f"{Colors.GREEN}✓ Release '{tag_name}' edited successfully.{Colors.RESET}"
            )
            return True
        else:
            print(f"{Colors.RED}✗ Error editing release '{tag_name}':{Colors.RESET}")
            print(f"{Colors.RED}{result.stderr}{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False
