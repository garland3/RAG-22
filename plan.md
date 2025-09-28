# RAG Ingestion & Retrieval Plan

## 1. Objectives
- Build a modular Retrieval-Augmented Generation (RAG) ingestion pipeline.
- Use MongoDB with vector search (Atlas Vector Search or local MongoDB 7.x with vector indexing) for storage of metadata + embeddings.
- Support filesystem traversal via a Python CLI to ingest heterogeneous document types (initial: text, Markdown, PDFs; extensible to images/audio later).
- Uniform ingestion interface with specialized subclass handlers per modality.
- Generate embeddings via Jina AI (`jina-embeddings-v3` with `text-matching` task) using simple `requests` HTTP calls (no heavy SDK dependency).
- Use Celery for asynchronous job queuing (batch embedding calls, large file splits, PDF parsing) to avoid blocking the CLI.
- Provide a clear separation between: collection (scan), parsing/splitting, embedding, persistence, and indexing.

## 2. High-Level Architecture (Multimodal & Hierarchical)
```
cli/
  ingest.py          (entrypoint - supports multimodal ingestion)
  search.py          (multimodal search and retrieval)
core/
  scanner.py         (filesystem traversal with multimodal support)
  loader.py          (loads multimodal content: text, images, videos, audio)
  splitter.py        (content-aware splitting strategies per modality)
  models.py          (Pydantic models: RawUnit, MacroUnit, DocumentMeta, etc.)
  registry.py        (maps file extensions → multimodal handler classes)
  embeddings.py      (multi-embedding client: text, vision, audio, code)
  llm_client.py      (LLM integration for summarization tasks)
  storage.py         (MongoDB client for 5 collections + vector indexes)
  pipeline.py        (orchestrates: extract → summarize → embed → hierarchize)
  hierarchy.py       (builds recursive macro unit structures)
handlers/
  base.py            (BaseIngestHandler with multimodal interface)
  text_handler.py    (text and markdown processing)
  pdf_handler.py     (PDF with text/image extraction)
  image_handler.py   (image analysis and description)
  video_handler.py   (video processing with frame/audio extraction)
  audio_handler.py   (audio transcription and analysis)
  code_handler.py    (source code analysis and documentation)
  data_handler.py    (CSV, JSON, structured data processing)
summarization/
  raw_summarizer.py  (generates content_summary for raw units)
  macro_summarizer.py (generates hierarchical summaries)
  doc_summarizer.py  (document-level summary generation)
workers/
  tasks.py           (Celery: embed, summarize, hierarchize, cross-modal analysis)
  embedding_tasks.py (multimodal embedding generation)
  summary_tasks.py   (LLM summarization tasks)
  hierarchy_tasks.py (recursive macro unit generation)
config/
  settings.py        (multimodal pipeline configuration)
  logging.py         (structured logging with task tracking)
  llm_config.py      (LLM provider configurations)
scripts/
  run_mongo.sh       (MongoDB with vector search support)
  run_redis.sh       (Redis for Celery task queue)
  dev_stack.sh       (complete development environment)
.env.example
plan.md
Datastructureingest.md
```

## 3. Data Model (Multimodal & Hierarchical)

Based on the comprehensive data structure in `Datastructureingest.md`, the system uses five MongoDB collections:

### Collection 1: RawUnit (Individual Content Units)
- Supports multiple content types: text, image, video, audio, data_blob, code, table, diagram
- Each unit has an LLM-generated summary (`content_summary`)
- Multiple embedding types supported (text, vision, multimodal, audio, code)
- Flexible metadata per content type (e.g., image resolution, video duration)
- Custom extensible metadata (key-value pairs)
- Quality metrics and source tracking

### Collection 2: MacroUnit (Hierarchical Summaries)
- Hierarchical summaries of multiple raw units (can span content types)
- Recursive structure with levels (1=first level above raw, 2=second level, etc.)
- Multi-modal support with per-content-type summaries
- Context summaries and key concepts extraction
- Cross-modal relationship tracking
- Quality metrics (coherence, coverage, multimodal alignment)

### Collection 3: DocumentMeta (Document-level Information)
- Enhanced document metadata with multimodal support
- Content composition analysis (types and distribution)
- Document-level summaries per modality
- Navigation aids (table of contents, key topics, content timeline)
- Custom extensible metadata for domain-specific needs

