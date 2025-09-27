```python
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import uuid

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DATA_BLOB = "data_blob"  # CSV, JSON, structured data
    CODE = "code"
    TABLE = "table"
    DIAGRAM = "diagram"

class EmbeddingType(Enum):
    TEXT = "text"           # Standard text embeddings
    VISION = "vision"       # Image/video embeddings (CLIP, etc.)
    MULTIMODAL = "multimodal"  # Combined text+vision
    AUDIO = "audio"         # Audio embeddings
    CODE = "code"           # Code-specific embeddings
    CUSTOM = "custom"       # Domain-specific embeddings

# Collection 1: Raw Units (formerly Raw Chunks)
class RawUnit(BaseModel):
    """Individual content units with their summaries - text, image, video, data, etc."""
    _id: str = str(uuid.uuid4())
    
    # Core Content
    content_type: ContentType
    content_data: Union[str, Dict[str, Any]]  # Text string OR structured data
    content_summary: str                      # LLM-generated summary of this unit
    
    # File/Storage Information
    file_path: Optional[str] = None          # Path to actual file (for large media)
    file_size_bytes: Optional[int] = None
    file_format: Optional[str] = None        # jpg, mp4, csv, etc.
    
    # Content-specific metadata
    content_metadata: Dict[str, Any] = {}    # Flexible metadata per content type
    # Examples:
    # - Image: {"resolution": "1920x1080", "format": "jpg", "objects_detected": [...]}
    # - Video: {"duration_seconds": 120, "fps": 30, "transcript": "..."}
    # - Audio: {"duration_seconds": 45, "format": "mp3", "transcript": "..."}
    # - Data: {"rows": 1000, "columns": 15, "schema": {...}}
    # - Code: {"language": "python", "function_names": [...], "complexity": 5}
    
    # Generic extensible metadata (your key-value requirement)
    custom_metadata: Dict[str, Any] = {}     # User-defined key-value pairs
    
    # Document hierarchy
    document_id: str                         # Parent document ID
    unit_index: int                          # Position in document (0, 1, 2...)
    
    # Embeddings (multiple types possible)
    embeddings: Dict[EmbeddingType, List[float]] = {}
    # Examples:
    # - Text unit: {EmbeddingType.TEXT: [...]}
    # - Image unit: {EmbeddingType.VISION: [...], EmbeddingType.TEXT: [...]}  # Image + caption
    # - Video unit: {EmbeddingType.VISION: [...], EmbeddingType.AUDIO: [...], EmbeddingType.TEXT: [...]}
    
    # Hierarchy links
    macro_unit_ids: List[str] = []           # Which macro units contain this
    
    # Cross-references
    related_unit_ids: List[str] = []         # Related units (same topic, different modality)
    reference_tags: List[str] = []           # User-defined tags for grouping
    
    # Source tracking
    source_file: str
    source_location: Optional[Dict[str, Any]] = None  # Page, timestamp, coordinates, etc.
    extraction_method: str                   # How this unit was extracted
    
    # Quality metrics
    content_quality_score: Optional[float] = None  # Automated quality assessment
    summary_confidence: Optional[float] = None      # How confident the summary is
    
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

# Collection 2: Macro Units (Hierarchical Summaries)
class MacroUnit(BaseModel):
    """Hierarchical summaries of multiple smaller units - can span multiple content types"""
    _id: str = str(uuid.uuid4())
    
    # Content
    macro_summary: str                       # Summary of child units
    context_summary: str                     # Broader context explanation
    key_concepts: List[str]                  # Extracted key concepts
    
    # Multimodal support
    content_types_included: List[ContentType]  # What types of content this covers
    modality_summary: Dict[ContentType, str] = {}  # Summaries per content type
    # Example: {ContentType.TEXT: "Technical specs...", ContentType.IMAGE: "Diagrams show..."}
    
    # Hierarchy
    level: int                               # 1=first level above raw, 2=second level, etc.
    document_id: str                         # Parent document
    parent_macro_id: Optional[str] = None    # Parent macro unit (if exists)
    child_macro_ids: List[str] = []          # Child macro units
    raw_unit_ids: List[str] = []             # Raw units directly under this macro
    
    # Aggregated metadata
    unit_count: int                          # How many raw units this covers
    total_content_size: int                  # Total size (chars for text, bytes for media)
    start_unit_index: int                    # First unit covered
    end_unit_index: int                      # Last unit covered
    
    # Generic extensible metadata
    custom_metadata: Dict[str, Any] = {}     # Aggregated or custom metadata
    
    # Embeddings (combined from child units)
    embeddings: Dict[EmbeddingType, List[float]] = {}
    
    # Cross-modal relationships
    modal_connections: Dict[str, Any] = {}   # How different modalities relate
    # Example: {"image_text_alignment": 0.85, "video_audio_sync": True}
    
    # Quality metrics
    coherence_score: float                   # How well units fit together
    coverage_score: float                    # How well summary covers content
    multimodal_alignment: Optional[float] = None  # How well modalities align
    
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

# Collection 3: Document Metadata (Enhanced)
class DocumentMeta(BaseModel):
    """Document-level information and navigation - supports multimodal documents"""
    _id: str = str(uuid.uuid4())
    
    # Document info
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    document_type: str                       # pdf, html, video, dataset, etc.
    
    # Generic extensible metadata (your key-value requirement)
    custom_metadata: Dict[str, Any] = {}
    # Examples:
    # - {"department": "engineering", "project": "alpha", "confidentiality": "internal"}
    # - {"course": "CS101", "semester": "fall2024", "assignment_type": "lab"}
    # - {"patient_id": "12345", "study_type": "mri", "date_of_scan": "2024-01-15"}
    
    # Content composition
    content_types: List[ContentType]         # What types of content in this doc
    content_distribution: Dict[ContentType, int] = {}  # Count per content type
    
    # Processing metadata
    total_units: int
    total_macro_units: int
    max_hierarchy_level: int
    
    # Multimodal summaries
    document_summary: str                    # Highest-level summary
    modality_summaries: Dict[ContentType, str] = {}  # Summary per content type
    
    # Embeddings (document-level)
    embeddings: Dict[EmbeddingType, List[float]] = {}
    
    # Navigation aids
    table_of_contents: List[Dict[str, Any]] = []  # Structure of the document
    key_topics: List[str] = []               # Main topics covered
    content_timeline: Optional[List[Dict]] = None  # For time-based content (videos, etc.)
    
    # Cross-references
    related_documents: List[str] = []        # Related document IDs
    document_tags: List[str] = []            # User-defined tags
    
    # Processing info
    processing_pipeline: Dict[str, Any] = {}  # How document was processed
    models_used: Dict[str, str] = {}         # Which models for each task
    processed_at: datetime
    
    # Quality and metrics
    processing_quality: Optional[float] = None
    content_completeness: Optional[float] = None
    
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

# Collection 4: Multimodal Embeddings Index (New!)
class EmbeddingIndex(BaseModel):
    """Separate collection for managing different embedding types and models"""
    _id: str = str(uuid.uuid4())
    
    # Reference
    content_id: str                          # Points to RawUnit or MacroUnit
    content_type: ContentType
    
    # Embedding details
    embedding_type: EmbeddingType
    embedding_vector: List[float]
    embedding_model: str                     # Model used to generate embedding
    model_version: str                       # Version of the model
    
    # Embedding metadata
    embedding_metadata: Dict[str, Any] = {}
    # Examples:
    # - {"image_preprocessing": "resized_224x224", "augmentations": ["rotate", "crop"]}
    # - {"text_preprocessing": "lowercased", "max_tokens": 512}
    # - {"audio_features": ["mfcc", "spectral"], "sample_rate": 16000}
    
    # Quality and performance
    embedding_confidence: Optional[float] = None
    generation_time_ms: Optional[float] = None
    
    created_at: datetime = datetime.now()

# Collection 5: Enhanced Retrieval Performance Tracking
class RetrievalLog(BaseModel):
    """Track what works for different query types and modalities"""
    _id: str = str(uuid.uuid4())
    
    # Query information
    query: str
    query_type: str                          # factual, analytical, creative, etc.
    query_modalities: List[ContentType] = [] # What content types user is looking for
    query_embeddings: Dict[EmbeddingType, List[float]] = {}
    
    # Context and metadata filters used
    metadata_filters: Dict[str, Any] = {}    # Custom metadata filters applied
    content_type_filters: List[ContentType] = []
    
    # What was retrieved
    raw_units_used: List[str] = []
    macro_units_used: List[str] = []
    retrieval_strategy: str                  # "raw_first", "macro_first", "multimodal", etc.
    
    # Multimodal retrieval details
    modality_weights: Dict[ContentType, float] = {}  # How different modalities were weighted
    cross_modal_matches: List[Dict] = []     # Cross-modal connections found
    
    # Performance
    response_quality: Optional[float] = None # User feedback or automated score
    retrieval_time_ms: float
    multimodal_coherence: Optional[float] = None
    
    # User interaction
    user_feedback: Optional[Dict[str, Any]] = None
    follow_up_queries: List[str] = []
    
    timestamp: datetime = datetime.now()


```