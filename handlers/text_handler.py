from .base import BaseIngestHandler
from core.models import Chunk, Document
from pathlib import Path
from typing import List
from config.settings import settings


class TextHandler(BaseIngestHandler):
    def can_handle(self, modality: str) -> bool:
        return modality in ["text", "markdown"]

    def load_and_split(self, file_path: Path, document: Document) -> List[Chunk]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        text_chunks = self._simple_text_split(content, max_tokens=settings.chunk_max_tokens)
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = Chunk(
                document_id=document.id,
                index=i,
                content=chunk_text,
                metadata={"token_count": len(chunk_text) // 4}  # rough estimate
            )
            chunks.append(chunk)
        return chunks