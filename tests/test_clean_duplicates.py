"""Tests for the clean_duplicate_tags functionality."""

from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest

from interactive_git_versioneer.core.git_ops import parse_version


class TestDuplicateTagsDetection:
    """Test suite for duplicate tags detection logic."""

    def _make_tag(self, name, commit_sha):
        """Helper to create a mock tag."""
        tag = MagicMock()
        tag.name = name
        tag.commit = MagicMock()
        tag.commit.hexsha = commit_sha
        return tag

    def test_detect_duplicates_simple(self):
        """Test detection of tags pointing to same commit."""
        # Simulate the duplicate detection logic
        commit_sha = "c71da3308937a51dc3bb1212fba67a0c2d848deb"
        tags = [
            self._make_tag("v0.26.0", commit_sha),
            self._make_tag("v0.23.0", commit_sha),
            self._make_tag("v0.20.0", commit_sha),
            self._make_tag("v0.17.0", commit_sha),
        ]

        # Map commits to tags
        commit_to_tags = defaultdict(list)
        for tag in tags:
            commit_to_tags[tag.commit.hexsha].append(tag.name)

        # Find duplicates
        duplicates = {
            sha: tag_names
            for sha, tag_names in commit_to_tags.items()
            if len(tag_names) > 1
        }

        assert len(duplicates) == 1
        assert commit_sha in duplicates
        assert len(duplicates[commit_sha]) == 4

    def test_select_highest_version(self):
        """Test that highest version is selected to keep."""
        tag_names = ["v0.17.0", "v0.26.0", "v0.20.0", "v0.23.0"]

        # Sort by version (descending)
        sorted_tags = sorted(tag_names, key=parse_version, reverse=True)

        keep_tag = sorted_tags[0]
        delete_tags = sorted_tags[1:]

        assert keep_tag == "v0.26.0"
        assert delete_tags == ["v0.23.0", "v0.20.0", "v0.17.0"]

    def test_no_duplicates(self):
        """Test that no duplicates are detected when tags point to different commits."""
        tags = [
            self._make_tag("v0.26.0", "commit1"),
            self._make_tag("v0.25.0", "commit2"),
            self._make_tag("v0.24.0", "commit3"),
        ]

        # Map commits to tags
        commit_to_tags = defaultdict(list)
        for tag in tags:
            commit_to_tags[tag.commit.hexsha].append(tag.name)

        # Find duplicates
        duplicates = {
            sha: tag_names
            for sha, tag_names in commit_to_tags.items()
            if len(tag_names) > 1
        }

        assert len(duplicates) == 0

    def test_multiple_commits_with_duplicates(self):
        """Test detection of multiple commits with duplicate tags."""
        commit1 = "c71da3308937a51dc3bb1212fba67a0c2d848deb"
        commit2 = "55510499055d87acbb5463f62d8add6825ade5fc"

        tags = [
            # Commit 1 duplicates
            self._make_tag("v0.26.0", commit1),
            self._make_tag("v0.23.0", commit1),
            self._make_tag("v0.20.0", commit1),
            # Commit 2 duplicates
            self._make_tag("v0.27.0", commit2),
            self._make_tag("v0.24.0", commit2),
            self._make_tag("v0.21.0", commit2),
        ]

        # Map commits to tags
        commit_to_tags = defaultdict(list)
        for tag in tags:
            commit_to_tags[tag.commit.hexsha].append(tag.name)

        # Find duplicates
        duplicates = {
            sha: tag_names
            for sha, tag_names in commit_to_tags.items()
            if len(tag_names) > 1
        }

        assert len(duplicates) == 2
        assert commit1 in duplicates
        assert commit2 in duplicates
        assert len(duplicates[commit1]) == 3
        assert len(duplicates[commit2]) == 3

    def test_version_comparison_edge_cases(self):
        """Test version comparison with edge cases."""
        # Test major version difference
        assert parse_version("v2.0.0") > parse_version("v1.9.9")

        # Test minor version difference
        assert parse_version("v1.10.0") > parse_version("v1.9.0")

        # Test patch version difference
        assert parse_version("v1.0.10") > parse_version("v1.0.9")

    def test_tags_to_delete_count(self):
        """Test calculation of tags to delete vs keep."""
        duplicates = {
            "commit1": ["v0.26.0", "v0.23.0", "v0.20.0", "v0.17.0"],
            "commit2": ["v0.27.0", "v0.24.0", "v0.21.0"],
        }

        tags_to_delete = []
        tags_to_keep = []

        for commit_sha, tag_names in duplicates.items():
            sorted_tags = sorted(tag_names, key=parse_version, reverse=True)
            keep_tag = sorted_tags[0]
            delete_tags = sorted_tags[1:]

            tags_to_keep.append(keep_tag)
            tags_to_delete.extend(delete_tags)

        assert len(tags_to_keep) == 2  # One per commit
        assert len(tags_to_delete) == 5  # Total duplicates to remove
        assert "v0.26.0" in tags_to_keep
        assert "v0.27.0" in tags_to_keep
        assert "v0.17.0" in tags_to_delete
        assert "v0.20.0" in tags_to_delete
        assert "v0.23.0" in tags_to_delete
        assert "v0.21.0" in tags_to_delete
        assert "v0.24.0" in tags_to_delete


class TestCleanDuplicateTagsIntegration:
    """Integration tests for clean_duplicate_tags function."""

    @patch('builtins.input', return_value='n')
    @patch('interactive_git_versioneer.tags.actions.clear_screen')
    @patch('interactive_git_versioneer.tags.actions.print_header')
    def test_cancel_operation(self, mock_header, mock_clear, mock_input):
        """Test that operation can be cancelled."""
        from interactive_git_versioneer.tags.actions import clean_duplicate_tags

        # Create mock repo with duplicate tags
        repo = MagicMock()

        commit1 = MagicMock()
        commit1.hexsha = "abc123"
        commit1.message = "Test commit"

        tag1 = MagicMock()
        tag1.name = "v1.0.0"
        tag1.commit = commit1

        tag2 = MagicMock()
        tag2.name = "v0.9.0"
        tag2.commit = commit1

        repo.tags = [tag1, tag2]
        repo.commit = MagicMock(return_value=commit1)

        # Execute with 'n' input to cancel
        result = clean_duplicate_tags(repo, include_remote=False)

        # Should return False (cancelled)
        assert result is False

    @patch('interactive_git_versioneer.tags.actions.wait_for_enter')
    def test_no_duplicates_found(self, mock_wait):
        """Test behavior when no duplicates are found."""
        from interactive_git_versioneer.tags.actions import clean_duplicate_tags

        # Create mock repo with no duplicate tags
        repo = MagicMock()

        commit1 = MagicMock()
        commit1.hexsha = "abc123"

        commit2 = MagicMock()
        commit2.hexsha = "def456"

        tag1 = MagicMock()
        tag1.name = "v1.0.0"
        tag1.commit = commit1

        tag2 = MagicMock()
        tag2.name = "v0.9.0"
        tag2.commit = commit2

        repo.tags = [tag1, tag2]

        # Execute
        result = clean_duplicate_tags(repo, include_remote=False)

        # Should return True (success, no duplicates)
        assert result is True
