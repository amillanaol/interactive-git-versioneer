"""
Port (interface) for Git operations used by the application layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

# Import the domain Commit model – this avoids circular imports because the
# domain layer does not depend on any infrastructure.
from ..models.commit import Commit


class GitRepository(ABC):
    """Abstract interface defining the Git operations required by the app.

    The concrete implementation lives in the ``infrastructure.git`` package.
    """

    @abstractmethod
    def get_last_tag(self) -> Optional[str]:
        """Return the most recent tag name, or ``None`` if no tags exist."""

    @abstractmethod
    def get_commits_since(self, tag: Optional[str]) -> List[Commit]:
        """Return a list of :class:`Commit` objects after ``tag``.

        ``tag`` can be ``None`` to retrieve all commits.
        """

    @abstractmethod
    def create_tag(self, name: str, commit_hash: str, message: str) -> None:
        """Create a new tag pointing at ``commit_hash`` with ``message``.
        """

    @abstractmethod
    def delete_tag(self, name: str) -> None:
        """Delete the tag identified by ``name``."""

    @abstractmethod
    def push_tags(self) -> None:
        """Push local tags to the remote repository."""
