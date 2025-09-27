from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "ragdb"
    jina_api_key: str = ""
    embed_model: str = "jina-embeddings-v3"
    embed_task: str = "text-matching"
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    chunk_max_tokens: int = 512
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()