from src.chatbot.session_manager import session_manager
from src.chatbot.state import ChatState
import logging

logger = logging.getLogger(__name__)


def load_session_node(state: ChatState) -> ChatState:
    """Node để load session data từ file"""
    session_id = state.get("user_session_id")
    
    if not session_id:
        logger.warning("No session_id provided, using fresh state")
        return state
    
    # Load session data
    saved_state = session_manager.load_session(session_id)
    
    # Merge với current state, ưu tiên SAVED data và current message
    current_message = state.get("message", "")
    current_session_id = state.get("user_session_id")
    
    # ✅ FIXED: Ưu tiên saved_state, chỉ ghi đè message và session_id hiện tại
    merged_state = {**state, **saved_state}  # saved_state ghi đè state
    merged_state["message"] = current_message  # Keep current message
    merged_state["user_session_id"] = current_session_id  # Keep current session_id
    
    # Đảm bảo các field quan trọng tồn tại
    if "conversation_history" not in merged_state or merged_state["conversation_history"] is None:
        merged_state["conversation_history"] = []
    if "cart_items" not in merged_state or merged_state["cart_items"] is None:
        merged_state["cart_items"] = []
    if "memory_context" not in merged_state or merged_state["memory_context"] is None:
        merged_state["memory_context"] = {}
    
    logger.info(f"Loaded session {session_id} with {len(merged_state.get('conversation_history', []))} messages")
    logger.info(f"Cart items: {len(merged_state.get('cart_items', []))}")
    logger.info(f"Memory context keys: {list(merged_state.get('memory_context', {}).keys())}")
    
    return merged_state


def update_memory_node(state: ChatState) -> ChatState:
    """Node để cập nhật memory context"""
    # Cập nhật memory context
    updated_state = session_manager.update_memory_context(state)
    
    logger.info(f"Updated memory context for session {state.get('user_session_id')}")
    
    return updated_state


def save_session_node(state: ChatState) -> ChatState:
    """Node để lưu session cuối workflow"""
    session_id = state.get("user_session_id")
    
    if not session_id:
        logger.warning("No session_id to save")
        return state
    
    # Cập nhật conversation history
    user_message = state.get("message", "")
    bot_response = state.get("response", "")
    
    if user_message and bot_response:
        updated_state = session_manager.update_conversation_history(
            state, user_message, bot_response
        )
    else:
        updated_state = state
    
    # Debug log trước khi save
    logger.info(f"Saving session {session_id}")
    logger.info(f"Conversation history length: {len(updated_state.get('conversation_history', []))}")
    logger.info(f"Cart items: {len(updated_state.get('cart_items', []))}")
    logger.info(f"Memory context: {updated_state.get('memory_context', {})}")
    
    # Lưu session
    session_manager.save_session(session_id, updated_state)
    
    return updated_state


def provide_context_node(state: ChatState) -> ChatState:
    """Node cung cấp context cho các node khác"""
    # Tạo context summary
    context_summary = session_manager.get_context_summary(state)
    
    # Thêm context vào state để các node khác sử dụng
    updated_state = state.copy()
    updated_state["context_summary"] = context_summary
    
    logger.info(f"Provided context summary: {len(context_summary)} characters")
    logger.info(f"Context summary preview: {context_summary[:200]}...")
    logger.info(f"Current conversation history: {len(state.get('conversation_history', []))} messages")
    
    return updated_state 