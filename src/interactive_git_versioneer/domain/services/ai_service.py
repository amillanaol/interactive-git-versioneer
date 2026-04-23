from abc import ABC, abstractmethod
from typing import Optional, Tuple


class AiService(ABC):
    @abstractmethod
    def generate_tag_message(
        self,
        commit_message: str,
        commit_diff: str,
        version_type: str,
        max_length: int = 72,
        locale: str = "es",
    ) -> Optional[str]:
        pass

    @abstractmethod
    def determine_version_type(
        self,
        commit_message: str,
        commit_diff: str,
    ) -> Tuple[str, str]:
        pass