### Collection 4: EmbeddingIndex (Embedding Management)
- Separate collection for managing different embedding types and models
- Supports multiple models and versions per content type
- Embedding metadata and quality tracking
- Performance metrics (generation time, confidence scores)

### Collection 5: RetrievalLog (Performance Tracking)
- Tracks retrieval performance across different query types and modalities
- Multimodal retrieval strategy tracking
- User feedback and follow-up query analysis
- Cross-modal match tracking

## 4. LLM Endpoint Requirements for Summarization

The system requires LLM integration for generating summaries at multiple levels:

### Content Summarization Endpoints
- **Raw Unit Summarization**: Generate `content_summary` for each individual content unit
  - Input: Raw content (text, image description, video transcript, etc.)
  - Output: Concise summary of the content unit
  - Models: Support for various LLMs (OpenAI GPT, Anthropic Claude, local models)

### Hierarchical Summarization Pipeline
- **Macro Unit Summarization**: Generate hierarchical summaries by combining child units
  - Input: Collection of raw unit summaries or child macro unit summaries
  - Output: `macro_summary`, `context_summary`, and `key_concepts`
  - Recursive processing: Level 1 (raw units) → Level 2 (macro units) → Level N

### Document-Level Summarization
- **Document Summary Generation**: Create comprehensive document-level summaries
  - Input: All macro units and raw units from a document
  - Output: `document_summary` and modality-specific summaries
  - Cross-modal analysis for multimodal documents

### LLM Configuration
```python
# Environment variables for LLM endpoints
LLM_PROVIDER=openai|anthropic|local|ollama
LLM_MODEL=gpt-4|claude-3|llama2|mistral
LLM_API_KEY=<api_key>
LLM_BASE_URL=<endpoint_url>  # For local/custom deployments
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.1  # Low temperature for consistent summaries
```

### Summarization Tasks (Celery)
- `summarize_raw_unit(unit_id)`: Generate summary for individual content unit
- `summarize_macro_unit(macro_unit_id)`: Generate hierarchical summary
- `summarize_document(document_id)`: Generate document-level summary
- `batch_summarize_units(unit_ids)`: Batch processing for efficiency

### Quality Control
- Summary confidence scoring
- Content completeness validation
- Multimodal alignment assessment
- Retry mechanisms for failed summarizations

## 6. MongoDB Schema Strategy (5 Collections)

### Collection: raw_units
```javascript
{
  _id: ObjectId,
  content_type: "text|image|video|audio|data_blob|code|table|diagram",
  content_data: String|Object,
  content_summary: String,  // LLM-generated
  document_id: String,
  unit_index: Number,
  embeddings: {
    "text": [Float],
    "vision": [Float],
    "multimodal": [Float],
    // ... other embedding types
  },
  custom_metadata: Object,
  // ... other fields from RawUnit model
}
```

### Collection: macro_units
```javascript
{
  _id: ObjectId,
  macro_summary: String,    // LLM-generated
  context_summary: String,  // LLM-generated
  key_concepts: [String],   // LLM-extracted
  level: Number,            // 1, 2, 3... (hierarchy depth)
  document_id: String,
  parent_macro_id: String|null,
  child_macro_ids: [String],
  raw_unit_ids: [String],
  embeddings: Object,
  // ... other fields from MacroUnit model
}
```

### Collection: document_meta
```javascript
{
  _id: ObjectId,
  filename: String,
  document_summary: String,     // LLM-generated
  modality_summaries: Object,   // LLM-generated per content type
  content_types: [String],
  total_units: Number,
  total_macro_units: Number,
  max_hierarchy_level: Number,
  custom_metadata: Object,      // Extensible key-value pairs
  // ... other fields from DocumentMeta model
}
```

### Collection: embedding_index
```javascript
{
  _id: ObjectId,
  content_id: String,           // Points to raw_unit or macro_unit
  content_type: "text|image|video|...",
  embedding_type: "text|vision|multimodal|...",
  embedding_vector: [Float],
  embedding_model: String,
  model_version: String,
  // ... other fields from EmbeddingIndex model
}
```

### Collection: retrieval_logs
```javascript
{
  _id: ObjectId,
  query: String,
  query_type: String,
  query_modalities: [String],
  raw_units_used: [String],
  macro_units_used: [String],
  retrieval_strategy: String,
  response_quality: Float,
  // ... other fields from RetrievalLog model
}
```

