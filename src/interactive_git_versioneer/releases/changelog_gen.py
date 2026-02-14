"""Lógica de generación de changelogs (commits → texto)."""

import sys
from typing import Any, List, Optional

try:
    import git
    from git import Commit, Repo
except ImportError:
    print("Error: GitPython is not installed")
    print("Install it with: pip install GitPython")
    sys.exit(1)

from ..core.git_ops import parse_version


def _get_commits_between_tags(repo: Repo, from_tag: str, to_tag: str) -> List[Commit]:
    """Retrieves commits between two tags using multiple strategies.

    Args:
        repo: The Git repository object.
        from_tag: The starting tag.
        to_tag: The ending tag.

    Returns:
        List[Commit]: A list of Commit objects between the tags.
    """
    commits: List[Commit] = []

    # Strategy 1: Standard from_tag..to_tag range
    try:
        commits = list(repo.iter_commits(f"{from_tag}..{to_tag}"))
        if commits:
            return commits
    except Exception:
        pass

    # Strategy 2: Get commits by date between the two tags
    try:
        from_commit: git.TagReference.commit = repo.tags[from_tag].commit
        to_commit: git.TagReference.commit = repo.tags[to_tag].commit

        # If tags point to the same commit, there's no changelog
        if from_commit.hexsha == to_commit.hexsha:
            return []

        from_date = from_commit.committed_datetime
        to_date = to_commit.committed_datetime

        # Get all reachable commits from to_tag
        all_commits: List[Commit] = list(repo.iter_commits(to_tag))

        # Filter by date: commits after from_tag and up to to_tag (inclusive)
        for commit in all_commits:
            if from_date < commit.committed_datetime <= to_date:
                commits.append(commit)
            elif commit.committed_datetime <= from_date:
                # We've passed the from_tag date, can stop
                break

        if commits:
            return commits
    except Exception:
        pass

    # Strategy 3: Find the closest previous tag to to_tag
    try:
        # Get all tags sorted by version
        all_tags: List[git.TagReference] = sorted(
            repo.tags, key=lambda t: parse_version(t.name)
        )
        tag_names: List[str] = [t.name for t in all_tags]

        if to_tag in tag_names:
            to_idx: int = tag_names.index(to_tag)
            if to_idx > 0:
                # Use the immediately preceding tag by version
                prev_tag: str = tag_names[to_idx - 1]
                commits = list(repo.iter_commits(f"{prev_tag}..{to_tag}"))
                if commits:
                    return commits
    except Exception:
        pass

    # Strategy 4: Get only the to_tag commit if nothing else worked
    try:
        to_commit = repo.tags[to_tag].commit
        # At least return the target tag's commit
        return [to_commit]
    except Exception:
        pass

    return commits


def _get_commits_until_tag(repo: Repo, to_tag: str) -> List[Commit]:
    """Retrieves all commits up to a specific tag (for the first release).

    Args:
        repo: The Git repository object.
        to_tag: The target tag.

    Returns:
        List[Commit]: A list of Commit objects up to the tag.
    """
    commits: List[Commit] = []

    # Strategy 1: Get all reachable commits from the tag
    try:
        commits = list(repo.iter_commits(to_tag))
        if commits:
            # See if there's a previous tag to limit
            other_tags: List[git.TagReference] = [
                t for t in repo.tags if t.name != to_tag
            ]
            if other_tags:
                # Sort by version and get the closest lower one
                sorted_tags: List[git.TagReference] = sorted(
                    other_tags, key=lambda t: parse_version(t.name), reverse=True
                )
                for prev_tag in sorted_tags:
                    if parse_version(prev_tag.name) < parse_version(to_tag):
                        # Use this tag as the lower limit
                        commits = list(repo.iter_commits(f"{prev_tag.name}..{to_tag}"))
                        break
            return commits
    except Exception:
        pass

    # Strategy 2: Only the commit of the tag
    try:
        to_commit: git.TagReference.commit = repo.tags[to_tag].commit
        return [to_commit]
    except Exception:
        pass

    return commits


def generate_changelog(
    repo: Repo, from_tag: Optional[str] = None, to_tag: Optional[str] = None
) -> str:
    """Generates a changelog between two versions.

    Args:
        repo: The Git repository object.
        from_tag: The starting tag (None = from the beginning of history).
        to_tag: The ending tag (None = HEAD).

    Returns:
        str: The formatted changelog.
    """
    try:
        # Determine commit range
        commits: List[Commit] = []

        if from_tag and to_tag:
            # Range between two tags - try multiple strategies
            commits = _get_commits_between_tags(repo, from_tag, to_tag)
        elif from_tag:
            # From tag to HEAD
            commit_range: str = f"{from_tag}..HEAD"
            commits = list(repo.iter_commits(commit_range))
        elif to_tag:
            # First release: get all commits up to this tag
            commits = _get_commits_until_tag(repo, to_tag)
        else:
            # No tag specified, use HEAD
            commits = list(repo.iter_commits("HEAD"))

        if not commits:
            return ""  # Return empty to indicate no changes

        # Categorize commits by type
        features: List[str] = []
        fixes: List[str] = []
        docs: List[str] = []
        other: List[str] = []

        for commit in commits:
            msg: str = commit.message.split("\n")[0]

            if msg.startswith("feat"):
                features.append(msg)
            elif msg.startswith("fix"):
                fixes.append(msg)
            elif msg.startswith("docs"):
                docs.append(msg)
            else:
                other.append(msg)

        # Generate changelog
        lines: List[str] = []

        if features:
            lines.append("### ✨ New Features")
            for msg in features:
                lines.append(f"- {msg}")
            lines.append("")

        if fixes:
            lines.append("### 🐛 Bug Fixes")
            for msg in fixes:
                lines.append(f"- {msg}")
            lines.append("")

        if docs:
            lines.append("### 📚 Documentation")
            for msg in docs:
                lines.append(f"- {msg}")
            lines.append("")

        if other:
            lines.append("### 🔧 Other Changes")
            for msg in other:
                lines.append(f"- {msg}")
            lines.append("")

        return "\n".join(lines) if lines else "No changes recorded."

    except Exception as e:
        return f"Error generating changelog: {e}"


