"""
Pure Git operations for interactive-git-versioneer.

Contains low-level functions for interacting with Git repositories.
"""

import re
import sys
from typing import List, Optional, Tuple

try:
    import git
    from git import Commit as GitCommit
    from git import Repo, Tag
except ImportError:
    print("Error: GitPython is not installed")
    print("Install it with: pip install GitPython")
    sys.exit(1)

from .models import Commit
from .ui import Colors


def get_git_repo() -> Repo:
    """Retrieves the current Git repository.

    Returns:
        Repo: The Git repository object.

    Raises:
        SystemExit: If the current directory is not a valid Git repository.
    """
    try:
        return Repo(".")
    except git.InvalidGitRepositoryError:
        print(f"{Colors.RED}Error: Not a valid Git repository{Colors.RESET}")
        sys.exit(1)


def parse_version(tag: str) -> Tuple[int, int, int]:
    """Parses a version tag into a (major, minor, patch) tuple.

    Args:
        tag (str): The version tag string (e.g., "v1.2.3", "1.2.3").

    Returns:
        Tuple[int, int, int]: A tuple representing the major, minor, and patch
            version numbers. Returns (0, 0, 0) if parsing fails.
    """
    version_str: str = re.sub(r"^v", "", tag)

    try:
        parts: List[str] = version_str.split(".")
        if len(parts) >= 3:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass

    return (0, 0, 0)


def get_last_tag(repo: Repo) -> Optional[str]:
    """Retrieves the most recent tag from the repository.

    Args:
        repo (Repo): The Git repository object.

    Returns:
        Optional[str]: The name of the most recent tag, or None if no tags are found.
    """
    try:
        tags: List[git.Tag] = sorted(
            repo.tags, key=lambda t: parse_version(t.name), reverse=True
        )
        return tags[0].name if tags else None
    except Exception:
        return None


def get_last_version_number(repo: Repo) -> Tuple[int, int, int]:
    """Retrieves the most recent version number as a (major, minor, patch) tuple.

    Args:
        repo: The Git repository object.

    Returns:
        Tuple[int, int, int]: A tuple representing the major, minor, and patch
            version numbers. Returns (0, 0, 0) if no tags are found.
    """
    last_tag: Optional[str] = get_last_tag(repo)

    if not last_tag:
        return (0, 0, 0)

    return parse_version(last_tag)


def get_next_version(repo: Repo, version_type: str) -> str:
    """Calculates the next version based on the type of change.

    Args:
        repo (Repo): The Git repository object.
        version_type (str): The type of version increment ("major", "minor", or "patch").

    Returns:
        str: The calculated next version string (e.g., "v1.2.3").

    Raises:
        ValueError: If an invalid version type is provided.
    """
    if version_type not in ("major", "minor", "patch"):
        raise ValueError(f"Invalid version type: {version_type}")

    major: int
    minor: int
    patch: int
    major, minor, patch = get_last_version_number(repo)

    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1

    return f"v{major}.{minor}.{patch}"


def get_untagged_commits(repo: Repo) -> List[Commit]:
    """Retrieves commits made after the last tag.

    Args:
        repo (Repo): The Git repository object.

    Returns:
        List[Commit]: A list of Commit objects representing the untagged commits,
                      ordered from oldest to newest.
    """
    commits: List[Commit] = []
    last_tag: Optional[str] = get_last_tag(repo)

    try:
        if last_tag:
            git_commits = repo.iter_commits(f"{last_tag}..HEAD")
        else:
            git_commits = repo.iter_commits("HEAD")

        for git_commit in git_commits:
            commits.append(
                Commit(
                    hash=git_commit.hexsha[:40],
                    message=git_commit.message.split("\n")[0],
                    author=git_commit.author.name,
                    date=git_commit.committed_datetime.strftime("%Y-%m-%d"),
                    version_type=None,
                    custom_message=None,
                    processed=False,
                )
            )
        # Reverse the list so commits are from oldest to newest
        commits.reverse()
    except Exception as e:
        print(f"{Colors.RED}Error getting commits: {e}{Colors.RESET}")

    return commits


def get_commit_diff(repo: Repo, commit_hash: str) -> str:
    """Retrieves the diff of a specific commit.

    Args:
        repo (Repo): The Git repository object.
        commit_hash (str): The hash of the commit.

    Returns:
        str: The diff of the commit.
    """
    try:
        commit: git.Commit = repo.commit(commit_hash)
        if commit.parents:
            diff: str = repo.git.diff(commit.parents[0].hexsha, commit_hash)
        else:
            diff = repo.git.show(commit_hash, format="", name_only=False)
        return diff
    except Exception as e:
        return f"Error getting diff: {e}"
