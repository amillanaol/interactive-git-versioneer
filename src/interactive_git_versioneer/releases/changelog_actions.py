"""Acciones de alto nivel sobre changelogs (UI + file I/O)."""

import os
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

from ..core.git_ops import get_untagged_commits, parse_version
from ..core.ui import (
    Colors,
    clear_screen,
    print_header,
    wait_for_enter,
    wait_for_enter_or_skip,
)
from .changelog_gen import generate_changelog, summarize_changelog_with_ai
from .changelog_progress import (
    _clear_changelog_progress,
    _load_changelog_progress,
    _save_changelog_progress,
)


def get_latest_changelog_section(repo: Repo) -> str:
    """
    Reads the CHANGELOG.md file and returns the content of the latest version section.

    Args:
        repo: The Git repository object.

    Returns:
        The content of the latest changelog section, or a default message if not found.
    """
    repo_root = repo.working_dir
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")

    if not os.path.exists(changelog_path):
        return "No se encontró CHANGELOG.md"

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    latest_version_content = []
    in_latest_section = False

    for line in lines:
        if line.startswith("## ["):
            if in_latest_section:
                # We have reached the next version, so we stop.
                break
            in_latest_section = True
            latest_version_content.append(line)
        elif in_latest_section:
            latest_version_content.append(line)

    if not latest_version_content:
        return "No se encontraron entradas de changelog."

    # Remove empty lines from the beginning and end
    while latest_version_content and not latest_version_content[0].strip():
        latest_version_content.pop(0)
    while latest_version_content and not latest_version_content[-1].strip():
        latest_version_content.pop()

    return "\n".join(latest_version_content)


def show_generate_changelog(repo: Repo) -> None:
    """Interface for generating a changelog.

    Allows the user to select start and end tags (or HEAD) to generate
    and display a changelog for the specified range.

    Args:
        repo: The Git repository object.
    """
    clear_screen()
    print_header("GENERATE CHANGELOG")

    # Get available tags
    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: parse_version(t.name), reverse=True
    )

    if not tags:
        print(f"{Colors.YELLOW}No tags in the repository.{Colors.RESET}")
        print(
            f"{Colors.YELLOW}First create some tags using the Tag Management option.{Colors.RESET}"
        )
        return

    print(f"{Colors.WHITE}Available tags:{Colors.RESET}")
    for i, tag in enumerate(tags[:10], 1):
        print(f"  {i}. {tag.name}")
    print()

    # Select start tag
    print(
        f"{Colors.WHITE}Select the start tag (Enter for from the beginning):{Colors.RESET}"
    )
    from_choice: str = input(f"{Colors.WHITE}Tag number: {Colors.RESET}").strip()

    from_tag: Optional[str] = None
    if from_choice:
        try:
            idx: int = int(from_choice) - 1
            if 0 <= idx < len(tags):
                from_tag = tags[idx].name
        except ValueError:
            pass

    # Select end tag
    print(f"{Colors.WHITE}Select the end tag (Enter for HEAD):{Colors.RESET}")
    to_choice: str = input(f"{Colors.WHITE}Tag number: {Colors.RESET}").strip()

    to_tag: Optional[str] = None
    if to_choice:
        try:
            idx = int(to_choice) - 1
            if 0 <= idx < len(tags):
                to_tag = tags[idx].name
        except ValueError:
            pass

    # Generate and display changelog
    print()
    print_header("GENERATED CHANGELOG")

    range_desc: str = f"{from_tag or 'beginning'} → {to_tag or 'HEAD'}"
    print(f"{Colors.CYAN}Range: {range_desc}{Colors.RESET}")
    print()

    changelog: str = generate_changelog(repo, from_tag, to_tag)
    if changelog:
        print(changelog)
    else:
        print(f"{Colors.YELLOW}No commits in the specified range.{Colors.RESET}")
        print(
            f"{Colors.WHITE}This can happen if tags point to the same commit{Colors.RESET}"
        )
        print(
            f"{Colors.WHITE}or if there is no direct relationship between them.{Colors.RESET}"
        )


