"""Port (interface) for AI-powered text generation services.

Any concrete AI provider (OpenAI, Groq, OpenRouter, etc.) must implement
this interface. Application code depends only on this abstraction, never
on the concrete adapter.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class AiService(ABC):
    """Abstract port for AI-powered text generation.

    Follows the Ports & Adapters (Hexagonal) pattern: the domain defines
    what it needs; the infrastructure layer provides the implementation.
    """

    @abstractmethod
    def generate_tag_message(
        self,
        commit_message: str,
        commit_diff: str,
        version_type: str,
        max_length: int = 72,
        locale: str = "es",
    ) -> Optional[str]:
        """Generate a concise git tag message from a commit.

        Args:
            commit_message: The original commit message.
            commit_diff: The diff of the commit (changes made).
            version_type: Semantic version type context (major/minor/patch).
            max_length: Maximum character length for the generated message.
            locale: Language code for the output (e.g., "es", "en").

        Returns:
            The generated tag message, or None if generation fails.
        """

    @abstractmethod
    def determine_version_type(
        self,
        commit_message: str,
        commit_diff: str,
    ) -> Tuple[str, str]:
        """Classify a commit into a semantic version type.

        Args:
            commit_message: The original commit message.
            commit_diff: The diff of the commit (changes made).

        Returns:
            A tuple of (version_type, reason) where version_type is one of
            "major", "minor", "patch" and reason is a brief justification.
        """