### Indexes Strategy
```javascript
// raw_units collection
db.raw_units.createIndex({ "document_id": 1, "unit_index": 1 })
db.raw_units.createIndex({ "content_type": 1 })
db.raw_units.createIndex({ "embeddings.text": "vector" })      // Vector search
db.raw_units.createIndex({ "embeddings.vision": "vector" })    // Vision search
db.raw_units.createIndex({ "custom_metadata": 1 })             // Flexible metadata queries

// macro_units collection
db.macro_units.createIndex({ "document_id": 1, "level": 1 })
db.macro_units.createIndex({ "parent_macro_id": 1 })
db.macro_units.createIndex({ "embeddings.text": "vector" })
db.macro_units.createIndex({ "embeddings.multimodal": "vector" })

// document_meta collection
db.document_meta.createIndex({ "filename": 1 }, { unique: true })
db.document_meta.createIndex({ "content_types": 1 })
db.document_meta.createIndex({ "custom_metadata": 1 })

// embedding_index collection
db.embedding_index.createIndex({ "content_id": 1, "embedding_type": 1 })
db.embedding_index.createIndex({ "embedding_vector": "vector" })
db.embedding_index.createIndex({ "embedding_model": 1, "model_version": 1 })

// retrieval_logs collection
db.retrieval_logs.createIndex({ "timestamp": -1 })
db.retrieval_logs.createIndex({ "query_type": 1, "response_quality": -1 })
```

## 7. Enhanced Pipeline Flow (Multimodal + Hierarchical)

### Stage 1: Content Extraction & Raw Unit Creation
1. **Scan & Load**: Detect file types and extract content using appropriate handlers
2. **Content Splitting**: Split content into logical units based on modality:
   - Text: paragraphs, sections, code blocks
   - Images: individual images with metadata extraction
   - Videos: scenes/frames with audio transcription
   - Audio: segments with speech-to-text
   - Data: tables, records, structured elements
3. **Raw Unit Creation**: Create RawUnit documents (without summaries yet)

### Stage 2: LLM Summarization Pipeline
1. **Raw Unit Summarization**:
   - `summarize_raw_unit(unit_id)` tasks for each unit
   - Generate `content_summary` using LLM
   - Update quality scores and confidence metrics
2. **Cross-Modal Analysis**: Link related units across modalities
3. **Batch Processing**: Group similar content types for efficiency

### Stage 3: Embedding Generation
1. **Multi-Modal Embedding**: Generate embeddings per content type:
   - Text content → text embeddings
   - Image descriptions → vision embeddings
   - Combined content → multimodal embeddings
   - Code → code-specific embeddings
2. **Batch Embedding Tasks**: `embed_batch_multimodal(unit_ids, embedding_types)`
3. **Storage**: Save to both RawUnit.embeddings and separate EmbeddingIndex collection

### Stage 4: Hierarchical Summarization (Recursive)
1. **Level 1 Macro Units**:
   - Group related raw units (3-7 units per macro)
   - `summarize_macro_unit(macro_id, raw_unit_ids)`
   - Generate hierarchical summaries, context, and key concepts
2. **Level N Macro Units** (Recursive):
   - Group Level N-1 macro units
   - Continue until document has manageable top-level units
   - Track parent-child relationships
3. **Cross-Modal Coherence**: Analyze alignment between modalities

### Stage 5: Document-Level Processing
1. **Document Summary**: `summarize_document(document_id)`
   - Aggregate all macro units into document summary
   - Generate modality-specific summaries
   - Extract key topics and create table of contents
2. **Navigation Aids**: Build content timeline, cross-references
3. **Quality Assessment**: Document completeness and coherence metrics

### Stage 6: Indexing & Optimization
1. **Vector Index Creation**: Ensure all embedding types are indexed
2. **Metadata Indexing**: Index custom metadata for flexible queries
3. **Performance Optimization**: Optimize index strategies based on usage patterns

### Pipeline Orchestration (Celery Tasks)
- `process_document_pipeline(document_path)`: Master orchestration task
- `extract_and_create_raw_units(document_id)`: Stage 1
- `batch_summarize_raw_units(document_id)`: Stage 2
- `batch_embed_units(document_id, embedding_types)`: Stage 3
- `build_hierarchy_recursive(document_id, max_level=5)`: Stage 4
- `finalize_document(document_id)`: Stage 5-6

