# RAG-22: Retrieval-Augmented Generation Ingestion Pipeline

A Python-based system for ingesting documents (text, Markdown, PDFs) into a vector database (MongoDB) with embeddings from Jina AI, enabling semantic search and RAG applications.

## Features

- **Multi-modal ingestion**: Supports text, Markdown, and PDF files
- **Incremental processing**: Skips unchanged files based on checksums
- **Async embedding**: Uses Celery for background processing of embeddings
- **Vector search**: Semantic similarity search over ingested content
- **Docker-based**: Easy setup with MongoDB and Redis containers
- **CLI interface**: Simple commands for scanning, ingesting, and searching

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- A Jina AI API key (get one at [jina.ai](https://jina.ai))

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/garland3/RAG-22.git
   cd RAG-22
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your JINA_API_KEY
   ```

## Configuration

Edit the `.env` file with your settings:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ragdb
JINA_API_KEY=your_jina_api_key_here
EMBED_MODEL=jina-embeddings-v3
EMBED_TASK=text-matching
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/1
CHUNK_MAX_TOKENS=512
LOG_LEVEL=INFO
```

## Usage

### 1. Start the services

Launch MongoDB (with vector search) and Redis:

```bash
./scripts/dev_stack.sh
```

This starts:
- MongoDB on `mongodb://localhost:27017`
- Redis on `redis://localhost:6379`

### 2. Start the workers (in a separate terminal)

Run Celery workers for async embedding:

```bash
./scripts/run_workers.sh
```

### 3. Scan files

Preview what files would be ingested:

```bash
python -m cli.ingest scan /path/to/your/documents --include-ext .txt .md .pdf
```

### 4. Ingest documents

Process and embed files:

```bash
python -m cli.ingest ingest /path/to/your/documents --include-ext .txt .md .pdf
```

Options:
- `--include-ext`: Specify file extensions (default: .txt, .md, .pdf)
- `--max-size-mb`: Skip files larger than this size
- `--dry-run`: Show what would be done without processing

### 5. Search content

Perform semantic search:

```bash
python -m cli.ingest search "your search query" --k 5
```

## Example Workflow

```bash
# Setup
./scripts/dev_stack.sh &
./scripts/run_workers.sh &

# Ingest sample files
python -m cli.ingest ingest fixtures/

# Search
python -m cli.ingest search "sample content"
```

## Architecture

- **Scanner**: Traverses directories and computes file checksums
- **Handlers**: Process different file types (text/markdown via simple splitting, PDFs via pypdf)
- **Storage**: MongoDB with vector indexes for chunks and embeddings
- **Embeddings**: Jina AI API for generating vector representations
- **Workers**: Celery tasks for batch embedding processing
- **CLI**: Typer-based interface for user interaction

## Development

### Running tests

```bash
pytest tests/
```

### Adding new handlers

1. Create a new handler class in `handlers/` inheriting from `BaseIngestHandler`
2. Implement `can_handle()` and `load_and_split()`
3. Register it in `handlers/__init__.py`

### Extending the CLI

Add new commands in `cli/ingest.py` using Typer decorators.

## Troubleshooting

- **MongoDB connection issues**: Ensure Docker containers are running (`docker ps`)
- **Embedding failures**: Check your Jina API key and network connectivity
- **Worker not processing**: Verify Redis is running and workers are started
- **Vector search not working**: Confirm MongoDB version supports vector indexes (7.x+)

## License

[Add your license here]