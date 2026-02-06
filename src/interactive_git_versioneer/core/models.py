"""
Data models for interactive-git-versioneer.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Commit:
    """Represents an untagged commit.

    Attributes:
        hash: The full hash of the commit.
        message: The first line of the commit message.
        author: The name of the commit author.
        date: The commit date in 'YYYY-MM-DD' format.
        version_type: The suggested version type ("major", "minor", "patch") for this commit.
        custom_message: A custom tag message for this commit, if provided.
        processed: A boolean indicating if this commit has been processed for tagging.
    """

    hash: str
    message: str
    author: str
    date: str
    version_type: Optional[str] = None
    custom_message: Optional[str] = None
    processed: bool = False
