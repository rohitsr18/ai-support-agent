"""
Core chat orchestration module.

This is the main entry point for processing user messages. It coordinates:
- Intent classification (order tracking, returns, escalation, FAQ)
- Entity extraction (order IDs, user names, style preferences)
- Session context persistence for multi-turn conversations
- Response generation with adaptive styling
"""

from ..services.session_manager import session_manager, UserProfile
from ..services.entity_extractor import EntityExtractor, IntentDetector, ResponseStyler
from ..services.rag import rag_answer
from ..services.order_service import OrderService


class MessageHandler:
    """
    Central orchestrator that routes messages to specialized handlers.
    
    Maintains stateless per-request processing while delegating session
    state to SessionManager. Each handler returns a string reply.
    """
    
    def __init__(self):
        # NLP components for text analysis
        self.extractor = EntityExtractor()      # Extracts order IDs, names, signals
        self.intent_detector = IntentDetector() # Classifies user intent
        self.styler = ResponseStyler()          # Adjusts reply verbosity
        self.order_service = OrderService()     # Order lookup and returns
    
    def handle_message(self, session_id: str, message: str, name: str | None = None) -> str:
        """
        Process a user message and return the agent's reply.
        
        Args:
            session_id: Unique identifier for this conversation
            message: The user's input text
            name: Optional explicit name from API payload
        
        Returns:
            Agent reply string, styled per user preference
        """
        # Store message in session history for multi-turn context
        session_manager.add_message(session_id, "user", message)
        profile = session_manager.get_profile(session_id)
        
        # --- Name Learning ---
        # Priority: explicit API param > detected from text
        if name:
            session_manager.set_name(session_id, name)
        detected_name = self.extractor.extract_name(message)
        if detected_name:
            session_manager.set_name(session_id, detected_name)
        
        # --- Adaptive Learning ---
        # Track style preference: "concise" or "detailed"
        style_pref = self.extractor.detect_style_preference(message)
        if style_pref:
            profile.style = style_pref
        
        # Track dissatisfaction to offer extra help in responses
        if self.extractor.is_dissatisfied(message):
            profile.dissatisfaction_count += 1
        
        # --- Greeting Shortcut ---
        # Simple greetings don't need intent classification
        if self.extractor.is_simple_greeting(message):
            reply = self._handle_greeting(session_id)
            session_manager.add_message(session_id, "assistant", reply)
            return reply
        
        # --- Intent Classification & Routing ---
        intent = self.intent_detector.detect(message)
        
        if intent == "TRACK_ORDER":
            reply = self._handle_track_order(session_id, message)
            profile.last_intent = "TRACK_ORDER"
        elif intent == "RETURN":
            reply = self._handle_return(session_id, message)
            profile.last_intent = "RETURN"
        elif intent == "ESCALATE":
            reply = self._handle_escalation(session_id)
            profile.last_intent = "ESCALATE"
        else:
            reply = rag_answer(message)
            profile.last_intent = "FAQ"
        
        # --- Post-Processing ---
        # Add help offer for users who expressed dissatisfaction earlier
        if profile.dissatisfaction_count > 0 and "Would you like" not in reply:
            reply += " If this doesn't solve it, tell me what part is unclear and I will improve the answer."
        
        # Apply user's preferred verbosity (concise/balanced/detailed)
        reply = self.styler.apply_style(profile.style, reply)
        
        # Persist assistant reply for conversation continuity
        session_manager.add_message(session_id, "assistant", reply)
        return reply
    
    def _handle_greeting(self, session_id: str) -> str:
        user_name = session_manager.get_name(session_id)
        if user_name:
            return f"Hi {user_name}! How can I help you today?"
        else:
            return "Hi! I can help with order tracking, returns, and refunds. What is your name?"
    
    def _handle_track_order(self, session_id: str, message: str) -> str:
        """Look up order status. Falls back to order ID from earlier messages."""
        # Try current message first, then search conversation history
        order_id = (
            self.extractor.extract_order_id(message) 
            or self._find_order_id_in_history(session_id)
        )
        
        if order_id:
            reply = self.order_service.get_status(order_id)
            reply += " Would you like to receive delivery updates?"
            return reply
        else:
            return "I can help track your order. Please share your order ID."
    
    def _handle_return(self, session_id: str, message: str) -> str:
        """Initiate return. Falls back to order ID from earlier messages."""
        # Try current message first, then search conversation history
        order_id = (
            self.extractor.extract_order_id(message) 
            or self._find_order_id_in_history(session_id)
        )
        
        if order_id:
            return self.order_service.initiate_return(order_id)
        else:
            return "I can help you initiate a return. Please provide your order ID."
    
    def _handle_escalation(self, session_id: str) -> str:
        """Transfer to human agent with full conversation context attached."""
        # Include entire session so human agent has complete background
        history = session_manager.get_session_history_dict(session_id)
        context_summary = "\n".join(
            f"{entry['role'].capitalize()}: {entry['content']}"
            for entry in history
        )
        
        return (
            "I'm escalating this to a human support agent. "
            "They will assist you shortly.\n\n"
            "[Escalation context]\n" + context_summary
        )
    
    def _find_order_id_in_history(self, session_id: str) -> str | None:
        """Search past messages for an order ID (e.g., user said 'ORD123' earlier)."""
        history = session_manager.get_session(session_id)
        for message in reversed(history):
            order_id = self.extractor.extract_order_id(message.content)
            if order_id:
                return order_id
        return None


_handler = MessageHandler()


def handle_message(session_id: str, message: str, name: str | None = None) -> str:
    """Public entry point used by the API layer."""
    return _handler.handle_message(session_id, message, name)
