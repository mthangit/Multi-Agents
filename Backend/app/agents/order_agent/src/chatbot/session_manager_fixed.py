import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from src.chatbot.state import ChatState, initial_state, create_conversation_message

logger = logging.getLogger(__name__)


class SessionManager:
    """Quản lý session và memory cho chatbot"""
    
    def __init__(self, session_dir: str = "chat_sessions"):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        
    def _get_session_file(self, session_id: str) -> str:
        """Lấy đường dẫn file session"""
        return os.path.join(self.session_dir, f"{session_id}.json")
    
    def _serialize_state(self, state: ChatState) -> Dict[str, Any]:
        """Convert state thành format có thể serialize"""
        serializable = {}
        for key, value in state.items():
            try:
                json.dumps(value)
                serializable[key] = value
            except (TypeError, OverflowError):
                if value is not None:
                    serializable[key] = str(value)
                else:
                    serializable[key] = None
        return serializable
    
    def _deserialize_state(self, data: Dict[str, Any]) -> ChatState:
        """Convert data từ file thành ChatState với safe guards"""
        state = initial_state()
        
        # Safely update state, handling potential data type issues
        for key, value in data.items():
            if key in state:
                # Special handling for list fields that might be serialized as strings
                if key in ["conversation_history", "cart_items", "pending_questions"]:
                    if isinstance(value, str):
                        try:
                            # Try to parse JSON string
                            import json
                            state[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # Fallback to empty list
                            state[key] = []
                            logger.warning(f"Could not deserialize {key}, using empty list")
                    elif isinstance(value, list):
                        state[key] = value
                    else:
                        state[key] = [] if value is None else value
                        
                # Special handling for dict fields
                elif key in ["memory_context", "collected_info", "parameters"]:
                    if isinstance(value, str):
                        try:
                            import json
                            state[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            state[key] = {}
                            logger.warning(f"Could not deserialize {key}, using empty dict")
                    elif isinstance(value, dict):
                        state[key] = value
                    else:
                        state[key] = {} if value is None else value
                else:
                    # Other fields
                    state[key] = value
            else:
                # Unknown field, ignore
                logger.warning(f"Unknown field in session data: {key}")
                
        return state
    
    def load_session(self, session_id: str) -> ChatState:
        """Load session từ file hoặc tạo mới nếu không tồn tại"""
        session_file = self._get_session_file(session_id)
        
        try:
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    state = self._deserialize_state(data)
                    state["user_session_id"] = session_id
                    logger.info(f"Loaded session {session_id} with {len(state.get('conversation_history', []))} messages")
                    return state
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
        
        # Tạo session mới
        state = initial_state()
        state["user_session_id"] = session_id
        logger.info(f"Created new session {session_id}")
        return state
    
    def save_session(self, session_id: str, state: ChatState):
        """Lưu session vào file"""
        session_file = self._get_session_file(session_id)
        
        try:
            # Thêm timestamp cho session
            serializable_state = self._serialize_state(state)
            serializable_state["last_updated"] = datetime.now().isoformat()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved session {session_id}")
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
    
    def update_conversation_history(self, state: ChatState, user_message: str, bot_response: str) -> ChatState:
        """Cập nhật conversation history với full safe guards"""
        try:
            # Safe copy của state
            if hasattr(state, 'copy') and callable(state.copy):
                updated_state = state.copy()
            else:
                updated_state = dict(state)
            
            # Đảm bảo conversation_history tồn tại và là list
            if "conversation_history" not in updated_state or updated_state["conversation_history"] is None:
                updated_state["conversation_history"] = []
            elif not isinstance(updated_state["conversation_history"], list):
                logger.warning(f"conversation_history is not a list: {type(updated_state['conversation_history'])}")
                updated_state["conversation_history"] = []
            
            # Tránh duplicate messages - kiểm tra message cuối
            history = updated_state["conversation_history"]
            if history and len(history) > 0:
                last_msg = history[-1]
                if isinstance(last_msg, dict) and last_msg.get("content") == bot_response and last_msg.get("role") == "assistant":
                    logger.info("Skipping duplicate bot response")
                    return updated_state
            
            # Thêm message từ user
            user_msg = create_conversation_message(
                role="user", 
                content=user_message,
                metadata={
                    "intent": updated_state.get("intent"),
                    "parameters": updated_state.get("parameters")
                }
            )
            updated_state["conversation_history"].append(user_msg)
            
            # Thêm response từ bot
            bot_msg = create_conversation_message(
                role="assistant", 
                content=bot_response,
                metadata={
                    "intent": updated_state.get("intent"),
                    "conversation_stage": updated_state.get("conversation_stage")
                }
            )
            updated_state["conversation_history"].append(bot_msg)
            
            # Limit history length (giữ tối đa 50 messages)
            if len(updated_state["conversation_history"]) > 50:
                updated_state["conversation_history"] = updated_state["conversation_history"][-50:]
            
            logger.info(f"Updated conversation history. Total messages: {len(updated_state['conversation_history'])}")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in update_conversation_history: {e}")
            import traceback
            traceback.print_exc()
            # Return state with empty history as fallback
            if hasattr(state, 'copy'):
                fallback_state = state.copy()
            else:
                fallback_state = dict(state)
            fallback_state["conversation_history"] = []
            return fallback_state
    
    def update_memory_context(self, state: ChatState) -> ChatState:
        """Cập nhật memory context với thông tin quan trọng"""
        try:
            if "memory_context" not in state or state["memory_context"] is None:
                state["memory_context"] = {}
            elif not isinstance(state["memory_context"], dict):
                logger.warning(f"memory_context is not a dict: {type(state['memory_context'])}")
                state["memory_context"] = {}
            
            memory = state["memory_context"]
            
            # Lưu intent và parameters gần đây
            if state.get("intent"):
                state["last_intent"] = state["intent"]
                memory["recent_intents"] = memory.get("recent_intents", [])
                if state["intent"] not in memory["recent_intents"]:
                    memory["recent_intents"].append(state["intent"])
                    
            if state.get("parameters"):
                state["last_parameters"] = state["parameters"]
                
            # Lưu thông tin sản phẩm đã tìm
            if state.get("product") or state.get("products"):
                memory["last_searched_products"] = {
                    "timestamp": datetime.now().isoformat(),
                    "product": state.get("product"),
                    "products": state.get("products")
                }
            
            # Lưu thông tin giỏ hàng
            cart_items = state.get("cart_items", [])
            if isinstance(cart_items, list) and cart_items:
                memory["cart_summary"] = {
                    "total_items": len(cart_items),
                    "last_updated": datetime.now().isoformat()
                }
            
            # Lưu thông tin đơn hàng
            if state.get("order") or state.get("order_id"):
                memory["last_order"] = {
                    "order_id": state.get("order_id"),
                    "order": state.get("order"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Lưu conversation stage quan trọng
            if state.get("conversation_stage"):
                memory["current_conversation_stage"] = state["conversation_stage"]
                memory["collected_info"] = state.get("collected_info", {})
            
            return state
            
        except Exception as e:
            logger.error(f"Error in update_memory_context: {e}")
            return state
    
    def get_context_summary(self, state: ChatState) -> str:
        """Tạo summary về context hiện tại để cung cấp cho LLM với full safe guards"""
        try:
            # Safe get with type checking
            history = state.get("conversation_history", [])
            if not isinstance(history, list):
                logger.warning(f"conversation_history is not a list: {type(history)}")
                history = []
                
            memory = state.get("memory_context", {})
            if not isinstance(memory, dict):
                logger.warning(f"memory_context is not a dict: {type(memory)}")
                memory = {}
            
            context_parts = []
            
            # Recent conversation
            if history:
                recent_messages = history[-6:]  # 6 messages gần nhất
                context_parts.append("Cuộc trò chuyện gần đây:")
                for msg in recent_messages:
                    if isinstance(msg, dict):
                        role = "Người dùng" if msg.get("role") == "user" else "Bot"
                        content = msg.get("content", "")
                        context_parts.append(f"- {role}: {content}")
                    else:
                        logger.warning(f"Invalid message format: {msg}")
            
            # Current cart
            cart_items = state.get("cart_items", [])
            if isinstance(cart_items, list) and cart_items:
                context_parts.append(f"\nGiỏ hàng hiện tại: {len(cart_items)} sản phẩm")
            
            # Current conversation stage
            if state.get("conversation_stage"):
                context_parts.append(f"\nTrạng thái hiện tại: {state['conversation_stage']}")
                collected_info = state.get("collected_info", {})
                if isinstance(collected_info, dict) and collected_info:
                    context_parts.append(f"Thông tin đã thu thập: {collected_info}")
            
            # Recent activities from memory
            recent_intents = memory.get("recent_intents", [])
            if isinstance(recent_intents, list) and recent_intents:
                context_parts.append(f"\nHành động gần đây: {', '.join(recent_intents[-3:])}")
            
            return "\n".join(context_parts) if context_parts else "Chưa có lịch sử cuộc trò chuyện."
            
        except Exception as e:
            logger.error(f"Error in get_context_summary: {e}")
            import traceback
            traceback.print_exc()
            return "Lỗi khi tạo context summary."
    
    def cleanup_old_sessions(self, days: int = 7):
        """Xóa các session cũ hơn X ngày"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.session_dir, filename)
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Removed old session file: {filename}")
                except Exception as e:
                    logger.error(f"Error removing old session {filename}: {e}")


# Singleton instance
session_manager = SessionManager() 