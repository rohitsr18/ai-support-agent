# AI Customer Support Agent for E-Commerce Platforms

## Executive Summary

This project implements an AI-powered customer support agent for e-commerce platforms. It handles high-frequency customer queries related to orders, returns, refunds, and delivery tracking using an LLM with Retrieval-Augmented Generation (RAG).

---

## Project Structure

```
ai-support-agent/
├── app.py                  # FastAPI web server and API endpoints
├── agent.py                # Intent detection, session memory, message routing
├── rag.py                  # RAG pipeline (FAISS retrieval + LLM generation)
├── order_service.py        # Order tracking and return initiation
├── embeddings.py           # OpenAI embedding generation
├── vector_store_faiss.py   # FAISS vector store for document search
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker containerization
├── certs.pem               # Combined CA certificate bundle (SSL)
└── .env                    # Environment variables (OPENAI_API_KEY)
```

---

## Features Implemented

### 1. Chat API Endpoint

**File:** `app.py`

- `POST /chat` — Accepts `session_id` and `message`, returns agent reply
- `GET /` — Health check endpoint
- Loads environment variables via `python-dotenv`
- Handles SSL certificates for corporate proxy environments

### 2. Intent Detection and Entity Extraction

**File:** `agent.py`

The agent classifies every incoming message into one of four intents:

| Intent | Trigger Keywords | Action |
|--------|-----------------|--------|
| `TRACK_ORDER` | "where is my order", "track" | Retrieves order status |
| `RETURN` | "return" | Initiates return workflow |
| `ESCALATE` | "human", "agent" | Escalates to human support |
| `FAQ` | Any other message | Answers via RAG pipeline |

**Entity extraction:** Extracts order IDs matching the pattern `ORD` followed by digits (e.g., `ORD123`) using regex.

### 3. Session Memory (Multi-Turn Conversations)

**File:** `agent.py`

- In-memory session store (`session_store` dict) keyed by `session_id`
- Each session stores full conversation history (`role` + `content`)
- Conversation context persists across multiple messages in the same session
- `extract_order_id_from_history()` searches past messages for order IDs, enabling multi-turn flows like:
  - **Message 1:** "Where is my order ORD123?" → Returns status
  - **Message 2:** "I want to return it" → Finds `ORD123` from history and initiates return

### 4. Order Tracking

**File:** `order_service.py`

- `get_order_status(order_id)` — Looks up order by ID, returns status and expected delivery date
- Returns "Order not found." for unknown order IDs
- Agent appends "Would you like to receive delivery updates?" to tracking responses

### 5. Return Initiation

**File:** `order_service.py`

- `initiate_return(order_id)` — Initiates a return for a valid order
- Validates order exists before processing
- Supports both direct ID input and session history lookup

### 6. Escalation to Human Agents with Context

**File:** `agent.py`

- Triggered when user mentions "human" or "agent"
- Includes full conversation history as `[Escalation context]` so the human agent has complete context
- Format:
  ```
  I'm escalating this to a human support agent. They will assist you shortly.

  [Escalation context]
  User: Where is my order ORD123?
  Assistant: Order status: Delayed. Expected delivery: Tomorrow.
  User: connect me to a human agent
  ```

### 7. RAG Pipeline (FAQ Answering)

**File:** `rag.py`

- **Knowledge Base:** 4 pre-loaded documents covering delays, returns, refunds, and order tracking
- **Retrieval:** FAISS vector similarity search finds top-3 relevant documents
- **Generation:** OpenAI `gpt-4o-mini` generates answers strictly from retrieved context
- **Lazy initialization:** FAISS store is built on first FAQ query, not at import time
- **Error handling:** Graceful fallback message on API errors (quota, network, SSL)
- **Logging:** Errors logged for debugging

### 8. Vector Store (FAISS)

**File:** `vector_store_faiss.py`

- `FaissVectorStore` class wrapping FAISS `IndexFlatL2` (L2 distance)
- Dimension: 1536 (matching OpenAI `text-embedding-3-small` output)
- `add_documents(docs)` — Embeds and indexes documents
- `search(query, k)` — Returns top-k most similar documents

### 9. Embeddings

**File:** `embeddings.py`

- Uses OpenAI `text-embedding-3-small` model
- `embed(text)` — Returns embedding vector for any text input

### 10. Docker Support

**File:** `Dockerfile`

- Based on `python:3.11-slim`
- Installs dependencies and runs uvicorn on port 8000

---

## Workflow (Case Study Mapping)

| Step | Requirement | Implementation |
|------|-------------|----------------|
| 1 | Customer submits query via chat | `POST /chat` endpoint in `app.py` |
| 2 | Agent identifies intent and key entities | `detect_intent()` + `extract_order_id()` in `agent.py` |
| 3 | Relevant knowledge or order data retrieved | FAISS search in `rag.py` / order lookup in `order_service.py` |
| 4 | Response generated or action triggered | LLM generation / `get_order_status()` / `initiate_return()` |
| 5 | Complex issues escalated with context | Escalation with full conversation history in `agent.py` |

---

## Sample Q&A

```
You: Where is my order ORD123?
Agent: Order status: Delayed. Expected delivery: Tomorrow. Would you like to receive delivery updates?

You: I want to return it
Agent: Return successfully initiated for order ORD123.

You: What is your refund policy?
Agent: Refunds are typically processed within 5 to 7 business days. [RAG-generated answer]

You: I need a human agent
Agent: I'm escalating this to a human support agent. They will assist you shortly.
       [Escalation context]
       User: Where is my order ORD123?
       Assistant: Order status: Delayed...
       ...
```

---

## How to Run

### Local

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Start server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t ai-support-agent .
docker run -p 8000:8000 --env-file .env ai-support-agent
```

### Testing

```bash
# Health check
curl http://localhost:8000/

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1","message":"Where is my order ORD123?"}'
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | FAISS (faiss-cpu) |
| Containerization | Docker |
| Language | Python 3.11+ |

---

## Dependencies

- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `pydantic` — Request validation
- `python-dotenv` — Environment variable loading
- `openai` — OpenAI API client
- `faiss-cpu` — Vector similarity search
- `numpy` — Numerical operations
