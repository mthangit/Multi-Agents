from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from typing import AsyncIterator, Any, Dict
import logging
import json
import os
from datetime import datetime
from src.config import settings

# === Logging setup ===
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chatbot_debug")

# === Node import giữ nguyên ===
from src.chatbot.nodes.product_tools import (
    find_product_by_id_node,
    find_product_by_name_node
)
from src.chatbot.nodes.cart_tools import (
    check_stock_node,
    add_to_cart_node,
    view_cart_node,
    clear_cart_node
)
from src.chatbot.nodes.order_tools import (
    start_order_process_node,
    collect_order_info_node,
    create_order_node
)
from src.chatbot.nodes.intent_nodes import (
    intent_classification_node,
    parameter_extraction_node,
    generate_response_node
)
from src.chatbot.nodes.conversation_node import (
    check_conversation_stage_node,
    generate_question_node
)
from src.chatbot.state import ChatState, initial_state

# === LLM setup ===
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)
streaming_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY, streaming=True)

# === Debug util ===
def save_debug_state(state, node_name):
    debug_dir = os.path.join(os.getcwd(), "debug_logs")
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{node_name}.json"
    filepath = os.path.join(debug_dir, filename)
    serializable_state = {}
    for key, value in state.items():
        try:
            json.dumps({key: value})
            serializable_state[key] = value
        except (TypeError, OverflowError):
            serializable_state[key] = str(value)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_state, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved debug state for node {node_name} to {filepath}")

def debug_state(state, node_name):
    logger.info(f"Node: {node_name}")
    logger.info(f"Message: {state.get('message', '')[:50]}...")
    logger.info(f"Intent: {state.get('intent')}")
    logger.info(f"Parameters: {state.get('parameters')}")
    logger.info(f"Conversation stage: {state.get('conversation_stage')}")
    save_debug_state(state, node_name)
    return state

# === Các node chuẩn hóa ===
def welcome_node(state):
    debug_state(state, "welcome_node")
    response = "Xin chào! Tôi là trợ lý ảo của hệ thống quản lý đơn hàng. Tôi có thể giúp bạn tìm sản phẩm, thêm vào giỏ hàng, đặt hàng hoặc kiểm tra trạng thái đơn hàng. Bạn cần giúp gì?"
    new_messages = state.get("messages", []) + [AIMessage(content=response)]
    return {"messages": new_messages}

def help_node(state):
    debug_state(state, "help_node")
    help_text = (
        "Tôi có thể giúp bạn với các tác vụ sau:\n"
        "1. Tìm sản phẩm theo tên (vd: 'Tìm sản phẩm tên là iPhone')\n"
        "2. Tìm sản phẩm theo ID (vd: 'Kiểm tra sản phẩm có ID 123')\n"
        "3. Kiểm tra tồn kho (vd: 'Sản phẩm ID 123 còn hàng không?')\n"
        "4. Thêm vào giỏ hàng (vd: 'Thêm 2 sản phẩm ID 123 vào giỏ')\n"
        "5. Xem giỏ hàng (vd: 'Xem giỏ hàng của tôi')\n"
        "6. Đặt hàng (vd: 'Tôi muốn đặt hàng')\n"
        "7. Kiểm tra đơn hàng (vd: 'Kiểm tra đơn hàng số 789')\n"
        "Bạn cần giúp gì ạ?"
    )
    new_messages = state.get("messages", []) + [AIMessage(content=help_text)]
    return {"messages": new_messages}

def unknown_node(state):
    debug_state(state, "unknown_node")
    response = "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể nói rõ hơn hoặc gõ 'help' để xem hướng dẫn."
    new_messages = state.get("messages", []) + [AIMessage(content=response)]
    return {"messages": new_messages}

