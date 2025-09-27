from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_path: str
    modality: str  # e.g., 'text', 'markdown', 'pdf'
    checksum: str  # SHA256 of file content
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # e.g., language, encoding


class Chunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    index: int  # sequence number within document
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # e.g., page_number, token_count


class EmbeddingRequest(BaseModel):
    model: str
    task: str
    input: List[str]


class EmbeddingResponse(BaseModel):
    model: str
    data: List[List[float]]  # list of embeddings
    usage: Dict[str, Any] = Field(default_factory=dict)