from typing import Dict, List, Optional, TypedDict, Any, Annotated
from pydantic import BaseModel, Field
import operator
from datetime import datetime


class ConversationMessage(TypedDict):
    """Single message in conversation"""
    role: str  # "user" hoặc "assistant"
    content: str
    timestamp: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ChatState(TypedDict):
    """State structure for chatbot conversation with memory"""
    
    # Current input message
    message: str
    
    # Conversation history - Manual management, không dùng operator.add
    conversation_history: List[ConversationMessage]
    
    # Intent and parameters
    intent: Optional[str]
    parameters: Optional[Dict[str, Any]]
    
    # Data results
    product: Optional[Dict]
    products: Optional[List[Dict]]
    order_id: Optional[int]
    order: Optional[Dict]
    error: Optional[str]
    
    # Cart data - Manual management, được persist qua session  
    cart_items: List[Dict]
    
    # Conversation state
    conversation_stage: Optional[str]
    collected_info: Optional[Dict[str, Any]]
    pending_questions: Optional[List[str]]
    user_session_id: Optional[str]
    
    # Memory context - lưu thông tin quan trọng từ conversation
    memory_context: Optional[Dict[str, Any]]
    
    # Last activities - theo dõi hành động gần đây
    last_intent: Optional[str]
    last_parameters: Optional[Dict[str, Any]]
    
    # Context summary for LLM
    context_summary: Optional[str]
    
    # Response
    response: Optional[str]


def initial_state() -> ChatState:
    """Create an empty initial state"""
    return {
        "message": "",
        "conversation_history": [],
        "intent": None,
        "parameters": None,
        "product": None,
        "products": None,
        "order_id": None,
        "order": None,
        "error": None,
        "cart_items": [],
        "conversation_stage": None,
        "collected_info": {},
        "pending_questions": [],
        "user_session_id": None,
        "memory_context": {},
        "last_intent": None,
        "last_parameters": None,
        "context_summary": None,
        "response": None
    }


def create_conversation_message(role: str, content: str, metadata: Dict[str, Any] = None) -> ConversationMessage:
    """Helper function để tạo conversation message"""
    return {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    } 