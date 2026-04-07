"""Autenticación con GitHub CLI."""

import subprocess
from typing import Tuple

from ..core.ui import Colors, clear_screen, print_header


def check_gh_cli() -> bool:
    """Checks if GitHub CLI (gh) is installed.

    Returns:
        bool: True if gh is available, False otherwise.
    """
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_gh_auth() -> Tuple[bool, str]:
    """Checks if the user is authenticated with GitHub CLI.

    Returns:
        Tuple[bool, str]: A tuple where the first element is True if authenticated,
            False otherwise, and the second element is the username or an error message.
    """
    if not check_gh_cli():
        return False, "GitHub CLI is not installed"

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            # Extract username if possible
            if "Logged in to" in result.stdout or "logged in" in result.stdout.lower():
                # Try to get the user
                user_result: subprocess.CompletedProcess = subprocess.run(
                    ["gh", "api", "user", "--jq", ".login"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if user_result.returncode == 0:
                    username: str = user_result.stdout.strip()
                    return True, username
                return True, "Authenticated"
            return True, "Authenticated"
        else:
            if "not authenticated" in result.stderr.lower():
                return False, "Not authenticated. Run: gh auth login"
            return False, result.stderr or "Authentication error"
    except Exception as e:
        return False, str(e)


def auth_github_cli() -> bool:
    """Opens the authentication process with GitHub CLI.

    Initiates the `gh auth login` command to authenticate the user with GitHub.

    Returns:
        bool: True if authentication is completed successfully, False otherwise.
    """
    clear_screen()
    print_header("AUTHENTICATE WITH GITHUB")

    if not check_gh_cli():
        print()
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install it from: https://cli.github.com/{Colors.RESET}")
        print()
        return False

    print()
    print(
        f"{Colors.WHITE}Your browser will open to authenticate with GitHub.{Colors.RESET}"
    )
    print()
    print(f"{Colors.CYAN}Executing: gh auth login{Colors.RESET}")
    print()

    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["gh", "auth", "login"], check=False
        )

        if result.returncode == 0:
            print()
            print(f"{Colors.GREEN}✓ Authentication completed.{Colors.RESET}")
            print()

            # Verify who is authenticated
            is_auth: bool
            user: str
            is_auth, user = check_gh_auth()
            if is_auth:
                print(f"{Colors.GREEN}Authenticated as: {user}{Colors.RESET}")
            return True
        else:
            print()
            print(f"{Colors.RED}✗ Authentication canceled or failed.{Colors.RESET}")
            return False

    except Exception as e:
        print()
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return False
