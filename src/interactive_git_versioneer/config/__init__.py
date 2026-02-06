"""
Configuration module for interactive-git-versioneer.

Re-exports configuration functions and the interactive config menu.
"""

from .config import (
    get_config_path,
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)
from .menu import run_config_menu

__all__ = [
    "get_config_path",
    "load_config",
    "save_config",
    "set_config_value",
    "get_config_value",
    "run_config_menu",
]
