"""Tests for the models module."""

from interactive_git_versioneer.core.models import Commit


class TestCommit:
    """Tests for the Commit dataclass."""

    def test_commit_creation_minimal(self):
        commit = Commit(
            hash="abc123def456",
            message="feat: add new feature",
            author="Test Author",
            date="2024-01-15",
        )

        assert commit.hash == "abc123def456"
        assert commit.message == "feat: add new feature"
        assert commit.author == "Test Author"
        assert commit.date == "2024-01-15"
        assert commit.version_type is None
        assert commit.custom_message is None
        assert commit.processed is False

    def test_commit_creation_full(self):
        commit = Commit(
            hash="abc123def456",
            message="fix: resolve bug",
            author="Test Author",
            date="2024-01-15",
            version_type="patch",
            custom_message="Custom tag message",
            processed=True,
        )

        assert commit.version_type == "patch"
        assert commit.custom_message == "Custom tag message"
        assert commit.processed is True

    def test_commit_mutability(self):
        commit = Commit(
            hash="abc123", message="initial", author="author", date="2024-01-01"
        )

        commit.version_type = "minor"
        commit.processed = True
        commit.custom_message = "Updated message"

        assert commit.version_type == "minor"
        assert commit.processed is True
        assert commit.custom_message == "Updated message"
