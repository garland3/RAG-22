from celery import Celery
from config.settings import settings
from core.storage import Storage
from core.embeddings import JinaEmbeddingClient
import logging

logger = logging.getLogger(__name__)

app = Celery('rag_workers', broker=settings.broker_url, backend=settings.result_backend)

@app.task(bind=True, max_retries=3)
def embed_chunk_batch(self, chunk_ids: list):
    """Embed a batch of chunks asynchronously."""
    try:
        storage = Storage(settings.mongo_uri, settings.mongo_db)
        embed_client = JinaEmbeddingClient(settings.jina_api_key, settings.embed_model, settings.embed_task)

        # Get chunks
        from bson import ObjectId
        chunks = list(storage.chunks.find({"_id": {"$in": [ObjectId(cid) for cid in chunk_ids]}}))
        texts = [c['content'] for c in chunks]

        embeddings = embed_client.embed_batch(texts)

        # Update each chunk
        for chunk_data, emb in zip(chunks, embeddings):
            storage.update_chunk_embedding(str(chunk_data['_id']), emb)

        storage.close()
        logger.info(f"Embedded {len(chunk_ids)} chunks")
    except Exception as e:
        logger.error(f"Embedding task failed: {e}")
        self.retry(countdown=60 * (2 ** self.request.retries))  # exponential backoff