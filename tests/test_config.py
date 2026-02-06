"""Tests for the config module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from interactive_git_versioneer.config import config


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    """Redirect config path to a temp directory for the duration of the test."""
    fake_path = tmp_path / "config.json"
    # Patch at module level to ensure all imports use the test path
    monkeypatch.setattr(config, "get_config_path", lambda: fake_path)
    yield fake_path


class TestLoadConfig:
    def test_load_config_no_file(self, config_dir):
        assert config.load_config() == {}

    def test_load_config_valid(self, config_dir):
        config_dir.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        assert config.load_config() == {"key": "value"}

    def test_load_config_invalid_json(self, config_dir):
        config_dir.write_text("not valid json", encoding="utf-8")
        assert config.load_config() == {}


class TestSaveConfig:
    def test_save_config_creates_file(self, config_dir):
        config.save_config({"hello": "world"})
        data = json.loads(config_dir.read_text(encoding="utf-8"))
        assert data == {"hello": "world"}

    def test_save_config_creates_parent_dir(self, tmp_path, monkeypatch):
        nested = tmp_path / "a" / "b" / "config.json"
        monkeypatch.setattr(config, "get_config_path", lambda: nested)
        config.save_config({"nested": True})
        assert nested.exists()


class TestSetAndGetConfigValue:
    def test_set_and_get_simple_key(self, config_dir):
        config.set_config_value("name", "igv")
        assert config.get_config_value("name") == "igv"

    def test_set_and_get_nested_key(self, config_dir):
        config.set_config_value("OPENAI.key", "sk-test-123")
        assert config.get_config_value("OPENAI.key") == "sk-test-123"

    def test_set_overwrites_existing(self, config_dir):
        config.set_config_value("name", "old")
        config.set_config_value("name", "new")
        assert config.get_config_value("name") == "new"

    def test_get_missing_key_returns_none(self, config_dir):
        assert config.get_config_value("missing") is None

    def test_get_missing_nested_key_returns_none(self, config_dir):
        config.set_config_value("OPENAI.key", "val")
        assert config.get_config_value("OPENAI.missing") is None

    def test_get_returns_none_for_dict_value(self, config_dir):
        """Getting a key that points to a dict (not a leaf) returns None."""
        config.set_config_value("SECTION.child", "val")
        assert config.get_config_value("SECTION") is None
