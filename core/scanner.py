import os
from pathlib import Path
from typing import List, Set, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class FileScanner:
    def __init__(self, include_exts: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None, max_size_mb: Optional[float] = None):
        self.include_exts = set(include_exts or [".txt", ".md", ".pdf"])
        self.exclude_patterns = exclude_patterns or []
        self.max_size_mb = max_size_mb

    def scan_directory(self, root_path: str) -> List[dict]:
        """Scan directory and return list of file info dicts."""
        root = Path(root_path)
        files = []
        for path in root.rglob("*"):
            if path.is_file() and self._should_include(path):
                info = self._get_file_info(path)
                if info:
                    files.append(info)
        return files

    def _should_include(self, path: Path) -> bool:
        # Check extension
        if path.suffix.lower() not in self.include_exts:
            return False
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in str(path):
                return False
        # Check size
        if self.max_size_mb and path.stat().st_size > self.max_size_mb * 1024 * 1024:
            return False
        return True

    def _get_file_info(self, path: Path) -> Optional[dict]:
        try:
            stat = path.stat()
            checksum = self._compute_checksum(path)
            return {
                "path": str(path),
                "size_bytes": stat.st_size,
                "checksum": checksum,
                "modality": self._infer_modality(path.suffix.lower())
            }
        except (OSError, IOError) as e:
            logger.warning(f"Failed to read file {path}: {e}")
            return None

    def _compute_checksum(self, path: Path) -> str:
        hash_sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _infer_modality(self, ext: str) -> str:
        mapping = {
            ".txt": "text",
            ".md": "markdown",
            ".pdf": "pdf"
        }
        return mapping.get(ext, "unknown")