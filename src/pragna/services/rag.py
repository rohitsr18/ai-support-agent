"""
Retrieval-Augmented Generation (RAG) pipeline for FAQ answering.

How it works:
1. User question is embedded and searched against FAISS knowledge base
2. Top 3 relevant documents are retrieved
3. LLM generates answer using retrieved context
4. Falls back OpenAI -> Gemini if primary fails

Knowledge base is loaded lazily on first FAQ query.
"""

import os
import logging
from openai import OpenAI
from google import genai
from ..data.vector_store_faiss import FaissVectorStore

logger = logging.getLogger(__name__)

# --- API Configuration ---
# Keys loaded from environment; missing keys cause runtime errors only when used
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Lazy-initialized clients (avoids startup crash if keys missing)
openai_client = None
OPENAI_MODEL = "gpt-4o-mini"   # Primary LLM

gemini_client = None
GEMINI_MODEL = "gemini-2.0-flash"  # Fallback LLM

# --- Knowledge Base ---
# FAQ documents indexed for semantic search
KNOWLEDGE_BASE = [
    "Orders may be delayed due to logistics or weather issues.",
    "Customers can return items within 7 days of delivery.",
    "Refunds are typically processed within 5 to 7 business days.",
    "Order tracking is available using the order ID shared via email or SMS."
]

# Vector store created on first use to avoid import-time overhead
store = None


def _get_store() -> FaissVectorStore:
    """Lazy-load FAISS index with knowledge base docs."""
    global store
    if store is None:
        store = FaissVectorStore()
        store.add_documents(KNOWLEDGE_BASE)
    return store


def _call_openai(prompt: str) -> str:
    """Generate response using OpenAI GPT. Raises if key missing."""
    global openai_client
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Generate response using Google Gemini. Raises if key missing."""
    global gemini_client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    if gemini_client is None:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def rag_answer(question: str) -> str:
    """
    Answer user question using RAG (Retrieval Augmented Generation).
    
    Process:
    1. Search FAISS for top-3 relevant knowledge base docs
    2. Build prompt with retrieved context + user question
    3. Call OpenAI (primary) or Gemini (fallback) for answer
    
    Returns:
        Generated answer string, or error message if both LLMs fail
    """
    # Step 1: Retrieve relevant documents
    try:
        docs = _get_store().search(question, k=3)
    except Exception as e:
        logger.error("Embedding error: %s", e)
        return "I'm sorry, our AI service is temporarily unavailable. Would you like me to connect you to a human agent?"

    # Step 2: Check if context was found
    if not docs:
        return "I'm not sure about that. Would you like me to connect you to a human agent?"

    # Step 3: Build LLM prompt with context
    context = "\n".join(docs)

    prompt = f"""
You are a customer support agent.
Answer the question strictly using the context below.

Context:
{context}

Question:
{question}
"""

    # Step 4: Generate answer (OpenAI primary, Gemini fallback)
    try:
        logger.info("Trying OpenAI...")
        return _call_openai(prompt)
    except Exception as e:
        logger.warning("OpenAI failed (%s), falling back to Gemini...", e)

    try:
        logger.info("Trying Gemini...")
        return _call_gemini(prompt)
    except Exception as e:
        logger.error("Gemini also failed: %s", e)

    return "I'm sorry, our AI service is temporarily unavailable. Would you like me to connect you to a human agent?"
