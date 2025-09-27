# Handlers package

from .text_handler import TextHandler
from .pdf_handler import PDFHandler
from core.registry import registry

# Register handlers
registry.register("text", TextHandler)
registry.register("markdown", TextHandler)
registry.register("pdf", PDFHandler)