def get_order_by_id_node(state):
    debug_state(state, "get_order_by_id_node")
    parameters = state.get("parameters", {})
    order_id = parameters.get("order_id")
    if not order_id:
        response = "Không tìm thấy ID đơn hàng."
        new_messages = state.get("messages", []) + [AIMessage(content=response)]
        return {"messages": new_messages}
    
    try:
        from src.database.queries.order import OrderQuery
        order = OrderQuery().get_order_by_id(order_id)
        if not order:
            response = f"Không tìm thấy đơn hàng với ID {order_id}"
            new_messages = state.get("messages", []) + [AIMessage(content=response)]
            return {"messages": new_messages}
        
        new_messages = state.get("messages", []) + [ToolMessage(content=f"Thông tin đơn hàng: {order}", tool_name="get_order_by_id", tool_args={"order_id": order_id})]
        return {"messages": new_messages, "order": order}
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        response = f"Lỗi khi lấy thông tin đơn hàng: {str(e)}"
        new_messages = state.get("messages", []) + [AIMessage(content=response)]
        return {"messages": new_messages, "error": str(e)}

# === Routing giữ nguyên ===
def route_by_intent(state: ChatState):
    debug_state(state, "route_by_intent")
    conversation_stage = state.get("conversation_stage")
    if conversation_stage:
        if conversation_stage == "collecting_info":
            return "collect_order_info"
        elif conversation_stage == "confirm_order":
            return "create_order"
    intent = state.get("intent")
    if intent == "greet":
        return "welcome"
    elif intent == "help":
        return "help"
    elif intent == "unknown":
        return "unknown"
    elif intent == "collecting_order_info":
        return "collect_order_info"
    elif intent in [
        "find_product_by_name", "find_product_by_id", "check_stock", 
        "add_to_cart", "view_cart", "clear_cart", "start_order", 
        "get_order_by_id"]:
        return "parameter_extraction"
    else:
        return "unknown"

def route_to_tool(state: ChatState):
    debug_state(state, "route_to_tool")
    intent = state.get("intent")
    tool_mapping = {
        "find_product_by_name": "find_product_by_name",
        "find_product_by_id": "find_product_by_id",
        "check_stock": "check_stock",
        "add_to_cart": "check_stock",  # Kiểm tra tồn kho trước khi thêm vào giỏ
        "view_cart": "view_cart",
        "clear_cart": "clear_cart",
        "start_order": "start_order_process",
        "get_order_by_id": "get_order_by_id"
    }
    return tool_mapping.get(intent, "unknown")

def post_check_stock_router(state: ChatState):
    debug_state(state, "post_check_stock_router")
    intent = state.get("intent")
    error = state.get("error")
    if error:
        return "generate_response"
    if intent == "add_to_cart":
        return "add_to_cart"
    else:
        return "generate_response"

