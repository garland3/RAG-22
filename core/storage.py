from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from typing import List, Optional
import logging
from .models import Document, Chunk

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.documents: Collection = self.db.documents
        self.chunks: Collection = self.db.chunks
        self._ensure_indexes()

    def _ensure_indexes(self):
        # Documents indexes
        self.documents.create_index([("source_path", ASCENDING)], unique=True)
        self.documents.create_index([("checksum", ASCENDING)])

        # Chunks indexes
        self.chunks.create_index([("document_id", ASCENDING), ("index", ASCENDING)])
        # Vector index for embeddings (MongoDB 7.x)
        try:
            self.chunks.create_index(
                [("embedding", "vector")],
                name="embedding_vector_index",
                vector={
                    "type": "knnVector",
                    "dimensions": 1024,  # Adjust based on Jina model; jina-embeddings-v3 is 1024 dims
                    "similarity": "cosine"
                }
            )
            logger.info("Vector index created on chunks.embedding")
        except Exception as e:
            logger.warning(f"Vector index creation failed (MongoDB version?): {e}")

    def insert_document(self, doc: Document) -> str:
        result = self.documents.insert_one(doc.dict())
        return str(result.inserted_id)

    def get_document_by_path(self, path: str) -> Optional[Document]:
        data = self.documents.find_one({"source_path": path})
        return Document(**data) if data else None

    def insert_chunks(self, chunks: List[Chunk]) -> List[str]:
        result = self.chunks.insert_many([c.dict() for c in chunks])
        return [str(id) for id in result.inserted_ids]

    def update_chunk_embedding(self, chunk_id: str, embedding: List[float]):
        from bson import ObjectId
        self.chunks.update_one(
            {"_id": ObjectId(chunk_id)},
            {"$set": {"embedding": embedding}}
        )

    def search_similar_chunks(self, query_embedding: List[float], top_k: int = 5) -> List[Chunk]:
        # Vector search
        pipeline = [
            {
                "$search": {
                    "knnBeta": {
                        "vector": query_embedding,
                        "path": "embedding",
                        "k": top_k
                    }
                }
            },
            {"$limit": top_k}
        ]
        results = list(self.chunks.aggregate(pipeline))
        return [Chunk(**r) for r in results]

    def close(self):
        self.client.close()