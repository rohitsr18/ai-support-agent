"""
FAISS-based vector store for semantic document search.

Provides fast nearest-neighbor lookup for the RAG pipeline:
- Documents are embedded and indexed on add
- Queries return top-k most semantically similar documents

Uses flat L2 index (exact search) suitable for small knowledge bases.
For large-scale deployments, consider IVF or HNSW indices.
"""

import faiss
import numpy as np
from .embeddings import embed


class FaissVectorStore:
    """
    Simple document vector index with add and search operations.
    
    Attributes:
        index: FAISS IndexFlatL2 for exact nearest-neighbor search
        documents: Parallel list of original text (position matches vector index)
    """

    def __init__(self, dimension: int = 1536):
        # L2 (Euclidean) distance index for exact search
        self.index = faiss.IndexFlatL2(dimension)
        # Store original docs so we can return text, not just indices
        self.documents = []

    def add_documents(self, docs: list[str]):
        """
        Embed documents and add to the index.
        
        Args:
            docs: List of document strings to index
        """
        vectors = [embed(doc) for doc in docs]
        vectors_np = np.array(vectors).astype("float32")
        self.index.add(vectors_np)
        self.documents.extend(docs)

    def search(self, query: str, k: int = 3) -> list[str]:
        """
        Find k most similar documents to query.
        
        Args:
            query: Search query text
            k: Number of results to return (default: 3)
        
        Returns:
            List of matching document strings
        """
        if not self.documents:
            return []

        # Embed query and search index
        query_vector = np.array([embed(query)]).astype("float32")
        _, indices = self.index.search(query_vector, k)

        # Filter out -1 (FAISS placeholder for missing results)
        return [
            self.documents[i]
            for i in indices[0]
            if i != -1
        ]
