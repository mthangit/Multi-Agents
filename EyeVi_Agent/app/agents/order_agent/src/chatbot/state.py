from typing import Dict, List, Optional, TypedDict, Any
from pydantic import BaseModel, Field


class ChatState(TypedDict):
    """State structure for chatbot conversation"""
    
    # Input message
    message: str
    
    # Intent and parameters
    intent: Optional[str]
    parameters: Optional[Dict[str, Any]]
    
    # Data results
    product: Optional[Dict]
    products: Optional[List[Dict]]
    order_id: Optional[int]
    order: Optional[Dict]
    error: Optional[str]
    
    # Cart data
    cart_items: Optional[List[Dict]]
    
    # Conversation state
    conversation_stage: Optional[str]
    collected_info: Optional[Dict[str, Any]]
    pending_questions: Optional[List[str]]
    user_session_id: Optional[str]
    
    # Response
    response: Optional[str]


def initial_state() -> ChatState:
    """Create an empty initial state"""
    return {
        "message": "",
        "intent": None,
        "parameters": None,
        "product": None,
        "products": None,
        "order_id": None,
        "order": None,
        "error": None,
        "cart_items": None,
        "conversation_stage": None,
        "collected_info": {},
        "pending_questions": [],
        "user_session_id": None,
        "response": None
    } 