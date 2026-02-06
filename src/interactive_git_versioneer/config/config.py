"""
Configuration module for interactive-git-versioneer.

Handles reading and writing configuration to ~/.igv/config.json.
"""

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
