# app.py - Entry point for the AI Customer Support Agent API
# Sets up the FastAPI server with endpoints for chat and health check.

import os

# Fix SSL certificate verification for corporate proxy environments (e.g. ZScaler)
_certs = os.path.join(os.path.dirname(__file__), "certs.pem")
os.environ["SSL_CERT_FILE"] = _certs
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = _certs
os.environ["REQUESTS_CA_BUNDLE"] = _certs

# Load environment variables from .env file (e.g. OPENAI_API_KEY)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from agent import handle_message

# Create the FastAPI application instance
app = FastAPI()


# Request model: each chat message must include a session_id and the user's message
class ChatRequest(BaseModel):
    session_id: str   # Unique ID to track conversation history per user
    message: str      # The user's chat message


@app.post("/chat")
def chat(request: ChatRequest):
    """Main chat endpoint — receives a user message, processes it through the
    agent, and returns the AI-generated reply."""
    reply = handle_message(
        session_id=request.session_id,
        message=request.message
    )
    return {"reply": reply}


@app.get("/")
def health():
    """Health check endpoint — returns server status."""
    return {"status": "running"}