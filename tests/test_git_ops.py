"""Tests for the git_ops module."""

from unittest.mock import MagicMock, patch

import pytest

from interactive_git_versioneer.core.git_ops import (
    get_last_tag,
    get_last_version_number,
    get_next_version,
    parse_version,
)


class TestParseVersion:
    def test_standard_version(self):
        assert parse_version("v1.2.3") == (1, 2, 3)

    def test_version_without_prefix(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_version_zeros(self):
        assert parse_version("v0.0.0") == (0, 0, 0)

    def test_version_large_numbers(self):
        assert parse_version("v10.20.30") == (10, 20, 30)

    def test_invalid_version_returns_zeros(self):
        assert parse_version("not-a-version") == (0, 0, 0)

    def test_empty_string_returns_zeros(self):
        assert parse_version("") == (0, 0, 0)

    def test_partial_version_returns_zeros(self):
        assert parse_version("v1.2") == (0, 0, 0)

    def test_version_with_extra_parts(self):
        # Solo toma los primeros 3
        assert parse_version("v1.2.3.4") == (1, 2, 3)


def _make_tag(name):
    tag = MagicMock()
    tag.name = name
    return tag


class TestGetLastTag:
    def test_returns_highest_version(self):
        repo = MagicMock()
        repo.tags = [_make_tag("v1.0.0"), _make_tag("v2.1.0"), _make_tag("v1.5.3")]
        assert get_last_tag(repo) == "v2.1.0"

    def test_no_tags_returns_none(self):
        repo = MagicMock()
        repo.tags = []
        assert get_last_tag(repo) is None

    def test_single_tag(self):
        repo = MagicMock()
        repo.tags = [_make_tag("v0.1.0")]
        assert get_last_tag(repo) == "v0.1.0"


class TestGetLastVersionNumber:
    def test_with_tags(self):
        repo = MagicMock()
        repo.tags = [_make_tag("v3.2.1")]
        assert get_last_version_number(repo) == (3, 2, 1)

    def test_no_tags(self):
        repo = MagicMock()
        repo.tags = []
        assert get_last_version_number(repo) == (0, 0, 0)


class TestGetNextVersion:
    def _repo_with_tag(self, tag_name):
        repo = MagicMock()
        repo.tags = [_make_tag(tag_name)]
        return repo

    def test_patch_bump(self):
        repo = self._repo_with_tag("v1.2.3")
        assert get_next_version(repo, "patch") == "v1.2.4"

    def test_minor_bump_resets_patch(self):
        repo = self._repo_with_tag("v1.2.3")
        assert get_next_version(repo, "minor") == "v1.3.0"

    def test_major_bump_resets_minor_and_patch(self):
        repo = self._repo_with_tag("v1.2.3")
        assert get_next_version(repo, "major") == "v2.0.0"

    def test_first_patch_from_zero(self):
        repo = MagicMock()
        repo.tags = []
        assert get_next_version(repo, "patch") == "v0.0.1"

    def test_first_minor_from_zero(self):
        repo = MagicMock()
        repo.tags = []
        assert get_next_version(repo, "minor") == "v0.1.0"

    def test_first_major_from_zero(self):
        repo = MagicMock()
        repo.tags = []
        assert get_next_version(repo, "major") == "v1.0.0"

    def test_invalid_version_type_raises(self):
        repo = self._repo_with_tag("v1.0.0")
        with pytest.raises(ValueError, match="Invalid version type"):
            get_next_version(repo, "invalid")