def action_generate_all_changelogs_with_ai(repo: Repo, rebuild: bool = False) -> None:
    """Generates and displays all changelogs between consecutive tags, from the beginning
    to the first tag, and from the last tag to HEAD, using AI to summarize.

    Continues from the last generated changelog unless rebuild=True.
    Ctrl+X skips the rest of pending changelogs.

    Args:
        repo: The Git repository object.
        rebuild: If True, regenerates all changelogs from scratch.
    """
    from ..core.logger import get_logger

    logger = get_logger()
    logger.function_enter("action_generate_all_changelogs_with_ai", rebuild=rebuild)

    clear_screen()
    if rebuild:
        print_header("REBUILD CHANGELOGS (with AI)")
        _clear_changelog_progress(repo)
    else:
        print_header("CONTINUE CHANGELOGS (with AI)")

    from ..config import get_config_value
    from ..tags.ai import auto_generate_all_with_ai

    # Check AI configuration
    if not get_config_value("OPENAI.key") or not get_config_value("OPENAI.baseURL"):
        print(f"{Colors.RED}Error: Incomplete AI configuration.{Colors.RESET}")
        print(f"{Colors.YELLOW}Configure with:{Colors.RESET}")
        print(f"  igv config set OPENAI.key <your-api-key>")
        print(f"  igv config set OPENAI.baseURL <url>")
        wait_for_enter()
        return

    # Check for untagged commits
    untagged_commits = get_untagged_commits(repo)
    if untagged_commits:
        logger.info(
            f"Se detectaron {len(untagged_commits)} commits sin etiquetar - Mostrando advertencia"
        )
        print()
        print(
            f"{Colors.RED}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}"
        )
        print(
            f"{Colors.RED}║  ⚠️  ADVERTENCIA: COMMITS SIN ETIQUETAR                      ║{Colors.RESET}"
        )
        print(
            f"{Colors.RED}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}"
        )
        print()
        print(
            f"{Colors.YELLOW}Se detectaron {len(untagged_commits)} commit(s) sin etiquetar:{Colors.RESET}"
        )
        print()
        for i, commit in enumerate(untagged_commits[:5], 1):
            print(
                f"  {Colors.CYAN}{commit.hash[:7]}{Colors.RESET} - {commit.message[:50]}..."
            )
        if len(untagged_commits) > 5:
            print(
                f"  {Colors.YELLOW}... y {len(untagged_commits) - 5} más{Colors.RESET}"
            )
        print()
        print(
            f"{Colors.YELLOW}Para generar changelogs completos, primero debe etiquetar estos commits.{Colors.RESET}"
        )
        print()
        print(f"{Colors.WHITE}Por favor, vaya a:{Colors.RESET}")
        print(
            f"{Colors.CYAN}  Menú Principal → 2. Tags → 8. Generar tags con IA{Colors.RESET}"
        )
        print()
        print(
            f"{Colors.WHITE}Una vez etiquetados, regrese aquí para generar los changelogs.{Colors.RESET}"
        )
        logger.info(
            "Operación cancelada - El usuario debe etiquetar commits primero desde el menú de Tags"
        )
        wait_for_enter()
        logger.function_exit("action_generate_all_changelogs_with_ai")
        return

    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: t.commit.committed_date
    )  # Sort chronologically

    if not tags:
        print(
            f"{Colors.YELLOW}No tags in the repository to generate changelogs.{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}Create some tags using the Tag Management option.{Colors.RESET}"
        )
        wait_for_enter()
        return

    # Load existing progress
    progress: Dict[str, str] = _load_changelog_progress(repo)

    # Load versions already in CHANGELOG.md file
    changelog_file_versions: List[str] = []
    last_changelog_version: Optional[str] = None
    repo_root: str = repo.working_dir
    changelog_path: str = os.path.join(repo_root, "CHANGELOG.md")
    if os.path.exists(changelog_path):
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            import re

            changelog_file_versions = re.findall(r"##\s*\[([^\]]+)\]", content)
            if changelog_file_versions:
                last_changelog_version = changelog_file_versions[
                    0
                ]  # Primera es la más reciente
        except Exception:
            pass

    total_ranges: int = len(tags)  # tags (start→first_tag + rangos entre tags)

    # Count how many are pending (not in changelog file and not in progress)
    pending_count: int = 0
    for t in tags:
        if t.name not in changelog_file_versions:
            range_key = f"{tags[tags.index(t) - 1].name if tags.index(t) > 0 else 'start'}→{t.name}"
            if range_key not in progress:
                pending_count += 1

    print(f"{Colors.WHITE}Total tags: {len(tags)}{Colors.RESET}")
    if changelog_file_versions:
        print(
            f"{Colors.WHITE}Versions in CHANGELOG.md: {len(changelog_file_versions)} (last: {last_changelog_version}){Colors.RESET}"
        )
    if progress:
        print(
            f"{Colors.WHITE}Versions in progress (provisional): {len(progress)}{Colors.RESET}"
        )
    if pending_count > 0:
        print(f"{Colors.YELLOW}Pending to generate: {pending_count}{Colors.RESET}")
    print()

    generated_count: int = 0
    skipped_count: int = 0
    user_skipped: bool = False  # Flag for when the user presses Ctrl+X
    auto_continue: bool = False  # Flag for when the user presses Ctrl+A (allow all)

    # Build list of ranges to process
    ranges_to_process: List[
        Tuple[Optional[str], str, Optional[str], Optional[str]]
    ] = []

    # First range: start → first tag
    first_tag_name: str = tags[0].name
    ranges_to_process.append(("start", first_tag_name, None, first_tag_name))

    # Intermediate ranges: tag[i] → tag[i+1]
    for i in range(len(tags) - 1):
        from_tag: str = tags[i].name
        to_tag: str = tags[i + 1].name
        ranges_to_process.append((from_tag, to_tag, from_tag, to_tag))

    # Nota: No se genera changelog para commits sin tag (HEAD)
    # El usuario debe etiquetar los commits primero en el menú de Tags

    # Process each range
    for display_from, display_to, git_from, git_to in ranges_to_process:
        range_key: str = f"{display_from}→{display_to}"

        # If the user skipped with Ctrl+X, do not process further
        if user_skipped:
            print(f"{Colors.YELLOW}⏭️  {range_key}: Skipped by user{Colors.RESET}")
            continue

        # If the target version is already in CHANGELOG.md file and not rebuild, skip
        if (
            display_to != "HEAD"
            and display_to in changelog_file_versions
            and not rebuild
        ):
            skipped_count += 1
            continue

        # If already in progress (provisional) and not rebuild, skip
        if range_key in progress and not rebuild:
            print(
                f"{Colors.GREEN}✓ {range_key}: In progress (provisional) - Skipping{Colors.RESET}"
            )
            skipped_count += 1
            continue

        # Generate changelog
        raw_changelog: str = generate_changelog(repo, from_tag=git_from, to_tag=git_to)

        if raw_changelog:
            print(f"{Colors.CYAN}=== CHANGELOG: {range_key} ==={Colors.RESET}")

            print(f"{Colors.YELLOW}Generating summary with AI...{Colors.RESET}")
            ai_changelog: str = summarize_changelog_with_ai(raw_changelog)
            print(ai_changelog)
            print("\n" + "=" * 50 + "\n")

            # Save progress
            progress[range_key] = ai_changelog
            _save_changelog_progress(repo, progress)
            generated_count += 1

            # Wait for user input (unless in auto mode)
            if not auto_continue:
                action: Optional[str] = wait_for_enter_or_skip()
                if action == "skip":
                    print(
                        f"{Colors.YELLOW}Skipping rest of changelogs...{Colors.RESET}"
                    )
                    user_skipped = True
                elif action == "all":
                    print(
                        f"{Colors.GREEN}Processing all remaining changelogs automatically...{Colors.RESET}"
                    )
                    auto_continue = True
                elif action == "quit":
                    print(f"{Colors.YELLOW}Exiting program...{Colors.RESET}")
                    sys.exit(0)
                elif action == "cancel":
                    print(f"{Colors.YELLOW}Canceled by user.{Colors.RESET}")
                    break
        else:
            print(f"{Colors.YELLOW}⏭️  {range_key}: No commits - Skipped{Colors.RESET}")
            progress[range_key] = "[No commits]"
            _save_changelog_progress(repo, progress)

    # Final summary
    print()
    print(f"{Colors.GREEN}═══ SUMMARY ═══{Colors.RESET}")
    print(f"{Colors.WHITE}Changelogs generated: {generated_count}{Colors.RESET}")
    print(
        f"{Colors.WHITE}Changelogs skipped (already existed): {skipped_count}{Colors.RESET}"
    )
    print(
        f"{Colors.WHITE}Total in progress (provisional): {len(progress)}{Colors.RESET}"
    )
    print()

    # Ask if user wants to save to CHANGELOG.md
    if len(progress) > 0:
        changelog_exists = os.path.exists(changelog_path)
        logger.info(
            f"Changelogs generados: {len(progress)} - Mostrando diálogo de guardado"
        )

        print(
            f"{Colors.YELLOW}¿Desea guardar los changelogs en el archivo CHANGELOG.md?{Colors.RESET}"
        )
        if changelog_exists:
            print(
                f"{Colors.YELLOW}⚠ El archivo CHANGELOG.md ya existe, será reemplazado.{Colors.RESET}"
            )
        print()

        logger.dialog_shown(
            "SAVE_CHANGELOG",
            f"¿Desea guardar los changelogs en el archivo CHANGELOG.md? (existe={changelog_exists})",
        )
        try:
            save_confirm = input(f"{Colors.WHITE}(s/n): {Colors.RESET}").strip().lower()
            logger.user_input("¿Desea guardar los changelogs?", save_confirm)
            if save_confirm == "s":
                logger.info(
                    "Usuario eligió guardar - Llamando a save_changelog_from_progress"
                )
                print()
                if save_changelog_from_progress(repo, changelog_path):
                    print()
                    print(
                        f"{Colors.GREEN}✓ Changelogs guardados en CHANGELOG.md{Colors.RESET}"
                    )
                    print(
                        f"{Colors.YELLOW}Recuerda hacer commit del archivo para persistir los cambios.{Colors.RESET}"
                    )
                    logger.info("Changelogs guardados exitosamente")
                else:
                    logger.error("Error al guardar changelogs")
            else:
                logger.info(f"Usuario eligió NO guardar (respuesta: '{save_confirm}')")
        except KeyboardInterrupt:
            print()
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            logger.info("Usuario canceló con KeyboardInterrupt en diálogo de guardado")

    wait_for_enter()
    logger.function_exit("action_generate_all_changelogs_with_ai")


