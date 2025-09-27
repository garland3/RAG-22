from abc import ABC, abstractmethod
from typing import List
from core.models import Chunk, Document
from pathlib import Path


class BaseIngestHandler(ABC):
    @abstractmethod
    def can_handle(self, modality: str) -> bool:
        pass

    @abstractmethod
    def load_and_split(self, file_path: Path, document: Document) -> List[Chunk]:
        """Load file content and split into chunks."""
        pass

    def _simple_text_split(self, text: str, max_tokens: int = 512) -> List[str]: