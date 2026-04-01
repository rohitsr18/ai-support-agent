# vector_store_faiss.py - FAISS-based vector store for semantic search
# Stores document embeddings in a FAISS index and retrieves the most
# semantically similar documents for a given query.

import faiss
import numpy as np
from embeddings import embed


class FaissVectorStore:
    """A simple vector store using FAISS (Facebook AI Similarity Search).
    Documents are embedded into vectors and indexed for fast similarity lookup."""

    def __init__(self, dimension: int = 1536):
        # Create a flat L2 (Euclidean distance) index for exact nearest-neighbor search
        self.index = faiss.IndexFlatL2(dimension)
        # Keep a parallel list of original document texts
        self.documents = []

    def add_documents(self, docs: list[str]):
        """Embed a list of documents and add them to the FAISS index."""
        # Convert each document text into an embedding vector
        vectors = [embed(doc) for doc in docs]
        vectors_np = np.array(vectors).astype("float32")
        # Add the vectors to the FAISS index
        self.index.add(vectors_np)
        # Store the original texts so we can return them on search
        self.documents.extend(docs)

    def search(self, query: str, k: int = 3) -> list[str]:
        """Find the top-k most similar documents to the query.
        Returns the original document texts."""
        if not self.documents:
            return []

        # Embed the query and search the FAISS index
        query_vector = np.array([embed(query)]).astype("float32")
        _, indices = self.index.search(query_vector, k)

        # Return matching documents (FAISS returns -1 for missing entries)
        return [
            self.documents[i]
            for i in indices[0]
            if i != -1
        ]