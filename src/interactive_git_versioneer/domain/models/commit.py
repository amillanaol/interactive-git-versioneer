"""
Domain model for a Git commit.

This mirrors the dataclass from the original core.models but adds
encapsulation and simple domain behavior as described in the refactoring
guide.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Commit:
    """Represents a Git commit with domain‑level behavior.

    The fields are intentionally private (prefixed with an underscore) to
    enforce access through properties and methods, allowing validation and
    future invariants.
    """

    hash: str
    message: str
    author: str
    date: str
    _version_type: Optional[str] = None
    _custom_message: Optional[str] = None
    _processed: bool = False

    # ---------------------------------------------------------------------
    # Accessors / Mutators
    # ---------------------------------------------------------------------
    @property
    def version_type(self) -> Optional[str]:
        return self._version_type

    def assign_version_type(self, vtype: str) -> None:
        """Assign a semantic‑version type after validation.

        Args:
            vtype: One of ``"major"``, ``"minor"`` or ``"patch"``.
        """
        if vtype not in ("major", "minor", "patch"):
            raise ValueError(f"Invalid version type: {vtype}")
        self._version_type = vtype
        self._processed = True

    @property
    def custom_message(self) -> Optional[str]:
        return self._custom_message

    def set_custom_message(self, message: str) -> None:
        """Set a custom tag message and mark the commit as processed."""
        self._custom_message = message
        self._processed = True

    @property
    def processed(self) -> bool:
        return self._processed

    # ---------------------------------------------------------------------
    # Convenience helpers used by the existing code base
    # ---------------------------------------------------------------------
    def as_dict(self) -> dict:
        """Return a plain dictionary representation (useful for serialization)."""
        return {
            "hash": self.hash,
            "message": self.message,
            "author": self.author,
            "date": self.date,
            "version_type": self._version_type,
            "custom_message": self._custom_message,
            "processed": self._processed,
        }
