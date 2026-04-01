"""
Session storage for multi-turn conversations.

Maintains per-session state including:
- Message history (for context and escalation handoff)
- User profile (style preference, dissatisfaction tracking)
- User name (for personalized greetings)

All storage is in-memory; data resets on server restart.
"""

from typing import Optional, Dict, List


class Message:
    """Single chat message with role (user/assistant) and content."""

    def __init__(self, role: str, content: str):
        self.role = role       # 'user' or 'assistant'
        self.content = content # Message text
    
    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class UserProfile:
    """
    Per-session preferences learned from user behavior.
    
    Attributes:
        style: Response verbosity ('concise', 'balanced', or 'detailed')
        dissatisfaction_count: Number of negative feedback signals detected
        last_intent: Most recent classified intent for analytics
    """

    def __init__(self):
        self.style = "balanced"           # Default response verbosity
        self.dissatisfaction_count = 0    # Tracks frustration signals
        self.last_intent = None           # Last recognized intent type
    
    def to_dict(self) -> dict:
        return {
            "style": self.style,
            "dissatisfaction_count": self.dissatisfaction_count,
            "last_intent": self.last_intent,
        }


class SessionManager:
    """
    In-memory store for conversation sessions.
    
    Thread-safe for single-process deployments. For multi-instance
    scaling, replace with Redis or database-backed storage.
    """

    def __init__(self):
        self._sessions: Dict[str, List[Message]] = {}  # session_id -> messages
        self._profiles: Dict[str, UserProfile] = {}    # session_id -> profile
        self._names: Dict[str, str] = {}               # session_id -> user name
    
    def get_session(self, session_id: str) -> List[Message]:
        """Return existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]
    
    def get_profile(self, session_id: str) -> UserProfile:
        """Return existing profile or create a new one."""
        if session_id not in self._profiles:
            self._profiles[session_id] = UserProfile()
        return self._profiles[session_id]
    
    def get_name(self, session_id: str) -> Optional[str]:
        """Get saved display name for the session if available."""
        return self._names.get(session_id)
    
    def set_name(self, session_id: str, name: str):
        """Store user's display name (cleaned and capitalized)."""
        if name and name.strip():
            self._names[session_id] = name.strip().capitalize()
    
    def add_message(self, session_id: str, role: str, content: str) -> Message:
        """Append message to timeline. Creates session if needed."""
        message = Message(role, content)
        self.get_session(session_id).append(message)
        return message
    
    def get_session_history_dict(self, session_id: str) -> List[dict]:
        """Get message list as dicts (for JSON serialization/escalation)."""
        return [msg.to_dict() for msg in self.get_session(session_id)]


# Singleton instance shared across all request handlers
session_manager = SessionManager()
