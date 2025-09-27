from typing import Dict, Type, List
from .models import Chunk
from pathlib import Path


class HandlerRegistry:
    def __init__(self):
        self.handlers: Dict[str, Type] = {}

    def register(self, modality: str, handler_class: Type):
        self.handlers[modality] = handler_class

    def get_handler(self, modality: str):
        return self.handlers.get(modality)

    def supported_modalities(self) -> List[str]:
        return list(self.handlers.keys())


# Global registry instance
registry = HandlerRegistry()