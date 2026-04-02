"""
Retrieval-Augmented Generation (RAG) pipeline for FAQ answering.

How it works:
1. User question is embedded and searched against FAISS knowledge base
2. Top 3 relevant documents are retrieved
3. LLM generates answer using retrieved context
4. Falls back through available providers: Ollama -> Groq -> OpenAI -> Gemini

Supported LLM Providers:
- Ollama (local, free) - Best for development
- Groq (cloud, free tier) - Very fast, good for production
- OpenAI (cloud, paid) - High quality
- Gemini (cloud, paid) - Google's model

Knowledge base is loaded lazily on first FAQ query.
"""

import os
import logging
import requests
from ..data.vector_store_faiss import FaissVectorStore

logger = logging.getLogger(__name__)

# --- LLM Provider Configuration ---
# Set LLM_PROVIDER env var to choose: "ollama", "groq", "openai", "gemini", or "auto"
# "auto" (default) tries providers in order: ollama -> groq -> openai -> gemini
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# Provider-specific settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # or "gemma2", "mistral", "qwen2.5"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Free, very fast

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Lazy-initialized clients
_openai_client = None
_gemini_client = None
_groq_client = None

# --- Knowledge Base ---
KNOWLEDGE_BASE = [
    "Orders may be delayed due to logistics or weather issues.",
    "Customers can return items within 7 days of delivery.",
    "Refunds are typically processed within 5 to 7 business days.",
    "Order tracking is available using the order ID shared via email or SMS."
]

store = None


def _get_store() -> FaissVectorStore:
    """Lazy-load FAISS index with knowledge base docs."""
    global store
    if store is None:
        store = FaissVectorStore()
        store.add_documents(KNOWLEDGE_BASE)
    return store


def _call_ollama(prompt: str) -> str:
    """
    Generate response using Ollama (local LLM).
    
    Requires Ollama running locally: https://ollama.ai
    Start with: ollama run llama3.2
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def _call_groq(prompt: str) -> str:
    """
    Generate response using Groq (free tier available).
    
    Get free API key: https://console.groq.com
    Models: llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it
    """
    global _groq_client
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")
    
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _call_openai(prompt: str) -> str:
    """Generate response using OpenAI GPT."""
    global _openai_client
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)

    response = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Generate response using Google Gemini."""
    global _gemini_client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)

    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def _generate_response(prompt: str) -> str:
    """
    Generate LLM response using configured provider(s).
    
    If LLM_PROVIDER is "auto", tries in order: ollama -> groq -> openai -> gemini
    Otherwise uses the specified provider only.
    """
    providers = {
        "ollama": _call_ollama,
        "groq": _call_groq,
        "openai": _call_openai,
        "gemini": _call_gemini,
    }
    
    # If specific provider requested, use only that
    if LLM_PROVIDER != "auto" and LLM_PROVIDER in providers:
        logger.info(f"Using {LLM_PROVIDER}...")
        return providers[LLM_PROVIDER](prompt)
    
    # Auto mode: try providers in order
    errors = []
    for name, func in providers.items():
        try:
            logger.info(f"Trying {name}...")
            return func(prompt)
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            errors.append(f"{name}: {e}")
    
    # All providers failed
    raise RuntimeError(f"All LLM providers failed: {errors}")


def rag_answer(question: str) -> str:
    """
    Answer user question using RAG (Retrieval Augmented Generation).
    
    Process:
    1. Search FAISS for top-3 relevant knowledge base docs
    2. Build prompt with retrieved context + user question
    3. Generate answer using available LLM provider
    
    Returns:
        Generated answer string, or error message if all providers fail
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

    prompt = f"""You are a helpful customer support agent.
Answer the question using ONLY the context below. Be concise and friendly.

Context:
{context}

Question: {question}

Answer:"""

    # Step 4: Generate answer using configured LLM provider(s)
    try:
        return _generate_response(prompt)
    except Exception as e:
        logger.error("All LLM providers failed: %s", e)
        return "I'm sorry, our AI service is temporarily unavailable. Would you like me to connect you to a human agent?"