### Failure Handling & Retry Logic
- Exponential backoff for LLM API failures
- Partial processing recovery (resume from failed stage)
- Quality validation at each stage
- Dead letter queues for persistent failures

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

## 9. Configuration & Environment (Enhanced)
`.env` keys:
```bash
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ragdb_multimodal

# Embedding Configuration
JINA_API_KEY=<your_jina_api_key>
EMBED_MODEL=jina-embeddings-v3
EMBED_TASK=text-matching
VISION_EMBED_MODEL=jina-clip-v1  # For image embeddings
CODE_EMBED_MODEL=jina-embeddings-v3  # For code embeddings

# LLM Configuration for Summarization
LLM_PROVIDER=openai  # openai|anthropic|local|ollama
LLM_MODEL=gpt-4-turbo
LLM_API_KEY=<your_llm_api_key>
LLM_BASE_URL=https://api.openai.com/v1  # For custom deployments
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.1
LLM_TIMEOUT=60  # seconds

# Alternative LLM Configurations
ANTHROPIC_API_KEY=<anthropic_key>
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama

# Celery Configuration
BROKER_URL=redis://redis:6379/0
RESULT_BACKEND=redis://redis:6379/1

# Processing Configuration
CHUNK_MAX_TOKENS=512
MAX_HIERARCHY_LEVELS=5
MACRO_UNIT_SIZE_MIN=3  # Minimum raw units per macro
MACRO_UNIT_SIZE_MAX=7  # Maximum raw units per macro
BATCH_SIZE_EMBEDDING=32
BATCH_SIZE_SUMMARIZATION=16

# Multimodal Processing
ENABLE_IMAGE_PROCESSING=true
ENABLE_VIDEO_PROCESSING=true
ENABLE_AUDIO_PROCESSING=true
VIDEO_FRAME_EXTRACTION_FPS=1  # Frames per second for video analysis
AUDIO_TRANSCRIPTION_MODEL=whisper-1

# Quality Control
MIN_CONTENT_QUALITY_SCORE=0.6
MIN_SUMMARY_CONFIDENCE=0.7
ENABLE_CROSS_MODAL_VALIDATION=true

# Performance
MAX_CONCURRENT_LLM_REQUESTS=5
MAX_CONCURRENT_EMBED_REQUESTS=10
REQUEST_RETRY_MAX_ATTEMPTS=3
REQUEST_RETRY_BACKOFF_FACTOR=2
```

Provide `.env.example` with placeholders and detailed comments.

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

## 17. Milestones & Phases (Updated for Multimodal + Hierarchical)

### Phase 1 (Foundation + Basic Text Processing):
- Project scaffolding with multimodal architecture
- MongoDB + Redis docker scripts with vector search support
- Core Pydantic models (RawUnit, MacroUnit, DocumentMeta, etc.)
- LLM client integration (OpenAI/Anthropic/local)
- Basic text handler with summarization
- Simple CLI ingest for .txt/.md with hierarchical processing

### Phase 2 (Multimodal Content Support):
- Image handler with vision embeddings
- PDF handler with text/image extraction
- Video handler with frame extraction and audio transcription
- Audio handler with speech-to-text
- Code handler with syntax analysis
- Data handler for CSV/JSON structured content

### Phase 3 (Hierarchical Summarization Pipeline):
- Recursive macro unit generation algorithms
- LLM-powered summarization at all levels
- Cross-modal relationship detection
- Quality assessment and validation
- Celery task orchestration for complex pipelines

### Phase 4 (Advanced Retrieval):
- Multimodal vector search across embedding types
- Hierarchical search (raw units vs macro units)
- Cross-modal query understanding
- Search result ranking and relevance scoring
- CLI command: `search "query" --modality image,text --level macro`

### Phase 5 (Performance & Analytics):
- Retrieval performance tracking and optimization
- A/B testing for different summarization strategies
- Usage analytics and query pattern analysis
- Automated quality improvement recommendations
- Performance monitoring and alerting

### Phase 6 (Production Readiness):
- Comprehensive test coverage (≥ 80%)
- Error handling and recovery mechanisms
- Logging and observability improvements
- Security auditing and compliance
- Documentation and deployment guides

### Phase 7 (Advanced Features):
- Hybrid search (BM25 + vector + metadata)
- Real-time incremental updates
- Web API wrapper (FastAPI) with multimodal endpoints
- Advanced analytics dashboard
- Integration with external systems (Slack, Discord, etc.)

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