def generate_changelog_from_tag_message(repo: Repo, tag_name: str) -> str:
    """Generates a changelog entry from a Git tag's message.

    This is more efficient than using AI to summarize commits, as tag messages
    already contain a human-readable description of changes.

    Args:
        repo: The Git repository object.
        tag_name: The tag name to extract the message from.

    Returns:
        str: The formatted changelog entry based on the tag message.
    """
    try:
        # Get the tag object
        tag = repo.tags[tag_name]

        # Get the tag message (annotation)
        # Annotated tags have a message attribute
        if hasattr(tag.tag, "message"):
            message = tag.tag.message.strip()
        else:
            # Lightweight tags don't have annotations, use commit message
            message = tag.commit.message.strip()

        # Clean up the message:
        # - Remove the tag name if it appears at the start
        # - Skip "Tagger:" metadata lines
        # - Split into lines
        lines = message.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip empty lines, tag name, and metadata
            if (
                not line
                or line == tag_name
                or line.startswith("tag ")
                or line.startswith("Tagger:")
                or line.startswith("Date:")
            ):
                continue
            cleaned_lines.append(line)

        if not cleaned_lines:
            return "No description available."

        # Format as changelog entry
        # If there's only one line, use it as-is
        if len(cleaned_lines) == 1:
            return cleaned_lines[0]

        # If there are multiple lines, format them
        result_lines = []
        for i, line in enumerate(cleaned_lines):
            # If line starts with a conventional commit prefix, format as bullet
            if any(
                line.startswith(prefix)
                for prefix in [
                    "feat:",
                    "fix:",
                    "docs:",
                    "test:",
                    "refactor:",
                    "chore:",
                    "style:",
                    "perf:",
                ]
            ):
                result_lines.append(f"- {line}")
            elif i == 0:
                # First line is the main description
                result_lines.append(line)
            else:
                # Subsequent lines are additional details
                result_lines.append(f"- {line}")

        return "\n".join(result_lines) if result_lines else cleaned_lines[0]

    except Exception as e:
        return f"Error extracting tag message: {e}"


def summarize_changelog_with_ai(raw_changelog_text: str, locale: str = "es") -> str:
    """Summarizes a changelog using the AI API.

    Args:
        raw_changelog_text: The changelog text to summarize.
        locale: The language for the summary (es, en).

    Returns:
        str: The AI-summarized changelog.
    """
    from ..config import get_config_value
    from ..core.ai import get_openai_client

    try:
        client: Any = get_openai_client()
        model: str = get_config_value("OPENAI.model") or "llama-3.3-70b-versatile"

        # Limit input to avoid excessive tokens
        changelog_truncated: str = (
            raw_changelog_text[:4000]
            if len(raw_changelog_text) > 4000
            else raw_changelog_text
        )

        prompt: str = f"""Summarize the following git changelog entries into a concise, human-readable changelog.
        Focus on key features, bug fixes, and significant changes. Group similar items.
        Exclude minor refactorings or documentation updates unless they are significant.
        Use imperative mood and clear language.
        Language: {locale}

        Raw Changelog Entries:
        ```
        {changelog_truncated}
        ```

        Output only the summarized changelog. Do not include any conversational text, introductions, or conclusions.
        """

        response: Any = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes git changelog entries concisely.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.5,
            stop=["\n\n\n", "```"],
        )

        result: str = response.choices[0].message.content.strip()
        return result

    except ImportError as e:
        return f"Error: The 'openai' library is not installed: {e}"
    except ValueError as e:
        return f"AI configuration error: {e}. Make sure OPENAI.key and OPENAI.baseURL are configured."
    except Exception as e:
        error_str: str = str(e).lower()
        if (
            "401" in error_str
            or "invalid_api_key" in error_str
            or "invalid api key" in error_str
        ):
            return (
                "Error: Invalid or unconfigured API Key.\n"
                "Configure your API key with:\n"
                '  igv config set OPENAI.key "your_api_key"\n'
                '  igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"\n'
                '  igv config set OPENAI.model "llama-3.3-70b-versatile"\n'
                "Get your API key at: https://console.groq.com/keys"
            )
        return f"Error summarizing changelog with AI: {e}"
