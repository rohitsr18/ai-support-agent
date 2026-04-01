# Pragna

Pragna is a lightweight customer support agent for e-commerce use cases. It handles order tracking, returns, escalation, and FAQ answers.

## Features

- **Intent Detection** - Routes queries to: order tracking, returns, escalation, or FAQ
- **Multi-turn Conversations** - Maintains session context across messages
- **Order Management** - Track orders, initiate returns via order ID lookup
- **Escalation** - Escalates to a human agent with conversation context
- **RAG Pipeline** - FAQ retrieval with OpenAI primary and Gemini fallback
- **Web UI** - Built-in chat page
- **Cloud Ready** - Docker + Cloud Run friendly

## Project Structure

```
src/pragna/
├── core/
│   └── agent.py              # Message routing and orchestration
├── services/
│   ├── session_manager.py    # Session state & conversation history
│   ├── entity_extractor.py   # NLP: intents & entity extraction
│   ├── order_service.py      # Order lookups & returns
│   └── rag.py                # RAG pipeline with dual LLM support
├── data/
│   ├── embeddings.py         # Hash-based embeddings (no API cost)
│   └── vector_store_faiss.py # FAISS vector index
├── api/
│   └── app.py                # FastAPI endpoints
└── static/
    └── UI.html               # Chat interface

config/
├── .env.example              # Environment template
scripts/
└── start_server.py           # Auto-port launcher
docker/
└── Dockerfile                # Container image
docs/
└── DEPLOYMENT.md             # Cloud Run deployment guide
```

## Quick Start

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp config/.env.example .env  # PowerShell: Copy-Item config/.env.example .env
# Edit .env with your OpenAI and Gemini API keys

# Run server
python scripts/start_server.py
```

The chat UI is available at `http://localhost:8000/app`.

### Docker

```bash
docker build -f docker/Dockerfile -t pragna .
docker run -p 8000:8000 --env-file .env pragna
```

### API Endpoints

- `POST /chat` - Send message and receive agent reply
  ```json
  {
    "session_id": "user123",
    "message": "Where is my order ORD123?",
    "name": "John"
  }
  ```
- `GET /` - Health check
- `GET /app` - Chat interface

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o-mini (primary) / Gemini 2.0-flash (fallback) |
| Vector Search | FAISS |
| Embeddings | Hash-based (local, no API cost) |
| Frontend | Vanilla HTML/JS (no frameworks) |
| Container | Docker |

## Architecture

The agent follows a modular design:

1. **User Input** → FastAPI endpoint (`/chat`)
2. **Intent Detection** → `IntentDetector` classifies: TRACK_ORDER, RETURN, ESCALATE, FAQ
3. **Routing** → `MessageHandler` directs to appropriate handler
4. **Processing**:
   - **Order tracking** → `OrderService.get_status()`
   - **Returns** → `OrderService.initiate_return()`
   - **FAQ** → `rag_answer()` with semantic search
   - **Escalation** → Includes full conversation context
5. **Response** → Styled per user preference, stored in `SessionManager`

## Sample Interactions

```
User: Where is my order ORD123?
Agent: Order status: Delayed. Expected delivery: Tomorrow.

User: I want to return it
Agent: Return successfully initiated for order ORD123.

User: What about refunds?
Agent: [RAG-generated answer from knowledge base]

User: I need help
Agent: [Escalates to human with full conversation history]
```

## Configuration

Set these environment variables in `.env`:

```
OPENAI_API_KEY=sk-...          # Required for primary LLM
GEMINI_API_KEY=...             # Optional fallback LLM
```

## Deployment

See [Deployment Guide](docs/DEPLOYMENT.md).

## Development

### Adding New Intents

Edit `src/pragna/services/entity_extractor.py` in `IntentDetector.detect()`:

```python
if "my_keyword" in msg:
    return "MY_INTENT"
```

Then add handler in `src/pragna/core/agent.py`:

```python
elif intent == "MY_INTENT":
    reply = self._handle_my_intent(session_id, message)
```

### Adding FAQ Documents

Edit `src/pragna/services/rag.py` and add to `KNOWLEDGE_BASE` list.

## Notes

- Start command for this repo: `python scripts/start_server.py`
- If port 8000 is busy, the script automatically picks the next free port.

## License

MIT

