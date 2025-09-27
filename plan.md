# RAG Ingestion & Retrieval Plan

## 1. Objectives
- Build a modular Retrieval-Augmented Generation (RAG) ingestion pipeline.
- Use MongoDB with vector search (Atlas Vector Search or local MongoDB 7.x with vector indexing) for storage of metadata + embeddings.
- Support filesystem traversal via a Python CLI to ingest heterogeneous document types (initial: text, Markdown, PDFs; extensible to images/audio later).
- Uniform ingestion interface with specialized subclass handlers per modality.
- Generate embeddings via Jina AI (`jina-embeddings-v3` with `text-matching` task) using simple `requests` HTTP calls (no heavy SDK dependency).
- Use Celery for asynchronous job queuing (batch embedding calls, large file splits, PDF parsing) to avoid blocking the CLI.
- Provide a clear separation between: collection (scan), parsing/splitting, embedding, persistence, and indexing.

## 2. High-Level Architecture
```
cli/
  ingest.py (entrypoint)
core/
  scanner.py         (filesystem traversal abstraction)
  loader.py          (loads raw file content)
  splitter.py        (document chunking strategies)
  models.py          (Pydantic data models / dataclasses for Document / Chunk)
  registry.py        (maps file extensions → handler classes)
  embeddings.py      (Jina embedding client)
  storage.py         (MongoDB client + CRUD + ensure indexes)
  pipeline.py        (orchestrates stages; can enqueue Celery tasks)
handlers/
  base.py            (BaseIngestHandler interface)
  text_handler.py
  markdown_handler.py
  pdf_handler.py
  # future: image_handler.py, audio_handler.py
workers/
  tasks.py           (Celery tasks: embed_chunks, persist_chunks, etc.)
config/
  settings.py        (environment loading, e.g., python-dotenv)
  logging.py         (structured logging setup)
scripts/
  run_mongo.sh       (docker compose or single-run script)
  seed_sample.sh     (optional: seed test docs)
.env.example
plan.md
```

## 3. Data Model (Conceptual)
Document:
- id (UUID)
- source_path
- modality (text|markdown|pdf|...)
- raw_text (optional for large docs -> maybe stored separately or not at all after chunking)
- metadata (dict: size, created_at, language, checksum)

Chunk:
- id (UUID)
- document_id (FK)
- index (sequence number)
- content (text segment)
- embedding (float[dim])
- metadata (length, page_number (if PDF), lang, etc.)

EmbeddingRequestBatch:
- model
- task
- inputs: list[str]

## 4. MongoDB Schema Strategy
- Collection: documents (metadata only; optionally limited text excerpt)
- Collection: chunks (with embedding vector field e.g. `embedding: [float]`)
- Indexes:
  - documents: `{ source_path: 1 }`, optional TTL for temp docs
  - chunks: vector index on `embedding` (MongoDB 7+ `vector` index spec) + compound `{ document_id: 1, index: 1 }`
- Possible future: Collection: ingestion_jobs (status tracking)

## 5. Embedding Flow
1. Chunks produced (no embedding yet).
2. Batch Celery task groups embeddings in size N (tune: 32–128 depending on token limits) and calls Jina endpoint.
3. Store embeddings back into MongoDB. Mark chunk status = embedded.
4. Failures retried with exponential backoff.

## 6. Chunking Strategy
- Plain text / Markdown: recursive split by paragraphs → sentences → token length threshold (~512 tokens) using a simple heuristic first (can swap in tiktoken or nltk later).
- PDF: extract text per page (use `pypdf` or `pdfminer.six`), then apply same text splitter.
- Store original page reference.

## 7. CLI Functional Requirements
Commands (initial):
- `scan` : Dry-run list of files that would be ingested (filters, size limits, extensions).
- `ingest PATH` : Traverse path, process new/changed files, enqueue embedding tasks.
- `reembed --filter modality=markdown` : Recompute embeddings for selected subset.
- `status` : Show queue depth, recent failures, number of embedded vs pending.
- `preview DOC_ID` : Show doc + first N chunks.

Options:
- `--include-ext .md,.pdf,.txt`
- `--max-size-mb 20`
- `--follow-symlinks` (default false)
- `--ignore "node_modules,.git,.venv"`

## 8. Celery + Worker Setup
- Broker: Redis (simplest) or RabbitMQ (if already in stack). (Assumption: Redis; adjust if not desired.)
- Tasks:
  - `parse_and_split(document_id)` (maybe synchronous in pipeline, optional task)
  - `embed_chunk_batch(chunk_id_list)`
  - `backfill_missing_embeddings()`
- Rate limiting embedding calls (Jina API fairness) using Celery task rate limit (e.g., 5 req/sec initially).