def generate_all_missing_changelogs(repo: Repo) -> None:
    """Generates and displays all changelogs between consecutive tags, from the beginning
    to the first tag, and from the last tag to HEAD.
    """
    clear_screen()
    print_header("GENERATE ALL MISSING CHANGELOGS")

    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: t.commit.committed_date
    )  # Sort chronologically

    if not tags:
        print(
            f"{Colors.YELLOW}No tags in the repository to generate changelogs.{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}Create some tags using the Tag Management option.{Colors.RESET}"
        )
        wait_for_enter()
        return

    print(
        f"{Colors.WHITE}Generating changelogs for the repository history...{Colors.RESET}"
    )
    print()

    # Changelog from the beginning to the first tag
    first_tag_name: str = tags[0].name
    changelog: str = generate_changelog(repo, from_tag=None, to_tag=first_tag_name)
    if changelog:
        print(f"{Colors.CYAN}=== CHANGELOG: Start → {first_tag_name} ==={Colors.RESET}")
        print(changelog)
        print("\n" + "=" * 50 + "\n")
        wait_for_enter()
    else:
        print(
            f"{Colors.YELLOW}⏭️  Start → {first_tag_name}: No commits in this range - Skipped{Colors.RESET}"
        )

    # Changelogs between consecutive tags
    for i in range(len(tags) - 1):
        from_tag_name: str = tags[i].name
        to_tag_name: str = tags[i + 1].name
        changelog = generate_changelog(repo, from_tag=from_tag_name, to_tag=to_tag_name)
        if changelog:
            print(
                f"{Colors.CYAN}=== CHANGELOG: {from_tag_name} → {to_tag_name} ==={Colors.RESET}"
            )
            print(changelog)
            print("\n" + "=" * 50 + "\n")
            wait_for_enter()
        else:
            print(
                f"{Colors.YELLOW}⏭️  {from_tag_name} → {to_tag_name}: No commits in this range - Skipped{Colors.RESET}"
            )

    # Changelog from the last tag to HEAD
    last_tag_name: str = tags[-1].name
    changelog = generate_changelog(repo, from_tag=last_tag_name, to_tag=None)
    if changelog:
        print(f"{Colors.CYAN}=== CHANGELOG: {last_tag_name} → HEAD ==={Colors.RESET}")
        print(changelog)
        print("\n" + "=" * 50 + "\n")
    else:
        print(
            f"{Colors.YELLOW}⏭️  {last_tag_name} → HEAD: No pending commits{Colors.RESET}"
        )
    wait_for_enter()  # Pause after the last changelog


