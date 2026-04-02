"""
Text analysis utilities for NLP processing.

Provides three main capabilities:
1. EntityExtractor - Pulls structured data from free-form text
2. IntentDetector - Classifies user request type
3. ResponseStyler - Adjusts reply verbosity based on user preference
"""

import re
from typing import Optional


class EntityExtractor:
    """
    Extracts entities and signals from user messages.
    
    Capabilities:
    - Order IDs (pattern: ORD followed by digits)
    - User names (from phrases like "My name is...")
    - Style preference (concise vs detailed)
    - Dissatisfaction signals (for adaptive responses)
    - Greeting detection (for quick replies)
    """

    @staticmethod
    def extract_order_id(message: str) -> Optional[str]:
        """
        Extract order ID from text (e.g., 'ORD123', 'ord456').
        Returns uppercase ID or None if not found.
        """
        match = re.search(r"\b(ORD\d+)\b", message, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    # Common words that should not be treated as names
    NON_NAMES = {
        'hi', 'hello', 'hey', 'yes', 'no', 'ok', 'okay', 'sure', 'thanks',
        'thank', 'please', 'help', 'good', 'morning', 'afternoon', 'evening',
        'bye', 'goodbye', 'what', 'how', 'why', 'when', 'where', 'who',
    }

    @staticmethod
    def extract_name(message: str) -> Optional[str]:
        """
        Extract user's name from introduction phrases or standalone name.
        Matches: 'My name is X', 'I am X', 'I'm X', 'This is X', or just 'X' (single word)
        Returns capitalized name or None.
        """
        # Pattern-based extraction
        patterns = [
            r"\bmy name is\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
            r"\bi am\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
            r"\bi'm\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
            r"\bthis is\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
            r"\bcall me\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
            r"\bit's\s+([A-Za-z][A-Za-z'\-]{1,30})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()
        
        # Check for standalone name (single word, 2-20 chars, letters only)
        msg = message.strip()
        if re.match(r"^[A-Za-z]{2,20}$", msg):
            # Exclude common greetings and filler words
            if msg.lower() not in EntityExtractor.NON_NAMES:
                return msg.capitalize()
        
        return None
    
    @staticmethod
    def is_name_response(message: str) -> bool:
        """
        Check if message looks like a name response to 'What's your name?'.
        Matches single words or short phrases that look like names.
        Excludes common greetings and filler words.
        """
        msg = message.strip().lower()
        
        # Single word check
        if re.match(r'^[A-Za-z]{2,20}$', msg):
            return msg not in EntityExtractor.NON_NAMES
        
        # Short intro phrases
        if re.match(r"^(i'm|my name is|call me|it's|this is)\s+[A-Za-z]{2,20}$", msg, re.IGNORECASE):
            return True
        return False
    
    @staticmethod
    def detect_style_preference(message: str) -> Optional[str]:
        """
        Detect if user wants concise or detailed responses.
        
        Returns:
            'concise' - User wants brief answers ('be brief', 'short answer')
            'detailed' - User wants thorough explanations ('explain', 'step by step')
            None - No clear preference detected
        """
        msg = message.lower()
        if any(phrase in msg for phrase in ["short answer", "be brief", "concise", "in short"]):
            return "concise"
        if any(phrase in msg for phrase in ["more detail", "explain", "step by step", "detailed"]):
            return "detailed"
        return None
    
    @staticmethod
    def is_dissatisfied(message: str) -> bool:
        """
        Check if user expresses frustration or dissatisfaction.
        Used to trigger extra help offers in responses.
        """
        msg = message.lower()
        cues = [
            "not helpful",
            "didn't help",
            "that is wrong",
            "wrong answer",
            "not clear",
            "confusing",
        ]
        return any(cue in msg for cue in cues)
    
    @staticmethod
    def is_simple_greeting(message: str) -> bool:
        """
        Check if message is just a greeting (hi, hello, hey, etc.).
        These skip intent classification for faster response.
        """
        return bool(
            re.match(
                r"^\s*(hi|hello|hey|good morning|good afternoon|good evening)\s*[!.]?\s*$",
                message,
                re.IGNORECASE,
            )
        )


class IntentDetector:
    """
    Classifies user messages into actionable intents.
    
    Intent Types:
    - TRACK_ORDER: User asking about order status/delivery
    - RETURN: User wants to return an item
    - ESCALATE: User explicitly requests human agent
    - FAQ: Default - answered via RAG pipeline
    """

    # Phrases that trigger human escalation bypass
    ESCALATION_PHRASES = [
        "human agent",
        "live agent",
        "real person",
        "customer representative",
        "talk to human",
        "talk to a human",
        "speak to human",
        "speak to a human",
        "speak with human",
        "speak with a human",
        "connect me to",
        "transfer me",
        "escalate this",
        "real human",
        "actual person",
        "supervisor",
        "manager",
    ]
    
    # Keywords suggesting order status inquiry
    ORDER_STATUS_KEYWORDS = [
        "status",
        "where",
        "delivery",
        "arrive",
        "arriving",
        "late",
        "delayed",
        "shipped",
        "dispatch",
    ]
    
    @staticmethod
    def wants_human_escalation(message: str) -> bool:
        """Check for explicit human agent request."""
        msg = message.lower()
        return any(phrase in msg for phrase in IntentDetector.ESCALATION_PHRASES)
    
    @staticmethod
    def detect(message: str) -> str:
        """
        Classify message into TRACK_ORDER, RETURN, ESCALATE, or FAQ.
        Returns the intent string for routing.
        """
        msg = message.lower()
        
        if "where is my order" in msg or "track" in msg:
            return "TRACK_ORDER"
        
        if "order" in msg and any(
            word in msg for word in IntentDetector.ORDER_STATUS_KEYWORDS
        ):
            return "TRACK_ORDER"
        
        if "return" in msg:
            return "RETURN"
        
        if IntentDetector.wants_human_escalation(msg):
            return "ESCALATE"
        
        return "FAQ"


class ResponseStyler:
    """
    Transforms replies based on user's verbosity preference.
    
    Styles:
    - 'concise': Returns only first sentence
    - 'detailed': Appends offer for more detail
    - 'balanced': No modification (default)
    """

    @staticmethod
    def apply_style(style: str, reply: str) -> str:
        """Adjust reply verbosity. Returns modified string."""
        if style == "concise":
            parts = re.split(r"(?<=[.!?])\s+", reply.strip(), maxsplit=1)
            return parts[0].strip() if parts else reply
        
        if style == "detailed" and "Would you like" not in reply:
            return reply + " If you want, I can share the next steps in detail."
        
        return reply
