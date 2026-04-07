"""Persistencia del progreso de changelogs generados (JSON en .git/)."""

import json
from pathlib import Path
from typing import Dict

from git import Repo

from ..core.ui import Colors


def _get_changelog_progress_path(repo: Repo) -> Path:
    """Gets the path to the changelog progress file.

    Args:
        repo: The Git repository object.

    Returns:
        Path: The path to the progress file.
    """
    # Use the repo's .git directory to store progress
    git_dir: Path = Path(repo.git_dir)
    return git_dir / "igv_changelog_progress.json"


def _load_changelog_progress(repo: Repo) -> Dict[str, str]:
    """Loads the generated changelog progress.

    Args:
        repo: The Git repository object.

    Returns:
        Dict: A dictionary with generated changelogs in the format {range: changelog}.
    """
    progress_path: Path = _get_changelog_progress_path(repo)
    if progress_path.exists():
        try:
            with open(progress_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_changelog_progress(repo: Repo, progress: Dict[str, str]) -> None:
    """Saves the generated changelog progress.

    Args:
        repo: The Git repository object.
        progress: A dictionary with generated changelogs.
    """
    progress_path: Path = _get_changelog_progress_path(repo)
    try:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"{Colors.YELLOW}Warning: Could not save progress: {e}{Colors.RESET}")


def _clear_changelog_progress(repo: Repo) -> None:
    """Deletes the changelog progress file.

    Args:
        repo: The Git repository object.
    """
    progress_path: Path = _get_changelog_progress_path(repo)
    if progress_path.exists():
        try:
            progress_path.unlink()
        except IOError:
            pass
