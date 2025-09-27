import pytest
from pathlib import Path
from core.scanner import FileScanner


def test_scanner(tmp_path):
    # Create test files
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello world")

    md_file = tmp_path / "test.md"
    md_file.write_text("# Title\nContent")

    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("fake pdf")  # Not real PDF, but for extension test

    scanner = FileScanner(include_exts=[".txt", ".md", ".pdf"])
    files = scanner.scan_directory(str(tmp_path))

    assert len(files) == 3
    paths = {f["path"] for f in files}
    assert str(txt_file) in paths
    assert str(md_file) in paths
    assert str(pdf_file) in paths