# === Khởi tạo LangGraph ===
class ChatbotGraph:
    def __init__(self):
        self.graph = StateGraph(ChatState)
        # Node
        self.graph.add_node("welcome", welcome_node)
        self.graph.add_node("help", help_node)
        self.graph.add_node("unknown", unknown_node)
        self.graph.add_node("intent_classification", intent_classification_node)
        self.graph.add_node("parameter_extraction", parameter_extraction_node)
        self.graph.add_node("generate_response", generate_response_node)
        self.graph.add_node("check_conversation_stage", check_conversation_stage_node)
        self.graph.add_node("generate_question", generate_question_node)
        self.graph.add_node("find_product_by_id", find_product_by_id_node)
        self.graph.add_node("find_product_by_name", find_product_by_name_node)
        self.graph.add_node("check_stock", check_stock_node)
        self.graph.add_node("add_to_cart", add_to_cart_node)
        self.graph.add_node("view_cart", view_cart_node)
        self.graph.add_node("clear_cart", clear_cart_node)
        self.graph.add_node("start_order_process", start_order_process_node)
        self.graph.add_node("collect_order_info", collect_order_info_node)
        self.graph.add_node("create_order", create_order_node)
        self.graph.add_node("get_order_by_id", get_order_by_id_node)
        # Entry + Edges
        self.graph.set_entry_point("check_conversation_stage")
        self.graph.add_edge("check_conversation_stage", "intent_classification")
        self.graph.add_conditional_edges("intent_classification", route_by_intent)
        self.graph.add_conditional_edges("parameter_extraction", route_to_tool)
        self.graph.add_conditional_edges("check_stock", post_check_stock_router)
        self.graph.add_edge("collect_order_info", "generate_question")
        tools = [
            "find_product_by_id", "find_product_by_name", "add_to_cart", 
            "view_cart", "clear_cart", "start_order_process", 
            "get_order_by_id", "create_order"
        ]
        for tool in tools:
            self.graph.add_edge(tool, "generate_response")
        self.graph.add_edge("welcome", "generate_response")
        self.graph.add_edge("help", "generate_response")
        self.graph.add_edge("unknown", "generate_response")
        self.graph.add_edge("generate_question", "generate_response")
        self.app = self.graph.compile()

    def process_message(self, message: str, session_id: str = None) -> str:
        state = initial_state()
        state["messages"] = [HumanMessage(content=message)]
        state["user_session_id"] = session_id
        logger.info(f"Processing message: {message}")
        save_debug_state(state, "initial_state")
        result = self.app.invoke(state)
        save_debug_state(result, "final_state")
        # Trả về AIMessage cuối cùng
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                return msg.content
        return str(result.get("messages", ["Không có phản hồi!"])[-1])

    async def stream(self, query: str, context_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming agent response theo pattern thực chiến, trả về các trạng thái rõ ràng
        """
        try:
            # Initialize với complete state như process_message
            inputs = initial_state()
            inputs.update({
                'message': query,  # ✅ Thêm field message để các nodes có thể access
                'messages': [HumanMessage(content=query)],
                'user_session_id': context_id
            })
            config = {'configurable': {'thread_id': context_id}}
            yielded_tool_msg = False
            final_state = None

            async for item in self.app.astream(inputs, config=config, stream_mode='values'):
                final_state = item  # Keep track of final state
                messages = item.get('messages', [])
                if not messages:
                    continue
                message = messages[-1]
                
                # AI vừa gọi tool/function
                if (
                    isinstance(message, AIMessage)
                    and getattr(message, "tool_calls", None)
                    and len(message.tool_calls) > 0
                ):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Đang tra cứu dữ liệu...',
                    }
                # ToolMessage: báo trạng thái đang xử lý
                elif isinstance(message, ToolMessage) and not yielded_tool_msg:
                    yielded_tool_msg = True
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Đang xử lý dữ liệu từ hệ thống...',
                    }

            # Yield kết quả cuối cùng từ final_state
            yield self.get_final_response(final_state)
            
        except Exception as e:
            logger.error(f"Error in stream method: {e}", exc_info=True)
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f"Đã xảy ra lỗi: {str(e)}"
            }

    def get_final_response(self, final_state) -> dict:
        """Get final response from the last state without using checkpointer"""
        try:
            if not final_state:
                logger.warning("No final state available")
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': "Xin lỗi, không thể xử lý yêu cầu của bạn."
                }
            
            messages = final_state.get("messages", [])
            logger.info(f"Found {len(messages)} messages in final state")
            
            if messages:
                # Tìm AIMessage cuối cùng
                last_ai_msg = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
                if last_ai_msg:
                    logger.info(f"Found final AI message: {last_ai_msg.content[:50]}...")
                    return {
                        'is_task_complete': True,
                        'require_user_input': False,
                        'content': last_ai_msg.content
                    }
            
            # Fallback: check response field in state
            response = final_state.get("response")
            if response:
                logger.info(f"Found response in state: {response[:50]}...")
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': response
                }
            
            # Final fallback
            logger.warning("No AI message or response found in final state")
            return {
                'is_task_complete': True,
                'require_user_input': False,
                'content': "Xin lỗi, không thể xử lý yêu cầu của bạn."
            }
            
        except Exception as e:
            logger.error(f"Error in get_final_response: {e}", exc_info=True)
            return {
                'is_task_complete': True,
                'require_user_input': False,
                'content': "Đã xảy ra lỗi khi xử lý yêu cầu."
            }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']