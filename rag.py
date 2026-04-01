# rag.py - Retrieval-Augmented Generation (RAG) module
# Uses FAISS vector search to find relevant knowledge base documents,
# then passes them as context to the LLM to generate accurate answers.
#
# DUAL PROVIDER SUPPORT (OpenAI + Google Gemini):
# - Tries OpenAI first
# - If it fails (quota exceeded, rate limit, etc.), automatically
#   falls back to Google Gemini
# - No manual switching needed — the agent stays available

import os
import logging
from openai import OpenAI
from google import genai
from vector_store_faiss import FaissVectorStore

# Set up logging to capture API errors for debugging
logger = logging.getLogger(__name__)

# ============================================================
# LLM CLIENT SETUP
# Both clients are initialized at startup so either can be
# used instantly when fallback is needed.
# ============================================================

# API keys (optional in local/dev runs)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Clients are lazy-initialized so import works even when keys are missing.
openai_client = None
OPENAI_MODEL = "gpt-4o-mini"

# Google Gemini client (uses the new google-genai SDK)
gemini_client = None
GEMINI_MODEL = "gemini-2.0-flash"

# ============================================================
# KNOWLEDGE BASE
# These are the FAQ documents that get embedded into FAISS.
# The agent searches these to answer general customer questions.
# ============================================================
KNOWLEDGE_BASE = [
    "Orders may be delayed due to logistics or weather issues.",
    "Customers can return items within 7 days of delivery.",
    "Refunds are typically processed within 5 to 7 business days.",
    "Order tracking is available using the order ID shared via email or SMS."
]

# Lazy-initialized FAISS store (created on first FAQ query, not at import time)
store = None


def _get_store() -> FaissVectorStore:
    """Initialize the FAISS vector store on first use.
    Embeds all knowledge base documents and indexes them for search."""
    global store
    if store is None:
        store = FaissVectorStore()
        store.add_documents(KNOWLEDGE_BASE)
    return store


# ============================================================
# RAG ANSWER FUNCTION
# This is the main RAG pipeline:
#   1. Search FAISS for relevant documents
#   2. Build a prompt with the retrieved context
#   3. Try primary LLM (OpenAI), if it fails try fallback (Gemini)
#   4. Return the generated answer
# ============================================================

def _call_openai(prompt: str) -> str:
    """Call OpenAI API to generate a response."""
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
    """Call Google Gemini API to generate a response."""
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
    """Answer a customer question using Retrieval-Augmented Generation.
    Tries OpenAI first, falls back to Gemini if OpenAI fails."""

    # Step 1: Search for the top 3 most relevant knowledge base documents
    try:
        docs = _get_store().search(question, k=3)
    except Exception as e:
        logger.error("Embedding error: %s", e)
        return "I'm sorry, our AI service is temporarily unavailable. Would you like me to connect you to a human agent?"

    # No relevant documents found
    if not docs:
        return "I'm not sure about that. Would you like me to connect you to a human agent?"

    # Step 2: Combine the retrieved documents into a single context string
    context = "\n".join(docs)

    # Step 3: Build the prompt with context and question
    prompt = f"""
You are a customer support agent.
Answer the question strictly using the context below.

Context:
{context}

Question:
{question}
"""

    # Step 4: Try OpenAI first, fall back to Gemini if it fails
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