def save_changelog_to_file(repo: Repo) -> None:
    """Generates and saves the full changelog to a file.

    Args:
        repo: The Git repository object.
    """
    clear_screen()
    print_header("SAVE CHANGELOG TO FILE")

    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: parse_version(t.name), reverse=True
    )

    if not tags:
        print(
            f"{Colors.YELLOW}No tags in the repository to generate changelog.{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}First create some tags using the Tag Management option.{Colors.RESET}"
        )
        wait_for_enter()
        return

    # Get repository root path
    repo_root: str = repo.working_dir
    default_filename: str = "CHANGELOG.md"
    default_path: str = os.path.join(repo_root, default_filename)

    # Ask for filename
    print(f"{Colors.WHITE}Default file: {default_path}{Colors.RESET}")
    print()
    custom_name: str = input(
        f"{Colors.WHITE}Filename (Enter to use '{default_filename}'): {Colors.RESET}"
    ).strip()

    if custom_name:
        if not custom_name.endswith(".md"):
            custom_name += ".md"
        filepath: str = os.path.join(repo_root, custom_name)
    else:
        filepath = default_path

    # Check if file exists
    file_exists: bool = os.path.exists(filepath)
    if file_exists:
        print(f"{Colors.YELLOW}The file already exists: {filepath}{Colors.RESET}")
        overwrite: str = (
            input(f"{Colors.WHITE}Overwrite? (y/n): {Colors.RESET}").strip().lower()
        )
        if overwrite != "y":
            print(f"{Colors.YELLOW}Operation canceled.{Colors.RESET}")
            wait_for_enter()
            return

    print()
    print(f"{Colors.CYAN}Generating changelog...{Colors.RESET}")

    # Generate changelog content
    lines: List[str] = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append(
        f"*Automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    )
    lines.append("")

    # Tags sorted from most recent to oldest
    tags_by_version: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: parse_version(t.name), reverse=True
    )

    generated_count: int = 0
    skipped_count: int = 0

    for i, tag in enumerate(tags_by_version):
        tag_name: str = tag.name
        tag_date: str = datetime.fromtimestamp(tag.commit.committed_date).strftime(
            "%Y-%m-%d"
        )

        # Find the previous tag (by version)
        prev_tag: Optional[str] = None
        for j, t in enumerate(tags_by_version):
            if t.name == tag_name and j + 1 < len(tags_by_version):
                prev_tag = tags_by_version[j + 1].name
                break

        # Generate changelog for this tag
        changelog: str = generate_changelog(repo, prev_tag, tag_name)

        if changelog:
            lines.append(f"## [{tag_name}] - {tag_date}")
            lines.append("")
            lines.append(changelog)
            lines.append("")
            generated_count += 1
        else:
            skipped_count += 1

    # Add links section (optional, standard Keep a Changelog format)
    lines.append("---")
    lines.append("")
    lines.append(
        "*This changelog follows the format of [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)*"
    )

    # Save file
    try:
        content: str = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print()
        print(f"{Colors.GREEN}✓ Changelog saved successfully to:{Colors.RESET}")
        print(f"  {Colors.CYAN}{filepath}{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}Summary:{Colors.RESET}")
        print(f"  - Versions included: {generated_count}")
        if skipped_count > 0:
            print(f"  - Versions skipped (no commits): {skipped_count}")
        print()
        print(
            f"{Colors.YELLOW}Remember to commit the file to persist changes.{Colors.RESET}"
        )

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving file: {e}{Colors.RESET}")

    wait_for_enter()


