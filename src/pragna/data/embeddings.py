"""
Deterministic embedding generation for semantic search.

Creates consistent vector representations of text without external API calls.
Uses hash-seeded random vectors so identical text always produces identical
embeddings, enabling reliable FAISS similarity search.

Note: This is a cost-free local approach. For production accuracy,
replace with OpenAI or HuggingFace embeddings.
"""

import hashlib
import numpy as np

# Must match FAISS index dimension
EMBEDDING_DIM = 1536


def embed(text: str) -> list:
    """
    Generate deterministic pseudo-embedding from text.
    
    Args:
        text: Input string to embed
    
    Returns:
        1536-dimensional float32 vector as Python list
    
    How it works:
        1. Hash normalized text to get consistent seed
        2. Use seeded RNG to generate random vector
        3. Same text always produces same vector
    """
    text_lower = text.lower().strip()
    seed = int(hashlib.md5(text_lower.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed)
    return rng.randn(EMBEDDING_DIM).astype("float32").tolist()
