from .base import BaseIngestHandler
from core.models import Chunk, Document
from pathlib import Path
from typing import List
from pypdf import PdfReader
from config.settings import settings


class PDFHandler(BaseIngestHandler):
    def can_handle(self, modality: str) -> bool:
        return modality == "pdf"

    def load_and_split(self, file_path: Path, document: Document) -> List[Chunk]:
        reader = PdfReader(file_path)
        # Extract text from first 3 pages for metadata
        metadata_text = ""
        for page_num in range(min(3, len(reader.pages))):
            metadata_text += reader.pages[page_num].extract_text() + "\n"
        metadata = self.extract_metadata(metadata_text)
        document.metadata.update(metadata)

        chunks = []
        chunk_index = 0
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text.strip():
                continue
            # Split page text into chunks
            text_chunks = self._simple_text_split(text, max_tokens=settings.chunk_max_tokens)
            for chunk_text in text_chunks:
                chunk = Chunk(
                    document_id=document.id,
                    index=chunk_index,
                    content=chunk_text,
                    metadata={
                        "page_number": page_num + 1,
                        "token_count": len(chunk_text) // 4
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        return chunks