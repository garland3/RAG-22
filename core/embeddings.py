import requests
from typing import List, Dict, Any
import logging
from .models import EmbeddingRequest, EmbeddingResponse

logger = logging.getLogger(__name__)


class JinaEmbeddingClient:
    def __init__(self, api_key: str, model: str = "jina-embeddings-v3", task: str = "text-matching"):
        self.api_key = api_key
        self.model = model
        self.task = task
        self.url = "https://api.jina.ai/v1/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Returns list of embeddings."""
        payload = EmbeddingRequest(
            model=self.model,
            task=self.task,
            input=texts
        ).dict()

        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            resp = EmbeddingResponse(**data)
            return resp.data
        except requests.RequestException as e:
            logger.error(f"Jina API error: {e}")
            raise

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        return self.embed_batch([text])[0]