## 9. Configuration & Environment
`.env` keys:
- `MONGO_URI=`
- `MONGO_DB=ragdb`
- `JINA_API_KEY=` (never hardcode secret; provided example replaced in repo with placeholder)
- `EMBED_MODEL=jina-embeddings-v3`
- `EMBED_TASK=text-matching`
- `BROKER_URL=redis://redis:6379/0`
- `RESULT_BACKEND=redis://redis:6379/1`
- `CHUNK_MAX_TOKENS=512`

Provide `.env.example` with placeholders.

## 10. Security / Secret Hygiene
- Remove real key from instructions; replace with placeholder in repo.
- Use dotenv; never print full keys in logs.
- Add `.env` to `.gitignore`.

## 11. Scripts Folder (`scripts/`)
- `mongo_up.sh`: run MongoDB with vector support (Docker) — choose version 7.x.
- `redis_up.sh`: run Redis for Celery broker (optional combine with docker compose).
- `dev_stack.sh`: bring up both.
- `lint.sh`, `format.sh` (optional improvement stage).

## 12. Retrieval (Future Outline)
- Add semantic search function: given query -> embed -> vector search in `chunks` (top-k) -> aggregate -> return contexts.
- Add hybrid search (BM25 + vector) later; can store full-text index on chunks.content.

## 13. Incremental Ingestion Logic
- Compute file checksum (e.g., SHA256) + size + mtime.
- If unchanged (same checksum) skip re-processing.
- If changed: mark old chunks as superseded (soft delete flag) and insert new set.

## 14. Logging & Observability
- Structured logs (JSON) for workers.
- Log levels: INFO for ingestion progress, DEBUG for chunk splits, WARN for API retries.
- Basic metrics (optional future): count of embeddings/sec, failed tasks.

## 15. Testing Strategy
- Unit tests: splitter, registry, embedding client (mock HTTP), storage layer (use test DB or mongomock if vector index not needed), checksum logic.
- Integration smoke test: ingest small fixture directory containing 1 .txt, 1 .md, 1 .pdf.
- CLI test: use `pytest` + `click.testing` (if using Click for CLI).

## 16. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Jina API rate limits | Slow ingestion | Batch + backoff + rate limit tasks |
| Large PDFs memory | Worker OOM | Page-wise streaming + incremental chunking |
| Vector index unsupported locally | Retrieval fails | Pin MongoDB 7.x image; verify index creation early |
| Secret leakage | Security | Use placeholders, .env ignored |
| Duplicate ingestion | Bloat | Checksum + uniqueness constraints |

## 17. Milestones & Phases
Phase 1 (Core Ingestion):
- Project scaffolding, config, scripts
- Mongo + Redis docker scripts
- Core models + storage + embedding client (sync)
- Simple CLI ingest for .txt/.md

Phase 2 (Async & PDFs):
- Add Celery worker + tasks
- Add PDF handler + chunking
- Add incremental ingestion (checksum)

Phase 3 (Search Prototype):
- Add vector search query function
- Simple retrieval CLI command `search "query" --k 5`

Phase 4 (Hardening):
- Logging improvements
- Tests coverage ≥ 70%
- Re-embedding & status commands

Phase 5 (Extensions / Future):
- Additional modalities
- Hybrid search
- Web API wrapper (FastAPI) for retrieval

## 18. Acceptance Criteria
- Running `scripts/dev_stack.sh` launches Mongo (vector) + Redis.
- `python -m cli.ingest ./fixtures` ingests sample set and enqueues embeddings.
- After workers finish, `chunks` collection has embeddings (vector length matches model spec).
- Re-running ingest on unchanged files results in zero new chunks.
- A query embedding call returns top-k chunk results (Phase 3+).

## 19. Immediate Next Actions (Implementation Order)
1. Add `.gitignore`, `.env.example`.
2. Add `scripts/` with Mongo + Redis startup.
3. Add basic package structure + `pyproject.toml` (if Python project not yet scaffolded).
4. Implement models + storage + embedding client (sync first).
5. Implement scanner + registry + basic text handlers.
6. Implement CLI (Click or argparse) with ingest + scan.
7. Add PDF parsing + splitting.
8. Introduce Celery tasks for embedding.
9. Add vector search helper.
10. Add tests + fixtures.

## 20. Open Questions / Assumptions
- Assumption: Use Redis as Celery broker (confirm). If not, adapt to RabbitMQ.
- Assumption: Python version ≥ 3.10.
- Need confirmation on preferred CLI framework (Click vs Typer vs argparse). Default: Typer for DX.
- Need decision whether to store full raw text long-term or only chunks.

---
This plan is designed to be iterative; we can trim or expand based on priorities you set next.
