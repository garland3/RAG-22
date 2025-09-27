from core.storage import Storage
from core.embeddings import JinaEmbeddingClient
from config.settings import settings
from typing import List, Dict, Any


class VectorSearch:
    def __init__(self):
        self.storage = Storage(settings.mongo_uri, settings.mongo_db)
        self.embed_client = JinaEmbeddingClient(settings.jina_api_key, settings.embed_model, settings.embed_task)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        query_emb = self.embed_client.embed_single(query)
        chunks = self.storage.search_similar_chunks(query_emb, top_k)
        results = []
        for chunk in chunks:
            doc = self.storage.get_document_by_path(chunk.metadata.get("source_path", ""))
            results.append({
                "chunk_content": chunk.content,
                "document_path": chunk.metadata.get("source_path", ""),
                "modality": doc.modality if doc else "unknown",
                "similarity_score": None  # MongoDB doesn't return scores in this pipeline
            })
        self.storage.close()
        return results