def save_changelog_from_progress(repo: Repo, filepath: Optional[str] = None) -> bool:
    """Saves the AI-generated changelogs (from progress) to a file.

    Args:
        repo: The Git repository object.
        filepath: The path to the file (if None, uses CHANGELOG.md).

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    progress: Dict[str, str] = _load_changelog_progress(repo)

    if not progress:
        print(f"{Colors.YELLOW}No AI-generated changelogs to save.{Colors.RESET}")
        return False

    repo_root: str = repo.working_dir
    if filepath is None:
        filepath = os.path.join(repo_root, "CHANGELOG.md")

    # Generate changelog content
    lines: List[str] = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append(
        f"*Automatically generated with AI on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    )
    lines.append("")

    # Get tags sorted by version (most recent first)
    tags: List[git.TagReference] = sorted(
        repo.tags, key=lambda t: parse_version(t.name), reverse=True
    )

    # Build a map of tag names to their dates and versions for lookup
    tag_dates: Dict[str, str] = {}
    tag_versions: Dict[str, Tuple[int, int, int]] = {}
    for tag in tags:
        tag_dates[tag.name] = datetime.fromtimestamp(
            tag.commit.committed_date
        ).strftime("%Y-%m-%d")
        tag_versions[tag.name] = parse_version(tag.name)

    # Process all ranges from progress, sorted by version (most recent first)
    # Extract ranges and sort them by the "to" version
    range_items = []
    for range_key, content in progress.items():
        if content == "[No commits]":
            continue

        # Extract the "to" part from the range (e.g., "v1.0.0" from "start→v1.0.0")
        parts = range_key.split("→")
        if len(parts) != 2:
            continue

        to_part = parts[1]

        # Get version for sorting
        if to_part == "HEAD":
            sort_key = (999, 999, 999)  # HEAD comes first (most recent)
        else:
            sort_key = tag_versions.get(to_part, (0, 0, 0))

        range_items.append((sort_key, to_part, content))

    # Sort by version descending (most recent first)
    range_items.sort(key=lambda x: x[0], reverse=True)

    for sort_key, to_part, content in range_items:
        # Get the date for this version
        if to_part == "HEAD":
            # For HEAD, use current date
            version_date = datetime.now().strftime("%Y-%m-%d")
            version_label = "Unreleased"
        else:
            # For tags, use the tag date
            version_date = tag_dates.get(to_part, datetime.now().strftime("%Y-%m-%d"))
            version_label = to_part

        lines.append(f"## [{version_label}] - {version_date}")
        lines.append("")
        lines.append(content)
        lines.append("")

    # Add links section
    lines.append("---")
    lines.append("")
    lines.append(
        "*This changelog was generated with AI and follows the format of [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)*"
    )

    # Save file
    try:
        content_str: str = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_str)

        print()
        print(f"{Colors.GREEN}✓ Changelog saved successfully to:{Colors.RESET}")
        print(f"  {Colors.CYAN}{filepath}{Colors.RESET}")
        return True

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving file: {e}{Colors.RESET}")
        return False


def view_local_changelog(repo: Repo) -> None:
    """Displays the content of the local changelog file.

    Args:
        repo: The Git repository object.
    """
    clear_screen()
    print_header("VIEW LOCAL CHANGELOG")

    repo_root: str = repo.working_dir

    # Search for changelog files in the repository
    changelog_files: List[str] = []
    for filename in os.listdir(repo_root):
        if filename.lower().startswith("changelog") and filename.endswith(".md"):
            changelog_files.append(filename)

    if not changelog_files:
        print(
            f"{Colors.YELLOW}No changelog files found in the repository.{Colors.RESET}"
        )
        print(
            f"{Colors.WHITE}Use the 'Save changelog to file' option to create one.{Colors.RESET}"
        )
        wait_for_enter()
        return

    # If there are several, show list to select
    if len(changelog_files) == 1:
        selected_file: str = changelog_files[0]
    else:
        print(f"{Colors.WHITE}Changelog files found:{Colors.RESET}")
        print()
        for i, filename in enumerate(changelog_files, 1):
            filepath: str = os.path.join(repo_root, filename)
            file_size: int = os.path.getsize(filepath)
            mod_time: str = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime(
                "%Y-%m-%d %H:%M"
            )
            print(
                f"  {Colors.CYAN}{i}.{Colors.RESET} {filename} ({file_size} bytes, modified: {mod_time})"
            )
        print()

        try:
            choice: str = input(
                f"{Colors.WHITE}Select file (1-{len(changelog_files)}): {Colors.RESET}"
            ).strip()
            idx: int = int(choice) - 1
            if 0 <= idx < len(changelog_files):
                selected_file = changelog_files[idx]
            else:
                print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
                wait_for_enter()
                return
        except ValueError:
            print(f"{Colors.RED}Invalid input.{Colors.RESET}")
            wait_for_enter()
            return

    filepath = os.path.join(repo_root, selected_file)

    # Show file information
    print()
    file_size = os.path.getsize(filepath)
    mod_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime(
        "%Y-%m-%d %H:%M"
    )
    print(f"{Colors.CYAN}File: {selected_file}{Colors.RESET}")
    print(
        f"{Colors.WHITE}Size: {file_size} bytes | Last modified: {mod_time}{Colors.RESET}"
    )
    print()
    print("=" * 60)
    print()

    # Read and display content with pagination
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content: str = f.read()

        lines: List[str] = content.split("\n")
        page_size: int = 25
        total_lines: int = len(lines)
        total_pages: int = (total_lines + page_size - 1) // page_size
        current_page: int = 0

        while True:
            clear_screen()
            print_header("VIEW LOCAL CHANGELOG")
            print(f"{Colors.CYAN}File: {selected_file}{Colors.RESET}")
            print(
                f"{Colors.WHITE}Page {current_page + 1}/{total_pages} | Total: {total_lines} lines{Colors.RESET}"
            )
            print()
            print("=" * 60)
            print()

            # Display current page
            start_line: int = current_page * page_size
            end_line: int = min(start_line + page_size, total_lines)
            for line in lines[start_line:end_line]:
                print(line)

            print()
            print("=" * 60)
            print()

            # Navigation options
            nav_options: List[str] = []
            if current_page > 0:
                nav_options.append("[p] Previous")
            if current_page < total_pages - 1:
                nav_options.append("[n] Next")
            nav_options.append("[0] Back")

            print(f"{Colors.WHITE}{' | '.join(nav_options)}{Colors.RESET}")

            try:
                choice = input(f"{Colors.WHITE}Option: {Colors.RESET}").strip().lower()
            except KeyboardInterrupt:
                break

            if choice == "0" or choice == "q" or choice == "-back-":
                break
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
            elif choice == "":  # Enter advances
                if current_page < total_pages - 1:
                    current_page += 1

    except Exception as e:
        print(f"{Colors.RED}Error reading file: {e}{Colors.RESET}")
        wait_for_enter()


def edit_changelog_file(repo: git.Repo) -> None:
    """Abre el archivo changelog en el editor del sistema para modificarlo.

    Args:
        repo: Repositorio Git
    """
    clear_screen()
    print_header("MODIFICAR CHANGELOG")

    repo_root = repo.working_dir

    # Buscar archivos changelog en el repositorio
    changelog_files = []
    for filename in os.listdir(repo_root):
        if filename.lower().startswith("changelog") and filename.endswith(".md"):
            changelog_files.append(filename)

    if not changelog_files:
        print(
            f"{Colors.YELLOW}No se encontraron archivos changelog en el repositorio.{Colors.RESET}"
        )
        print(
            f"{Colors.WHITE}Usa la opción 'Generar changelog' para crear uno primero.{Colors.RESET}"
        )
        wait_for_enter()
        return

    # Si hay varios, mostrar lista para seleccionar
    if len(changelog_files) == 1:
        selected_file = changelog_files[0]
    else:
        print(f"{Colors.WHITE}Archivos changelog encontrados:{Colors.RESET}")
        print()
        for i, filename in enumerate(changelog_files, 1):
            filepath = os.path.join(repo_root, filename)
            file_size = os.path.getsize(filepath)
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime(
                "%Y-%m-%d %H:%M"
            )
            print(
                f"  {Colors.CYAN}{i}.{Colors.RESET} {filename} ({file_size} bytes, modificado: {mod_time})"
            )
        print()

        try:
            choice = input(
                f"{Colors.WHITE}Seleccione archivo (1-{len(changelog_files)}): {Colors.RESET}"
            ).strip()
            idx = int(choice) - 1
            if 0 <= idx < len(changelog_files):
                selected_file = changelog_files[idx]
            else:
                print(f"{Colors.RED}Selección inválida.{Colors.RESET}")
                wait_for_enter()
                return
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.YELLOW}Operación cancelada.{Colors.RESET}")
            wait_for_enter()
            return

    filepath = os.path.join(repo_root, selected_file)

    print()
    print(f"{Colors.CYAN}Abriendo {selected_file} en el editor...{Colors.RESET}")
    print()

    try:
        # Determinar el editor según el sistema operativo
        if sys.platform == "win32":
            # En Windows, usar el comando 'start' para abrir con el programa predeterminado
            os.startfile(filepath)
        elif sys.platform == "darwin":
            # En macOS, usar 'open'
            import subprocess

            subprocess.run(["open", filepath], check=False)
        else:
            # En Linux, intentar con el editor definido en $EDITOR o usar nano/vim
            import subprocess

            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, filepath], check=False)

        print(f"{Colors.GREEN}✓ Editor abierto.{Colors.RESET}")
        print(
            f"{Colors.WHITE}Guarda los cambios en el editor cuando termines.{Colors.RESET}"
        )

    except Exception as e:
        print(f"{Colors.RED}Error al abrir editor: {e}{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}Puedes editar el archivo manualmente en:{Colors.RESET}")
        print(f"  {Colors.CYAN}{filepath}{Colors.RESET}")

    wait_for_enter()
