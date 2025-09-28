from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.models import Chunk, Document
from pathlib import Path
import re
from datetime import datetime


class BaseIngestHandler(ABC):
    @abstractmethod
    def can_handle(self, modality: str) -> bool:
        pass

    @abstractmethod
    def load_and_split(self, file_path: Path, document: Document) -> List[Chunk]:
        """Load file content and split into chunks."""
        pass

    def _simple_text_split(self, text: str, max_tokens: int = 512) -> List[str]:
        """Simple splitter: split by paragraphs, then by sentences, respecting max_tokens."""
        # Rough token approximation: 1 token ~ 4 chars
        max_chars = max_tokens * 4
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # If para itself is too long, split by sentences
                sentences = para.split('. ')
                for sent in sentences:
                    if len(current_chunk) + len(sent) > max_chars:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent
                    else:
                        current_chunk += sent + '. '
            else:
                current_chunk += para + '\n\n'
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract title, authors, date from text."""
        lines = text.split('\n')[:20]  # First 20 lines
        metadata = {}

        # Title: first non-empty line, or # heading in markdown
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('#'):
                    metadata['title'] = line.lstrip('#').strip()
                    break
                else:
                    metadata['title'] = line
                    break

        # Authors: look for patterns like "by", "authors", "written by"
        text_lower = text.lower()[:1000]  # first 1000 chars
        author_patterns = [
            r'by\s+([^\n\r]+)',
            r'authors?\s*:\s*([^\n\r]+)',
            r'written by\s+([^\n\r]+)'
        ]
        for pattern in author_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                authors_str = match.group(1).strip()
                # Split by common separators
                authors = re.split(r'[,&]', authors_str)
                metadata['authors'] = [a.strip() for a in authors if a.strip()]
                break

        # Date: look for YYYY-MM-DD, MM/DD/YYYY, etc.
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # 2023-10-01
            r'\b(\d{2}/\d{2}/\d{4})\b',  # 10/01/2023
            r'\b(\d{4}/\d{2}/\d{2})\b',  # 2023/10/01
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse
                    if '-' in date_str:
                        parsed = datetime.strptime(date_str, '%Y-%m-%d')
                    elif '/' in date_str:
                        if len(date_str.split('/')[0]) == 4:
                            parsed = datetime.strptime(date_str, '%Y/%m/%d')
                        else:
                            parsed = datetime.strptime(date_str, '%m/%d/%Y')
                    metadata['date'] = parsed.isoformat()
                    break
                except ValueError:
                    continue

        return metadata

    def _simple_text_split(self, text: str, max_tokens: int = 512) -> List[str]: