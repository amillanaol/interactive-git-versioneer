"""
Main entry point for interactive-git-versioneer (igv).

CLI with subcommands for configuration and version tagging.
"""

import argparse
import json
import sys
from typing import Optional

from git import Repo

from . import __app_name__, __version__
from .config import (
    get_config_path,
    get_config_value,
    load_config,
    set_config_value,
)
from .core.git_ops import get_last_tag
from .tags import clean_all_tags, get_git_repo


def cmd_config_set(args: argparse.Namespace) -> int:
    """Handles the 'config set' command, saving a configuration key-value pair.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes:
                - key (str): The configuration key to set.
                - value (str): The value to assign to the key.

    Returns:
        int: An exit code (0 for success).
    """
    set_config_value(str(args.key), str(args.value))
    print(f"Configuration saved: {args.key} = {args.value}")
    return 0


def cmd_config_get(args: argparse.Namespace) -> int:
    """Handles the 'config get' command, retrieving a configuration value.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes:
                - key (str): The configuration key to retrieve.

    Returns:
        int: An exit code (0 for success, 1 if the key is not found).
    """
    value: Optional[str] = get_config_value(str(args.key))
    if value is None:
        print(f"Key not found: {args.key}")
        return 1
    print(value)
    return 0


def cmd_config_list(args: argparse.Namespace) -> int:
    """Handles the 'config list' command, displaying all current configurations.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              This function does not use any specific attributes from `args`.

    Returns:
        int: An exit code (0 for success).
    """
    config: dict = load_config()
    if not config:
        print(f"No configuration found. File: {get_config_path()}")
        return 0

    print(json.dumps(config, indent=2, ensure_ascii=False))
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    """Handles the 'tag' command, executing either the interactive tagging menu or automatic tagging.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes:
                - auto (bool): If True, runs the automatic tagger.
                - dry_run (bool): If True, performs a dry run without actual changes.
                - push (bool): If True, pushes tags to the remote repository after creation.
                - type (str): The version type for automatic tagging (e.g., 'major', 'minor', 'patch', 'auto').

    Returns:
        int: An exit code (0 for success).
    """
    # Import here to avoid circular dependency and lazy loading
    from .tags import run_auto_tagger, run_interactive_tagger

    if args.auto:
        return run_auto_tagger(
            dry_run=args.dry_run, push=args.push, version_type=str(args.type)
        )

    return run_interactive_tagger(dry_run=args.dry_run, push=args.push)


def cmd_clean_tags(args: argparse.Namespace) -> int:
    """Handles the 'clean-tags' command, which removes Git tags.

    This is a destructive and irreversible operation.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes:
                - local_only (bool): If True, only local tags are deleted; otherwise, remote tags are also deleted.

    Returns:
        int: An exit code (0 for success, 1 for failure).
    """
    repo: Repo = get_git_repo()
    success: bool = clean_all_tags(repo, include_remote=not args.local_only)

    if success:
        return 0
    return 1


def main() -> int:
    """Main entry point for the Interactive Git Versioneer CLI.

    This function sets up the argument parser, defines subcommands for configuration,
    tagging, and tag cleaning, and dispatches the execution to the appropriate handler
    based on the parsed command-line arguments.

    Returns:
        int: The exit code of the executed command handler.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=__app_name__,
        description="Interactive Git Versioneer - Version tag manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
AI Configuration (Groq/OpenAI):
  python -m interactive_git_versioneer.main config set OPENAI.key "gsk_your_api_key"
  python -m interactive_git_versioneer.main config set OPENAI.baseURL "https://api.groq.com/openai/v1"
  python -m interactive_git_versioneer.main config set OPENAI.model "llama-3.3-70b-versatile"

Available models on Groq:
  https://console.groq.com/docs/models

Example models:
  - llama-3.3-70b-versatile (default)
  - qwen/qwen3-32b
  - mixtral
""",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and repository info",
    )

    subparsers: argparse._SubParsersAction = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="<command>",
    )

    # Command: config
    config_parser: argparse.ArgumentParser = subparsers.add_parser(
        "config",
        help="Manage configuration",
    )
    config_subparsers: argparse._SubParsersAction = config_parser.add_subparsers(
        title="subcommands",
        dest="config_command",
        metavar="<subcommand>",
    )

    # config set
    config_set_parser: argparse.ArgumentParser = config_subparsers.add_parser(
        "set",
        help="Set a configuration value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available keys:
  OPENAI.key      - Groq/OpenAI API key
  OPENAI.baseURL  - API base URL (e.g., https://api.groq.com/openai/v1)
  OPENAI.model    - Model to use (e.g., llama-3.3-70b-versatile)

Available models: https://console.groq.com/docs/models
""",
    )
    config_set_parser.add_argument(
        "key",
        help="Key to set (e.g., OPENAI.key, OPENAI.model)",
    )
    config_set_parser.add_argument(
        "value",
        help="Value to assign",
    )
    config_set_parser.set_defaults(func=cmd_config_set)

    # config get
    config_get_parser: argparse.ArgumentParser = config_subparsers.add_parser(
        "get",
        help="Get a configuration value",
    )
    config_get_parser.add_argument(
        "key",
        help="Key to get (e.g., OPENAI.key)",
    )
    config_get_parser.set_defaults(func=cmd_config_get)

    # config list
    config_list_parser: argparse.ArgumentParser = config_subparsers.add_parser(
        "list",
        help="List all configuration",
    )
    config_list_parser.set_defaults(func=cmd_config_list)

    # Command: tag
    tag_parser: argparse.ArgumentParser = subparsers.add_parser(
        "tag",
        help="Execute the interactive tagging menu",
    )
    tag_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode. Shows commands without executing them.",
    )
    tag_parser.add_argument(
        "--push",
        action="store_true",
        help="Pushes tags to the remote repository after creation.",
    )
    tag_parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatic mode for CI/CD. No interactive menu, uses AI to generate tags.",
    )
    tag_parser.add_argument(
        "--type",
        choices=["major", "minor", "patch", "auto"],
        default="auto",
        help="Version type for --auto. 'auto' lets AI decide. (default: auto)",
    )
    tag_parser.set_defaults(func=cmd_tag)

    # Command: clean-tags
    clean_tags_parser: argparse.ArgumentParser = subparsers.add_parser(
        "clean-tags",
        help="Deletes ALL local and remote tags (destructive operation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This operation is DESTRUCTIVE and IRREVERSIBLE.

Removes all tags from the repository to re-do versioning from scratch.
Requires multiple confirmations before execution.

Examples:
  igv clean-tags              # Deletes local and remote tags
  igv clean-tags --local-only # Only deletes local tags
""",
    )
    clean_tags_parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only deletes local tags, not remote ones.",
    )
    clean_tags_parser.set_defaults(func=cmd_clean_tags)

    # Parse arguments
    args: argparse.Namespace = parser.parse_args()

    # Handle -v/--version flag
    if args.version:
        print(f"{__app_name__} v{__version__}")
        return 0

    # If no command is provided, show help or run tag by default
    if args.command is None:
        # By default, run the interactive menu
        args.dry_run = False
        args.push = False
        args.auto = False
        args.type = "auto"
        return cmd_tag(args)

    # If it's a config command without a subcommand, show help
    if args.command == "config" and args.config_command is None:
        config_parser.print_help()
        return 1

    # Execute the command
    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
