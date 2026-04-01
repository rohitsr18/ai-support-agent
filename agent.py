# agent.py - Core AI agent logic
# Handles intent detection, entity extraction, session memory,
# and routes user messages to the appropriate handler.

from rag import rag_answer
from order_service import get_order_status, initiate_return

import re

# ============================================================
# SESSION MEMORY
# Stores conversation history per session_id so the agent can
# remember previous messages in a multi-turn conversation.
# Format: { "session_id": [ {"role": "user"/"assistant", "content": "..."}, ... ] }
# ============================================================
session_store: dict[str, list[dict]] = {}


def get_session(session_id: str) -> list[dict]:
    """Get or create the conversation history for a given session."""
    if session_id not in session_store:
        session_store[session_id] = []
    return session_store[session_id]


# ============================================================
# ENTITY EXTRACTION
# Extracts key entities (order IDs) from user messages.
# Order IDs follow the format: ORD followed by digits (e.g. ORD123)
# ============================================================

def extract_order_id(message: str) -> str | None:
    """Extract an order ID (e.g. ORD123) from a single message."""
    match = re.search(r'\b(ORD\d+)\b', message, re.IGNORECASE)
    return match.group(1).upper() if match else None


def extract_order_id_from_history(session_id: str) -> str | None:
    """Search conversation history (most recent first) for an order ID.
    This enables multi-turn flows like:
      User: 'Where is my order ORD123?'
      User: 'I want to return it'  <-- agent finds ORD123 from history
    """
    for entry in reversed(get_session(session_id)):
        order_id = extract_order_id(entry["content"])
        if order_id:
            return order_id
    return None


# ============================================================
# INTENT DETECTION
# Classifies user message into one of 4 intents:
#   TRACK_ORDER - user wants to track a delivery
#   RETURN      - user wants to return an item
#   ESCALATE    - user wants to talk to a human agent
#   FAQ         - general question (handled by RAG)
# ============================================================

def detect_intent(message: str) -> str:
    """Classify user message into an intent category."""
    msg = message.lower()

    if "where is my order" in msg or "track" in msg:
        return "TRACK_ORDER"

    if "return" in msg:
        return "RETURN"

    if "human" in msg or "agent" in msg:
        return "ESCALATE"

    # Default: treat as a general FAQ question
    return "FAQ"


# ============================================================
# MAIN MESSAGE HANDLER
# This is the core function that processes each user message:
#   1. Saves the message to session history
#   2. Detects the user's intent
#   3. Routes to the appropriate handler
#   4. Saves the agent reply to session history
# ============================================================

def handle_message(session_id: str, message: str) -> str:
    """Process a user message and return the agent's reply."""

    # Step 1: Add the user's message to conversation history
    history = get_session(session_id)
    history.append({"role": "user", "content": message})

    # Step 2: Detect what the user wants
    intent = detect_intent(message)

    # Step 3: Route to the appropriate handler based on intent

    if intent == "TRACK_ORDER":
        # Try to find the order ID in current message or conversation history
        order_id = extract_order_id(message) or extract_order_id_from_history(session_id)
        if order_id:
            # Order ID found — fetch status and offer delivery updates
            reply = (
                get_order_status(order_id)
                + " Would you like to receive delivery updates?"
            )
        else:
            # No order ID found — ask the user to provide one
            reply = (
                "I can help track your order. "
                "Please share your order ID."
            )

    elif intent == "RETURN":
        # Try to find the order ID in current message or conversation history
        order_id = extract_order_id(message) or extract_order_id_from_history(session_id)
        if order_id:
            # Order ID found — initiate the return workflow
            reply = initiate_return(order_id)
        else:
            # No order ID found — ask the user to provide one
            reply = (
                "I can help you initiate a return. "
                "Please provide your order ID."
            )

    elif intent == "ESCALATE":
        # Build a summary of the full conversation to hand off to the human agent
        context_summary = "\n".join(
            f"{entry['role'].capitalize()}: {entry['content']}"
            for entry in history
        )
        reply = (
            "I'm escalating this to a human support agent. "
            "They will assist you shortly.\n\n"
            "[Escalation context]\n" + context_summary
        )

    else:
        # FAQ intent — use RAG (Retrieval-Augmented Generation) to answer
        reply = rag_answer(message)

    # Step 4: Save the agent's reply to conversation history
    history.append({"role": "assistant", "content": reply})
    return reply
