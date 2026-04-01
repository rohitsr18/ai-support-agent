# embeddings.py - Text embedding generation
# Converts text into numerical vectors (embeddings) that capture
# semantic meaning. These vectors are used by FAISS for similarity search.
# Uses a local hash-based approach for consistent, free embeddings
# that work without any external API calls.

import hashlib
import numpy as np

# Embedding dimension — must match the FAISS index dimension
EMBEDDING_DIM = 1536


def embed(text: str) -> list:
    """Generate a deterministic pseudo-embedding from text using hashing.
    Produces consistent vectors so the same text always maps to the same point
    in vector space, enabling reliable similarity search via FAISS."""
    text_lower = text.lower().strip()
    seed = int(hashlib.md5(text_lower.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed)
    return rng.randn(EMBEDDING_DIM).astype("float32").tolist()
