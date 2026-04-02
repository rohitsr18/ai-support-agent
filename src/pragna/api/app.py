"""
HTTP API layer providing REST endpoints for Pragna chat service.

Endpoints:
    POST /chat  - Process user messages and return AI responses
    GET  /      - Health check for liveness probes  
    GET  /app   - Serve the built-in chat UI

This module loads environment variables (API keys) at import time
and delegates all business logic to the core agent module.
"""

from dotenv import load_dotenv
load_dotenv()  # Load API keys before any service imports

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ..core.agent import handle_message
from pathlib import Path

# FastAPI instance with OpenAPI metadata for auto-generated docs at /docs
app = FastAPI(title="Pragna")

# Resolve static directory relative to this file's location
STATIC_DIR = Path(__file__).parent.parent / "static"


class ChatRequest(BaseModel):
    """
    Request payload for the /chat endpoint.
    
    Attributes:
        session_id: Unique client session for conversation continuity.
        message: User's text input to process.
        name: Optional user name for personalized responses.
    """
    session_id: str
    message: str
    name: str | None = None


class ChatResponse(BaseModel):
    """
    Response payload from the /chat endpoint.
    
    Attributes:
        reply: AI-generated response text.
    """
    reply: str


class HealthResponse(BaseModel):
    """
    Response payload from the health endpoint.
    
    Attributes:
        status: Current service state ("running" when healthy).
    """
    status: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user message and return an AI response.
    
    Delegates to the core agent which handles intent detection,
    RAG retrieval, order lookups, and response generation.
    
    Args:
        request: Chat payload with session_id, message, and optional name.
        
    Returns:
        ChatResponse containing the AI-generated reply.
    """
    reply = handle_message(
        session_id=request.session_id,
        message=request.message,
        name=request.name,
    )
    return ChatResponse(reply=reply)


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Health check endpoint for monitoring and orchestration platforms.
    
    Used by Cloud Run, Kubernetes, load balancers, and local scripts
    to verify the service is accepting requests.
    
    Returns:
        HealthResponse with status="running" when healthy.
    """
    return HealthResponse(status="running")


@app.get("/app")
def serve_chat_ui():
    """
    Serve the built-in chat interface.
    
    Returns the static HTML/JS/CSS UI from the static directory.
    Clients access this at /app to use the chat widget.
    
    Returns:
        FileResponse with ui.html content.
    """
    ui_path = STATIC_DIR / "ui.html"
    return FileResponse(ui_path, media_type="text/html")
