"""
Configuration submenu for interactive-git-versioneer.

Manages AI configuration and system alias creation.
"""

import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, List, Literal, Optional, Tuple

from ..core.ui import Colors, Menu, clear_screen, print_header, wait_for_enter
from .config import get_config_value, load_config, set_config_value


_MODEL_PAGE_SIZE: int = 10


def _format_ctx(ctx: Optional[int]) -> str:
    """Format a token count as a human-readable string (e.g. 128K, 1M)."""
    if ctx is None:
        return "-"
    if ctx >= 1_000_000:
        return f"{ctx // 1_000_000}M"
    return f"{ctx // 1_000}K"


def _select_model_interactive() -> Optional[str]:
    """Show a paginated model picker populated from the provider API.

    Fetches the model list using the currently configured credentials.
    Falls back to a manual text prompt if the API call fails.

    Returns:
        The selected model id, or None if the user cancels.
    """
    from ..core.ai import list_available_models

    print(f"{Colors.CYAN}Fetching available models...{Colors.RESET}", end="", flush=True)
    models: List[dict] = list_available_models()
    print()

    if not models:
        print(
            f"{Colors.YELLOW}Could not fetch model list "
            f"(check OPENAI.key and OPENAI.baseURL).{Colors.RESET}"
        )
        print()
        typed: str = input(f"{Colors.WHITE}Enter model name: {Colors.RESET}").strip()
        return typed or None

    current_model: Optional[str] = get_config_value("OPENAI.model")
    total: int = len(models)
    total_pages: int = (total + _MODEL_PAGE_SIZE - 1) // _MODEL_PAGE_SIZE
    page: int = 0

    while True:
        clear_screen()
        start: int = page * _MODEL_PAGE_SIZE
        page_models: List[dict] = models[start : start + _MODEL_PAGE_SIZE]

        print_header(f"SELECT MODEL  (page {page + 1}/{total_pages}  —  {total} models)")
        print()

        id_col: int = min(max((len(m["id"]) for m in page_models), default=20), 45)
        print(
            f"  {'#':>2}  {Colors.WHITE}{'Model':<{id_col}}{Colors.RESET}"
            f"  {Colors.CYAN}{'Context':>7}{Colors.RESET}"
            f"  {'Provider':<14}  Free"
        )
        print(f"  {'─' * (id_col + 36)}")

        for i, m in enumerate(page_models, 1):
            mid: str = m["id"]
            display: str = mid if len(mid) <= id_col else mid[: id_col - 2] + ".."
            ctx_str: str = _format_ctx(m["context_window"])
            owner: str = (m["owned_by"] or "")[:14]
            marker: str = (
                f"{Colors.GREEN}→ {Colors.RESET}" if mid == current_model else "  "
            )
            free_val: Optional[bool] = m.get("is_free")
            if free_val is True:
                free_str: str = f"{Colors.GREEN}Yes{Colors.RESET}"
            elif free_val is False:
                free_str = "No "
            else:
                free_str = "-  "
            print(
                f"{marker}{i:>2}  {Colors.WHITE}{display:<{id_col}}{Colors.RESET}"
                f"  {Colors.CYAN}{ctx_str:>7}{Colors.RESET}"
                f"  {owner:<14}  {free_str}"
            )

        print()
        nav: List[str] = []
        if page < total_pages - 1:
            nav.append("[n] Next")
        if page > 0:
            nav.append("[p] Prev")
        nav.append("[m] Type manually")
        nav.append("[0] Cancel")
        print(f"  {Colors.WHITE}{'  '.join(nav)}{Colors.RESET}")
        print()

        try:
            sel: str = input(f"{Colors.WHITE}Select: {Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            return None

        if sel in ("0", ""):
            return None
        elif sel == "n" and page < total_pages - 1:
            page += 1
        elif sel == "p" and page > 0:
            page -= 1
        elif sel == "m":
            typed = input(f"{Colors.WHITE}Enter model name: {Colors.RESET}").strip()
            return typed or None
        elif sel.isdigit():
            idx: int = int(sel) - 1
            if 0 <= idx < len(page_models):
                return page_models[idx]["id"]
            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")


def _detect_provider(base_url: Optional[str]) -> str:
    """Infer the AI provider name from its base URL.

    Args:
        base_url: The configured OPENAI.baseURL value.

    Returns:
        A human-readable provider name.
    """
    if not base_url:
        return "Unknown"
    if "groq.com" in base_url:
        return "Groq"
    if "openrouter.ai" in base_url:
        return "OpenRouter"
    if "openai.com" in base_url:
        return "OpenAI"
    return "Custom"


def run_config_menu() -> None:
    """Executes the configuration submenu.

    This function presents a menu to the user for managing various configuration
    settings, such as AI integration and system alias creation.
    """

    def show_config_status() -> None:
        """Displays the current status of the AI configuration.

        This includes whether the API key is configured and the active model.
        """
        api_key: Optional[str] = get_config_value("OPENAI.key")
        base_url: Optional[str] = get_config_value("OPENAI.baseURL")
        model: Optional[str] = get_config_value("OPENAI.model")

        if api_key:
            masked_key: str = api_key[:8] + "..." if len(api_key) > 8 else "***"
            provider: str = _detect_provider(base_url)
            print(f"{Colors.GREEN}AI: {provider} ({masked_key}){Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}AI: Not configured{Colors.RESET}")

        if model:
            print(f"{Colors.WHITE}Model: {model}{Colors.RESET}")

    def action_show_config() -> Literal[False]:
        """Displays the current configuration loaded from the configuration file.

        Retrieves and prints the stored configuration, masking sensitive API keys
        for security purposes.

        Returns:
            Literal[False]: Always returns False to keep the configuration menu open.
        """
        clear_screen()
        print_header("CURRENT CONFIGURATION")
        print()

        # ── AI integration summary (derived from config) ──────────────────
        ai_key: Optional[str] = get_config_value("OPENAI.key")
        ai_url: Optional[str] = get_config_value("OPENAI.baseURL")
        ai_model: Optional[str] = get_config_value("OPENAI.model")

        provider: str = _detect_provider(ai_url)
        provider_color: str = Colors.GREEN if ai_key else Colors.YELLOW
        provider_label: str = provider if ai_key else "Not configured"

        print(f"{Colors.CYAN}AI:{Colors.RESET}")
        print(
            f"  {Colors.WHITE}Proveedor actual:      {Colors.RESET}"
            f"{provider_color}{provider_label}{Colors.RESET}"
        )
        print(
            f"  {Colors.WHITE}Proveedores disponibles:{Colors.RESET}"
            f" {Colors.YELLOW}Groq{Colors.RESET}"
            f" · {Colors.YELLOW}OpenRouter{Colors.RESET}"
            f" · {Colors.YELLOW}OpenAI{Colors.RESET}"
            f" · {Colors.YELLOW}Custom{Colors.RESET}"
        )
        if ai_model:
            print(
                f"  {Colors.WHITE}Modelo activo:         {Colors.RESET}"
                f"{Colors.GREEN}{ai_model}{Colors.RESET}"
            )
        print()

        # ── Raw stored configuration ──────────────────────────────────────
        config: dict = load_config()

        if not config:
            print(f"{Colors.YELLOW}No configuration saved.{Colors.RESET}")
        else:
            for section, values in config.items():
                print(f"{Colors.CYAN}{section}:{Colors.RESET}")
                if isinstance(values, dict):
                    for key, value in values.items():
                        # Partially hide API keys
                        if "key" in key.lower() and value:
                            display_value: str = (
                                value[:8] + "..." if len(str(value)) > 8 else "***"
                            )
                        else:
                            display_value = value
                        print(
                            f"  {Colors.WHITE}{key}: {Colors.GREEN}{display_value}{Colors.RESET}"
                        )
                else:
                    print(f"  {Colors.GREEN}{values}{Colors.RESET}")
                print()

        print()
        wait_for_enter()
        return False

    def action_configure_ai() -> Literal[False]:
        """Configures AI integration settings for services like Groq/OpenAI.

        This interactive function guides the user to set or update the API key,
        base URL, and AI model, including a streamlined quick setup for Groq.

        Returns:
            Literal[False]: Always returns False to ensure the configuration menu remains active.
        """
        clear_screen()
        print_header("CONFIGURE AI (Groq/OpenRouter/OpenAI)")
        print()

        print(f"{Colors.WHITE}Current configuration:{Colors.RESET}")
        current_key: Optional[str] = get_config_value("OPENAI.key")
        current_url: Optional[str] = get_config_value("OPENAI.baseURL")
        current_model: Optional[str] = get_config_value("OPENAI.model")

        if current_key:
            print(f"  API Key: {Colors.GREEN}{current_key[:8]}...{Colors.RESET}")
        else:
            print(f"  API Key: {Colors.YELLOW}Not configured{Colors.RESET}")

        print(
            f"  Base URL: {Colors.CYAN}{current_url or 'Not configured'}{Colors.RESET}"
        )
        print(
            f"  Model: {Colors.CYAN}{current_model or 'Not configured'}{Colors.RESET}"
        )
        print()

        print(f"{Colors.WHITE}What do you want to configure?{Colors.RESET}")
        print(f"  1. API Key")
        print(f"  2. Base URL")
        print(f"  3. Model")
        print(f"  4. Quick setup (Groq)")
        print(f"  5. Quick setup (OpenRouter)")
        print(f"  0. Back")
        print()

        choice: str = input(f"{Colors.WHITE}Select option: {Colors.RESET}").strip()

        if choice == "1":
            new_key: str = input(f"{Colors.WHITE}Enter API Key: {Colors.RESET}").strip()
            if new_key:
                set_config_value("OPENAI.key", new_key)
                print(f"{Colors.GREEN}✓ API Key saved{Colors.RESET}")

        elif choice == "2":
            print(f"{Colors.CYAN}Examples:{Colors.RESET}")
            print(f"  Groq:       https://api.groq.com/openai/v1")
            print(f"  OpenRouter: https://openrouter.ai/api/v1")
            print(f"  OpenAI:     https://api.openai.com/v1")
            new_url: str = input(
                f"{Colors.WHITE}Enter Base URL: {Colors.RESET}"
            ).strip()
            if new_url:
                set_config_value("OPENAI.baseURL", new_url)
                print(f"{Colors.GREEN}✓ Base URL saved{Colors.RESET}")

        elif choice == "3":
            selected_model: Optional[str] = _select_model_interactive()
            if selected_model:
                set_config_value("OPENAI.model", selected_model)
                clear_screen()
                print_header("CONFIGURE AI (Groq/OpenRouter/OpenAI)")
                print()
                print(f"{Colors.GREEN}✓ Model saved: {selected_model}{Colors.RESET}")

        elif choice == "4":
            print()
            print(f"{Colors.CYAN}Quick setup for Groq{Colors.RESET}")
            print(
                f"{Colors.WHITE}Get your API key at: https://console.groq.com/keys{Colors.RESET}"
            )
            print()
            api_key_input: str = input(
                f"{Colors.WHITE}Enter your Groq API Key: {Colors.RESET}"
            ).strip()
            if api_key_input:
                set_config_value("OPENAI.key", api_key_input)
                set_config_value("OPENAI.baseURL", "https://api.groq.com/openai/v1")
                set_config_value("OPENAI.model", "llama-3.3-70b-versatile")
                print()
                print(f"{Colors.GREEN}✓ Groq configuration completed{Colors.RESET}")

        elif choice == "5":
            print()
            print(f"{Colors.CYAN}Quick setup for OpenRouter{Colors.RESET}")
            print(
                f"{Colors.WHITE}Get your API key at: https://openrouter.ai/keys{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}Hundreds of models available at: https://openrouter.ai/models{Colors.RESET}"
            )
            print()
            api_key_input = input(
                f"{Colors.WHITE}Enter your OpenRouter API Key: {Colors.RESET}"
            ).strip()
            if api_key_input:
                set_config_value("OPENAI.key", api_key_input)
                set_config_value("OPENAI.baseURL", "https://openrouter.ai/api/v1")
                set_config_value(
                    "OPENAI.model", "meta-llama/llama-3.3-70b-instruct"
                )
                print()
                print(
                    f"{Colors.GREEN}✓ OpenRouter configuration completed{Colors.RESET}"
                )
                print(
                    f"{Colors.WHITE}Default model: meta-llama/llama-3.3-70b-instruct{Colors.RESET}"
                )

        print()
        wait_for_enter()
        return False

    def action_add_alias() -> Literal[False]:
        """Adds the 'igv' command alias to the user's system.

        This function detects the operating system (Windows or Unix-like) and
        invokes the relevant helper function to establish 'igv' as a system-wide
        command for easier execution.

        Returns:
            Literal[False]: Always returns False to ensure the configuration menu remains active.
        """
        clear_screen()
        print_header("ADD 'igv' ALIAS TO SYSTEM")
        print()

        # Detectar sistema operativo
        is_windows: bool = sys.platform == "win32"

        if is_windows:
            _add_alias_windows()
        else:
            _add_alias_unix()

        print()
        wait_for_enter()
        return False

    def action_show_help() -> Literal[False]:
        """Displays comprehensive help information for `igv config` commands.

        This function provides detailed usage instructions for available CLI
        configuration commands (`list`, `get`, `set`) and enumerates the
        various configuration keys that can be managed.

        Returns:
            Literal[False]: Always returns False to ensure the configuration menu remains active.
        """
        clear_screen()
        print_header("HELP - CONFIGURATION COMMANDS")
        print()

        print(f"{Colors.WHITE}Commands available from terminal:{Colors.RESET}")
        print()
        print(
            f"{Colors.CYAN}  igv config list{Colors.RESET}           - View current configuration"
        )
        print(f"{Colors.CYAN}  igv config get <key>{Colors.RESET}    - Get a value")
        print(
            f"{Colors.CYAN}  igv config set <key> <value>{Colors.RESET} - Set a value"
        )
        print()
        print(f"{Colors.WHITE}Available keys:{Colors.RESET}")
        print(f"  {Colors.YELLOW}OPENAI.key{Colors.RESET}      - API key (Groq / OpenRouter / OpenAI)")
        print(f"  {Colors.YELLOW}OPENAI.baseURL{Colors.RESET}  - API base URL")
        print(f"  {Colors.YELLOW}OPENAI.model{Colors.RESET}    - Model to use")
        print()
        print(f"{Colors.WHITE}Groq example:{Colors.RESET}")
        print(
            f'{Colors.CYAN}  igv config set OPENAI.key "gsk_your_api_key"{Colors.RESET}'
        )
        print(
            f'{Colors.CYAN}  igv config set OPENAI.baseURL "https://api.groq.com/openai/v1"{Colors.RESET}'
        )
        print(
            f'{Colors.CYAN}  igv config set OPENAI.model "llama-3.3-70b-versatile"{Colors.RESET}'
        )
        print()
        print(f"{Colors.WHITE}OpenRouter example:{Colors.RESET}")
        print(
            f'{Colors.CYAN}  igv config set OPENAI.key "sk-or-v1-your_api_key"{Colors.RESET}'
        )
        print(
            f'{Colors.CYAN}  igv config set OPENAI.baseURL "https://openrouter.ai/api/v1"{Colors.RESET}'
        )
        print(
            f'{Colors.CYAN}  igv config set OPENAI.model "meta-llama/llama-3.3-70b-instruct"{Colors.RESET}'
        )
        print()

        wait_for_enter()
        return False

    def action_back() -> Literal[True]:
        """Exits the configuration submenu and returns to the main menu.

        Returns:
            Literal[True]: Always returns True to signal that the menu should close
                           and control should return to the calling menu.
        """
        return True

    # Create configuration menu
    config_menu: Menu = Menu("CONFIGURATION")
    config_menu.set_status_callback(show_config_status)
    config_menu.add_item("1", "Show current configuration", action_show_config)
    config_menu.add_item("2", "Configure AI (Groq/OpenRouter/OpenAI)", action_configure_ai)
    config_menu.add_item("3", "Add 'igv' alias to system", action_add_alias)
    config_menu.add_item("4", "Help - CLI Commands", action_show_help)
    config_menu.add_item("0", "Back to main menu", action_back)

    config_menu.run()


def _add_alias_windows() -> None:
    """Configures the 'igv' command alias for Windows operating systems.

    This function first verifies if 'igv' is already accessible as a system command.
    If not, it provides interactive guidance and options for the user to
    install 'igv' (e.g., via pip install -e .), add its executable directory
    to the system's PATH, or define a function in the PowerShell profile,
    making 'igv' easily runnable from the command line.
    """
    print(f"{Colors.CYAN}System detected: Windows{Colors.RESET}")
    print()

    # Check if already installed as a command
    result: subprocess.CompletedProcess = subprocess.run(
        ["where", "igv"], capture_output=True, text=True, shell=True
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}✓ The 'igv' command is already available:{Colors.RESET}")
        print(f"  {result.stdout.strip()}")
        return

    # Check if igv.exe exists but is not in PATH
    igv_path: Optional[Path] = _find_igv_executable()

    if igv_path:
        scripts_dir: Path = igv_path.parent
        print(f"{Colors.GREEN}✓ igv.exe installed was found:{Colors.RESET}")
        print(f"  {igv_path}")
        print()
        print(f"{Colors.YELLOW}⚠ The folder is not in the system PATH.{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}To add it, run in PowerShell:{Colors.RESET}")
        print()
        print(
            f'{Colors.CYAN}[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User"){Colors.RESET}'
        )
        print()
        print(f"{Colors.WHITE}Then restart your terminal.{Colors.RESET}")
        print()

        choice: str = (
            input(f"{Colors.WHITE}Execute command automatically? (y/n): {Colors.RESET}")
            .strip()
            .lower()
        )

        if choice == "y":
            _add_to_path_windows(scripts_dir)
        return

    print(f"{Colors.WHITE}Options to add 'igv' on Windows:{Colors.RESET}")
    print()

    # Option 1: pip install -e .
    print(f"{Colors.YELLOW}1. Install with pip (Recommended):{Colors.RESET}")
    print(f"   pip install -e .")
    print(
        f"   {Colors.WHITE}Creates igv.exe and then return here to add to PATH{Colors.RESET}"
    )
    print()

    # Option 2: Create in user folder (more reliable)
    user_bin: Path = Path.home() / ".local" / "bin"
    print(f"{Colors.YELLOW}2. Create script in user folder:{Colors.RESET}")
    print(f"   {user_bin / 'igv.bat'}")
    print()

    # Option 3: PowerShell profile
    print(f"{Colors.YELLOW}3. Add function to PowerShell:{Colors.RESET}")
    print(f"   Added to PowerShell profile")
    print()

    choice = input(
        f"{Colors.WHITE}Select option (1/2/3) or Enter to cancel: {Colors.RESET}"
    ).strip()

    if choice == "1":
        print()
        print(f"{Colors.CYAN}Run in the terminal:{Colors.RESET}")
        print(f"  pip install -e .")
        print()
        print(f"{Colors.WHITE}Then return to this option to add to PATH.{Colors.RESET}")

    elif choice == "2":
        _create_windows_batch_user(user_bin)

    elif choice == "3":
        _create_powershell_function()


def _find_igv_executable() -> Optional[Path]:
    """Locates the 'igv.exe' executable within common Python installation paths on Windows.

    This function systematically checks various standard and user-specific
    locations where Python packages and their executables are typically installed.
    These include the standard Python 'Scripts' directory, paths associated with
    Microsoft Store Python installations, and user-specific pip installation
    directories (e.g., `%APPDATA%\Python\Scripts`).

    Returns:
        Optional[Path]: Returns a `Path` object pointing to 'igv.exe' if found,
                        otherwise returns `None`.
    """
    possible_paths: list[Path] = []

    # Standard Scripts path
    standard_scripts: Path = Path(sys.executable).parent / "Scripts" / "igv.exe"
    possible_paths.append(standard_scripts)

    # Microsoft Store Python
    local_packages: Path = Path.home() / "AppData" / "Local" / "Packages"
    if local_packages.exists():
        for pkg in local_packages.iterdir():
            if pkg.name.startswith("PythonSoftwareFoundation.Python"):
                ms_store_scripts: Path = pkg / "LocalCache" / "local-packages"
                if ms_store_scripts.exists():
                    for python_ver in ms_store_scripts.iterdir():
                        igv_path: Path = python_ver / "Scripts" / "igv.exe"
                        possible_paths.append(igv_path)

    # pip --user install location
    user_scripts: Path = Path.home() / "AppData" / "Roaming" / "Python"
    if user_scripts.exists():
        for python_ver in user_scripts.iterdir():
            igv_path: Path = python_ver / "Scripts" / "igv.exe"
            possible_paths.append(igv_path)

    # Search through the paths
    for path in possible_paths:
        if path.exists():
            return path

    return None


def _add_to_path_windows(scripts_dir: Path) -> None:
    """Adds a specified directory to the current user's PATH environment variable on Windows.

    This function executes a PowerShell command to append the given `scripts_dir`
    to the system's PATH variable, making executables within that directory
    accessible from any command prompt or terminal session. Users are informed
    that a terminal restart is required for changes to take effect.

    Args:
        scripts_dir (Path): The `Path` object representing the directory
                            to be added to the user's PATH.
    """
    try:
        # Execute PowerShell to add to PATH
        ps_command: str = f'[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User")'

        result: CompletedProcess = subprocess.run(
            ["powershell", "-Command", ps_command], capture_output=True, text=True
        )

        if result.returncode == 0:
            print()
            print(f"{Colors.GREEN}✓ Path added to user's PATH{Colors.RESET}")
            print()
            print(
                f"{Colors.YELLOW}⚠ IMPORTANT: You must restart your terminal for changes to take effect.{Colors.RESET}"
            )
            print(f"{Colors.WHITE}After restarting, run: igv --help{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ Error executing command:{Colors.RESET}")
            print(f"  {result.stderr}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")


def _create_windows_batch_user(user_bin: Path) -> None:
    """Creates a batch script (`igv.bat`) in the specified user's local bin folder on Windows.

    This script acts as an alias, allowing the user to execute the `interactive_git_versioneer.main`
    module directly via `igv` from the command line. The function also provides guidance
    on how to add this local bin directory to the system's PATH environment variable
    if it's not already included, and reminds the user to restart their terminal
    for changes to take effect.

    Args:
        user_bin (Path): The `Path` object representing the user's local bin directory
                         where the `igv.bat` script will be created.
    """
    try:
        # Create directory if it doesn't exist
        user_bin.mkdir(parents=True, exist_ok=True)
        batch_path: Path = user_bin / "igv.bat"

        # Create batch script
        batch_content: str = "@echo off\npython -m interactive_git_versioneer.main %*"
        batch_path.write_text(batch_content)

        print()
        print(f"{Colors.GREEN}✓ Script created in: {batch_path}{Colors.RESET}")
        print()

        # Check if it's in PATH
        path_env: str = os.environ.get("PATH", "")
        if str(user_bin) not in path_env:
            print(
                f"{Colors.YELLOW}⚠ The folder is not in the system PATH.{Colors.RESET}"
            )
            print()
            print(f"{Colors.WHITE}To add it permanently:{Colors.RESET}")
            print()
            print(f"{Colors.CYAN}PowerShell (as Administrator):{Colors.RESET}")
            print(
                f'  [Environment]::SetEnvironmentVariable("Path", $env:Path + ";{user_bin}", "User")'
            )
            print()
            print(f"{Colors.CYAN}Or manually:{Colors.RESET}")
            print(f"  1. Search for 'Environment Variables' in Windows")
            print(f"  2. Edit 'Path' in user variables")
            print(f"  3. Add: {user_bin}")
            print()
            print(
                f"{Colors.WHITE}Restart your terminal after adding to PATH.{Colors.RESET}"
            )
        else:
            print(f"{Colors.GREEN}✓ The folder is already in PATH{Colors.RESET}")
            print(f"{Colors.WHITE}Restart your terminal to use 'igv'{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")


def _create_powershell_function() -> None:
    """Adds a persistent 'igv' function to the user's PowerShell profile.

    This function modifies the PowerShell profile script (`Microsoft.PowerShell_profile.ps1`)
    to define an `igv` function. This allows the 'igv' command to be directly
    invoked from any PowerShell session, acting as an alias for
    `python -m interactive_git_versioneer.main`. It also provides instructions
    for users to restart PowerShell and handle potential script execution policy errors.
    """
    # Get PowerShell profile path
    ps_profile: Path = (
        Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    )
    ps_profile_legacy: Path = (
        Path.home()
        / "Documents"
        / "WindowsPowerShell"
        / "Microsoft.PowerShell_profile.ps1"
    )

    # Use the one that exists or prefer the new one
    if ps_profile_legacy.exists() and not ps_profile.exists():
        profile_path: Path = ps_profile_legacy
    else:
        profile_path = ps_profile

    function_code: str = "\n# Interactive Git Versioneer alias\nfunction igv { python -m interactive_git_versioneer.main $args }\n"

    print()
    print(f"{Colors.WHITE}PowerShell profile: {profile_path}{Colors.RESET}")

    # Check if the function already exists
    if profile_path.exists():
        content: str = profile_path.read_text(encoding="utf-8", errors="ignore")
        if "function igv" in content:
            print(
                f"{Colors.GREEN}✓ The 'igv' function already exists in the profile{Colors.RESET}"
            )
            print(f"{Colors.WHITE}Restart PowerShell to activate it{Colors.RESET}")
            return

    try:
        # Create directory if it doesn't exist
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        # Add function to profile
        with open(profile_path, "a", encoding="utf-8") as f:
            f.write(function_code)

        print(f"{Colors.GREEN}✓ Function added to PowerShell profile{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}Restart PowerShell to use 'igv'{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}If you see script execution errors, run:{Colors.RESET}")
        print(f"  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        print()
        print(f"{Colors.WHITE}Add it manually to your profile:{Colors.RESET}")
        print(f"  {function_code.strip()}")


def _add_alias_unix() -> None:
    """Configures the 'igv' command alias for Unix-like operating systems (Linux/macOS).

    This function first checks if 'igv' is already a recognized command. If not,
    it identifies the user's shell (bash or zsh) and attempts to add a permanent
    alias for 'igv' (mapping to `python -m interactive_git_versioneer.main`)
    to the respective shell configuration file (`.bashrc` or `.zshrc`).
    It then provides instructions for the user to activate the alias by
    sourcing the configuration file or restarting their terminal.
    """
    print(
        f"{Colors.CYAN}System detected: {'macOS' if sys.platform == 'darwin' else 'Linux'}{Colors.RESET}"
    )
    print()

    # Check if the command already exists
    result: CompletedProcess = subprocess.run(
        ["which", "igv"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}✓ The 'igv' command is already available:{Colors.RESET}")
        print(f"  {result.stdout.strip()}")
        return

    # Detect shell
    shell: str = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        rc_file: Path = Path.home() / ".zshrc"
    else:
        rc_file = Path.home() / ".bashrc"

    alias_line: str = 'alias igv="python -m interactive_git_versioneer.main"'

    print(f"{Colors.WHITE}Shell detected: {shell}{Colors.RESET}")
    print(f"{Colors.WHITE}Configuration file: {rc_file}{Colors.RESET}")
    print()

    # Check if alias already exists
    if rc_file.exists():
        content: str = rc_file.read_text()
        if "alias igv=" in content:
            print(
                f"{Colors.GREEN}✓ The alias already exists in {rc_file.name}{Colors.RESET}"
            )
            print(
                f"{Colors.WHITE}Run 'source {rc_file}' or restart your terminal{Colors.RESET}"
            )
            return

    print(
        f"{Colors.YELLOW}The following line will be added to {rc_file.name}:{Colors.RESET}"
    )
    print(f"  {alias_line}")
    print()

    choice: str = (
        input(f"{Colors.WHITE}Continue? (y/n): {Colors.RESET}").strip().lower()
    )

    if choice == "y":
        try:
            with open(rc_file, "a") as f:
                f.write(f"\n# Interactive Git Versioneer alias\n{alias_line}\n")
            print()
            print(f"{Colors.GREEN}✓ Alias added to {rc_file.name}{Colors.RESET}")
            print()
            print(f"{Colors.WHITE}To activate now, run:{Colors.RESET}")
            print(f"  source {rc_file}")
            print()
            print(f"{Colors.WHITE}Or restart your terminal.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
    else:
        print()
        print(f"{Colors.YELLOW}You can add it manually:{Colors.RESET}")
        print(f"  echo '{alias_line}' >> {rc_file}")
