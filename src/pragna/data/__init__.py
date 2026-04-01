"""Data layer exports."""

from .embeddings import embed
from .vector_store_faiss import FaissVectorStore

__all__ = ["embed", "FaissVectorStore"]
