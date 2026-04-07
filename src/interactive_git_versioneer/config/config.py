"""
Configuration module for interactive-git-versioneer.

Handles reading and writing configuration to ~/.igv/config.json.
Supports both JSON and INI formats.
"""

import configparser
import json
import os
from pathlib import Path
from typing import Any, Optional


def get_config_path() -> Path:
    """Returns the path to the configuration file.

    Returns:
        Path: The path to ~/.igv/config.json.
    """
    return Path.home() / ".igv" / "config.json"


def get_ini_config_path() -> Path:
    """Returns the path to the INI configuration file.

    Returns:
        Path: The path to ~/.igv/config.ini.
    """
    return Path.home() / ".igv" / "config.ini"


def get_prompt_template_path() -> Path:
    """Returns the path to the prompt template file.

    Returns:
        Path: The path to ~/.igv/prompt.txt.
    """
    return Path.home() / ".igv" / "prompt.txt"


def load_config() -> dict:
    """Loads the existing configuration.

    Returns:
        dict: The loaded configuration or an empty dictionary if it doesn't exist or is invalid.
    """
    config_path: Path = get_config_path()

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: dict) -> None:
    """Saves the given configuration to the file.

    Args:
        config: The dictionary containing the configuration to save.
    """
    config_path: Path = get_config_path()

    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def set_config_value(key: str, value: str) -> None:
    """Sets a value in the configuration.

    Supports dot notation for nested keys (e.g., "OPENAI.key").

    Args:
        key (str): The key to set (can use dot notation for nested keys, e.g., "SECTION.KEY").
        value (str): The value to assign to the specified key.
    """
    config: dict = load_config()
    keys: list[str] = key.split(".")

    # Navigate/create the nested structure
    current: Any = config
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]

    # Set the final value
    current[keys[-1]] = value

    save_config(config)


def get_config_value(key: str) -> Optional[str]:
    """Retrieves a value from the configuration.

    Supports dot notation for nested keys (e.g., "OPENAI.key").

    Args:
        key (str): The key to retrieve (can use dot notation for nested keys, e.g., "SECTION.KEY").

    Returns:
        Optional[str]: The found value as a string, or None if it does not exist.
    """
    config: dict = load_config()
    keys: list[str] = key.split(".")

    current: Any = config
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return None
        current = current[k]

    return current if not isinstance(current, dict) else None


def load_ini_config() -> configparser.ConfigParser:
    """Loads the INI configuration file.

    Returns:
        ConfigParser: The loaded INI configuration, or empty if file doesn't exist.
    """
    ini_path: Path = get_ini_config_path()

    if not ini_path.exists():
        return configparser.ConfigParser()

    try:
        parser = configparser.ConfigParser()
        parser.read(ini_path, encoding="utf-8")
        return parser
    except configparser.Error:
        return configparser.ConfigParser()


def get_ini_value(
    section: str, key: str, fallback: Optional[str] = None
) -> Optional[str]:
    """Retrieves a value from the INI configuration.

    Args:
        section (str): The section in the INI file (e.g., "OLLAMA").
        key (str): The key within the section (e.g., "model").
        fallback (Optional[str]): Default value if not found.

    Returns:
        Optional[str]: The found value, or fallback.
    """
    parser: configparser.ConfigParser = load_ini_config()
    return parser.get(section, key, fallback=fallback)


def get_ini_bool(section: str, key: str, fallback: bool = False) -> bool:
    """Retrieves a boolean value from the INI configuration.

    Args:
        section (str): The section in the INI file.
        key (str): The key within the section.
        fallback (bool): Default value if not found.

    Returns:
        bool: The boolean value.
    """
    parser: configparser.ConfigParser = load_ini_config()
    try:
        return parser.getboolean(section, key)
    except (configparser.Error, AttributeError):
        return fallback


def save_ini_config(parser: configparser.ConfigParser) -> None:
    """Saves the INI configuration to the file.

    Args:
        parser: The ConfigParser with the configuration to save.
    """
    ini_path: Path = get_ini_config_path()

    ini_path.parent.mkdir(parents=True, exist_ok=True)

    with open(ini_path, "w", encoding="utf-8") as f:
        parser.write(f)


def load_prompt_template() -> Optional[str]:
    """Loads the prompt template from prompt.txt.

    Returns:
        Optional[str]: The prompt template content, or None if file doesn't exist.
    """
    template_path: Path = get_prompt_template_path()

    if not template_path.exists():
        return None

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None


def get_prompt_tags_template_path() -> Path:
    """Returns the path to the prompt tags template file.

    Returns:
        Path: The path to ~/.igv/prompt_tags.txt.
    """
    return Path.home() / ".igv" / "prompt_tags.txt"


def load_prompt_tags_template() -> Optional[str]:
    """Loads the prompt tags template from prompt_tags.txt.

    Returns:
        Optional[str]: The prompt tags template content, or None if file doesn't exist.
    """
    template_path: Path = get_prompt_tags_template_path()

    if not template_path.exists():
        return None

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None


def get_tag_detail_level() -> str:
    """Gets the tag detail level from config.ini.

    Returns:
        str: The detail level (concise, detailed, comprehensive). Defaults to "detailed".
    """
    return get_ini_value("TAGS", "detailLevel", "detailed") or "detailed"
