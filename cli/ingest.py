import typer
from pathlib import Path
from typing import Optional, List
import logging
from core.scanner import FileScanner
from core.storage import Storage
from core.embeddings import JinaEmbeddingClient
from core.models import Document
from core.registry import registry
from config.settings import settings

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def scan(
    path: str = typer.Argument(..., help="Directory to scan"),
    include_ext: Optional[List[str]] = typer.Option(None, "--include-ext", help="File extensions to include"),
    max_size_mb: Optional[float] = typer.Option(None, "--max-size-mb", help="Max file size in MB")
):
    """Scan directory and list files that would be ingested."""
    scanner = FileScanner(include_exts=include_ext, max_size_mb=max_size_mb)
    files = scanner.scan_directory(path)
    typer.echo(f"Found {len(files)} files:")
    for f in files:
        typer.echo(f"  {f['path']} ({f['size_bytes']} bytes, {f['modality']})")


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Directory to ingest"),
    include_ext: Optional[List[str]] = typer.Option(None, "--include-ext", help="File extensions to include"),
    max_size_mb: Optional[float] = typer.Option(None, "--max-size-mb", help="Max file size in MB"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without doing it"),
    force: bool = typer.Option(False, "--force", help="Force re-processing of all files, even if unchanged")
):
    """Ingest files from directory."""
    storage = Storage(settings.mongo_uri, settings.mongo_db)
    embed_client = JinaEmbeddingClient(settings.jina_api_key, settings.embed_model, settings.embed_task)
    scanner = FileScanner(include_exts=include_ext, max_size_mb=max_size_mb)

    files = scanner.scan_directory(path)
    typer.echo(f"Processing {len(files)} files...")

    for file_info in files:
        file_path = Path(file_info["path"])
        existing = storage.get_document_by_path(file_info["path"])
        if not force and existing and existing.checksum == file_info["checksum"]:
            typer.echo(f"Skipping {file_path} (unchanged)")
            continue

        # If force or changed, delete old data
        if existing:
            typer.echo(f"Re-processing {file_path} (force or changed)")
            # Delete old chunks
            storage.chunks.delete_many({"document_id": existing.id})
            # Delete old document
            storage.documents.delete_one({"source_path": file_info["path"]})
        else:
            typer.echo(f"Processing {file_path} (new)")

        document = Document(
            source_path=file_info["path"],
            modality=file_info["modality"],
            checksum=file_info["checksum"],
            size_bytes=file_info["size_bytes"]
        )

        handler_class = registry.get_handler(file_info["modality"])
        if not handler_class:
            typer.echo(f"No handler for {file_info['modality']}: {file_path}")
            continue

        handler = handler_class()
        chunks = handler.load_and_split(file_path, document)

        if dry_run:
            typer.echo(f"Would ingest {file_path} -> {len(chunks)} chunks")
        else:
            storage.insert_document(document)
            chunk_ids = storage.insert_chunks(chunks)
            # Enqueue embedding task
            from workers.tasks import embed_chunk_batch
            embed_chunk_batch.delay(chunk_ids)
            typer.echo(f"Ingested {file_path} -> {len(chunks)} chunks (embedding queued)")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "--k", help="Number of results")
):
    """Search for similar content."""
    from core.search import VectorSearch
    searcher = VectorSearch()
    results = searcher.search(query, top_k)
    for i, res in enumerate(results, 1):
        typer.echo(f"{i}. {res['document_path']} ({res['modality']})")
        typer.echo(f"   {res['chunk_content'][:200]}...")
        typer.echo()


if __name__ == "__main__":
    app()