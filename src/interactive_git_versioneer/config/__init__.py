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
    get_ini_config_path,
    get_prompt_template_path,
    get_prompt_tags_template_path,
    get_ini_value,
    get_ini_bool,
    load_prompt_template,
    load_prompt_tags_template,
    get_tag_detail_level,
    load_ini_config,
    save_ini_config,
)
from .menu import run_config_menu

__all__ = [
    "get_config_path",
    "load_config",
    "save_config",
    "set_config_value",
    "get_config_value",
    "get_ini_config_path",
    "get_prompt_template_path",
    "get_prompt_tags_template_path",
    "get_ini_value",
    "get_ini_bool",
    "load_prompt_template",
    "load_prompt_tags_template",
    "get_tag_detail_level",
    "run_config_menu",
]
