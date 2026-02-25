"""
Core module for interactive-git-versioneer.

Re-exports shared components: AI integration, Git operations, data models, and UI utilities.
"""

from .ai import determine_version_type, generate_tag_message, get_ai_service
from .git_ops import (
    get_commit_diff,
    get_git_repo,
    get_last_tag,
    get_last_version_number,
    get_next_version,
    get_untagged_commits,
    parse_version,
)
from .logger import DebugLogger, get_logger, is_logging_enabled
from .models import Commit
from .ui import (
    Colors,
    Menu,
    MenuItem,
    clear_screen,
    get_menu_input,
    print_header,
    print_info,
    print_subheader,
    wait_for_enter,
    wait_for_enter_or_skip,
)

__all__ = [
    # AI
    "get_ai_service",
    "generate_tag_message",
    "determine_version_type",
    # Git operations
    "get_git_repo",
    "get_last_tag",
    "get_last_version_number",
    "get_next_version",
    "get_untagged_commits",
    "get_commit_diff",
    "parse_version",
    # Logger
    "DebugLogger",
    "get_logger",
    "is_logging_enabled",
    # Models
    "Commit",
    # UI
    "Colors",
    "Menu",
    "MenuItem",
    "clear_screen",
    "print_header",
    "print_subheader",
    "print_info",
    "wait_for_enter",
    "wait_for_enter_or_skip",
    "get_menu_input",
]
