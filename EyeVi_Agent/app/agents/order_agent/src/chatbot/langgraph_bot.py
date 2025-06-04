from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated, TypedDict, AsyncIterator, Dict, Any
import operator
import asyncio
import logging
import json
import os
from datetime import datetime
from src.config import settings

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger("chatbot_debug")

# Import các node tools
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

# Khởi tạo LLM Gemini từ settings
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)

# Streaming version của LLM
streaming_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=settings.GEMINI_API_KEY,
    streaming=True
)

def save_debug_state(state, node_name):
    """Lưu state tại mỗi bước vào file để phân tích"""
    debug_dir = os.path.join(os.getcwd(), "debug_logs")
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{node_name}.json"
    filepath = os.path.join(debug_dir, filename)
    
    # Convert state to serializable format
    serializable_state = {}
    for key, value in state.items():
        if key == "message" or key == "intent" or key == "response" or key == "conversation_stage":
            serializable_state[key] = value
        else:
            try:
                # Attempt to convert to JSON-serializable format
                json.dumps({key: value})
                serializable_state[key] = value
            except (TypeError, OverflowError):
                # If not serializable, convert to string
                serializable_state[key] = str(value)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_state, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved debug state for node {node_name} to {filepath}")
    return state

def debug_state(state, node_name):
    """Helper function để log state tại mỗi node"""
    logger.info(f"Executing node: {node_name}")
    logger.info(f"Current intent: {state.get('intent')}")
    logger.info(f"Current parameters: {state.get('parameters')}")
    logger.info(f"Current conversation stage: {state.get('conversation_stage')}")
    
    # Save state to file for debugging
    save_debug_state(state, node_name)
    
    return state

def welcome_node(state):
    """Node chào mừng, sẽ được gọi khi bắt đầu hội thoại mới"""
    debug_state(state, "welcome_node")
    return {"response": "Xin chào! Tôi là trợ lý ảo của hệ thống quản lý đơn hàng. Tôi có thể giúp bạn tìm sản phẩm, thêm vào giỏ hàng, đặt hàng hoặc kiểm tra trạng thái đơn hàng. Bạn cần giúp gì?"}

def help_node(state):
    """Node trợ giúp, cung cấp hướng dẫn về các tính năng"""
    debug_state(state, "help_node")
    help_text = """
    Tôi có thể giúp bạn với các tác vụ sau:
    1. Tìm sản phẩm theo tên (ví dụ: "Tìm sản phẩm tên là iPhone")
    2. Tìm sản phẩm theo ID (ví dụ: "Kiểm tra sản phẩm có ID 123")
    3. Kiểm tra tồn kho (ví dụ: "Sản phẩm ID 123 còn hàng không?")
    4. Thêm vào giỏ hàng (ví dụ: "Thêm 2 sản phẩm ID 123 vào giỏ")
    5. Xem giỏ hàng (ví dụ: "Xem giỏ hàng của tôi")
    6. Đặt hàng (ví dụ: "Tôi muốn đặt hàng")
    7. Kiểm tra đơn hàng (ví dụ: "Kiểm tra đơn hàng số 789")
    
    Bạn cần giúp đỡ gì ạ?
    """
    return {"response": help_text}

def unknown_node(state):
    """Node xử lý khi không xác định được intent"""
    debug_state(state, "unknown_node")
    return {"response": "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể nói rõ hơn hoặc gõ 'help' để xem hướng dẫn."}

def get_order_by_id_node(state):
    """Node lấy thông tin đơn hàng theo ID"""
    debug_state(state, "get_order_by_id_node")
    parameters = state.get("parameters", {})
    order_id = parameters.get("order_id")
    
    if not order_id:
        return {"error": "Không tìm thấy ID đơn hàng"}
    
    from src.database.queries.order import OrderQuery
    order = OrderQuery().get_order_by_id(order_id)
    
    if not order:
        return {"error": f"Không tìm thấy đơn hàng với ID {order_id}"}
    
    return {"order": order}

def route_by_intent(state: ChatState):
    """Xác định node tiếp theo dựa trên intent hoặc conversation_stage"""
    debug_state(state, "route_by_intent")
    logger.info(f"Routing based on intent: {state.get('intent')} and conversation stage: {state.get('conversation_stage')}")
    
    # Nếu đang trong một cuộc trò chuyện, ưu tiên xử lý theo stage
    conversation_stage = state.get("conversation_stage")
    if conversation_stage:
        if conversation_stage == "collecting_info":
            return "collect_order_info"
        elif conversation_stage == "confirm_order":
            return "create_order"
    
    # Nếu không, xử lý theo intent
    intent = state.get("intent")
    if intent == "greet":
        return "welcome"
    elif intent == "help":
        return "help"
    elif intent == "unknown":
        return "unknown"
    elif intent == "collecting_order_info":
        return "collect_order_info"
    elif intent in ["find_product_by_name", "find_product_by_id", "check_stock", 
                   "add_to_cart", "view_cart", "clear_cart", "start_order", 
                   "get_order_by_id"]:
        return "parameter_extraction"
    else:
        return "unknown"

def route_to_tool(state: ChatState):
    """Xác định tool node dựa trên intent sau khi đã có parameters"""
    debug_state(state, "route_to_tool")
    intent = state.get("intent")
    logger.info(f"Routing to tool for intent: {intent}")
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
    """Router sau khi kiểm tra tồn kho"""
    debug_state(state, "post_check_stock_router")
    intent = state.get("intent")
    error = state.get("error")
    
    if error:
        return "generate_response"
    
    if intent == "add_to_cart":
        return "add_to_cart"
    else:
        return "generate_response"

# Khởi tạo LangGraph
class ChatbotGraph:
    def __init__(self):
        # Tạo state graph từ ChatState
        self.graph = StateGraph(ChatState)
        
        # Thêm các node
        # - Basic nodes
        self.graph.add_node("welcome", welcome_node)
        self.graph.add_node("help", help_node)
        self.graph.add_node("unknown", unknown_node)
        self.graph.add_node("intent_classification", intent_classification_node)
        self.graph.add_node("parameter_extraction", parameter_extraction_node)
        self.graph.add_node("generate_response", generate_response_node)
        
        # - Conversation management
        self.graph.add_node("check_conversation_stage", check_conversation_stage_node)
        self.graph.add_node("generate_question", generate_question_node)
        
        # - Product nodes
        self.graph.add_node("find_product_by_id", find_product_by_id_node)
        self.graph.add_node("find_product_by_name", find_product_by_name_node)
        self.graph.add_node("check_stock", check_stock_node)
        
        # - Cart nodes
        self.graph.add_node("add_to_cart", add_to_cart_node)
        self.graph.add_node("view_cart", view_cart_node)
        self.graph.add_node("clear_cart", clear_cart_node)
        
        # - Order nodes
        self.graph.add_node("start_order_process", start_order_process_node)
        self.graph.add_node("collect_order_info", collect_order_info_node)
        self.graph.add_node("create_order", create_order_node)
        self.graph.add_node("get_order_by_id", get_order_by_id_node)

        # Thiết lập entry point
        self.graph.set_entry_point("check_conversation_stage")

        # Thiết lập edges và conditional routing
        # - Main flow
        self.graph.add_edge("check_conversation_stage", "intent_classification")
        self.graph.add_conditional_edges("intent_classification", route_by_intent)
        self.graph.add_conditional_edges("parameter_extraction", route_to_tool)
        
        # - Product & stock flow
        self.graph.add_conditional_edges("check_stock", post_check_stock_router)
        
        # - Collection flow
        self.graph.add_edge("collect_order_info", "generate_question")
        
        # - Routing to generate_response
        tools = ["find_product_by_id", "find_product_by_name", "add_to_cart", 
                "view_cart", "clear_cart", "start_order_process", 
                "get_order_by_id", "create_order"]
                
        for tool in tools:
            self.graph.add_edge(tool, "generate_response")
            
        self.graph.add_edge("welcome", "generate_response")
        self.graph.add_edge("help", "generate_response")
        self.graph.add_edge("unknown", "generate_response")
        self.graph.add_edge("generate_question", "generate_response")

        # Compile graph
        self.app = self.graph.compile()

    def process_message(self, message: str, session_id: str = None) -> str:
        """Process user message and return response"""
        # Create initial state with user message
        state = initial_state()
        state["message"] = message
        state["user_session_id"] = session_id
        
        logger.info(f"Processing message: {message}")
        logger.info(f"Session ID: {session_id}")
        
        # Save initial state
        save_debug_state(state, "initial_state")
        
        # Run the graph
        result = self.app.invoke(state)
        
        # Log final state
        logger.info(f"Final state: intent={result.get('intent')}, response={result.get('response')}")
        
        # Save final state
        save_debug_state(result, "final_state")
        
        # Return the response
        return result["response"]
        
    async def process_message_streaming(self, message: str, session_id: str = None) -> AsyncIterator[str]:
        """Process user message và trả về response theo kiểu streaming thực sự"""
        logger.info(f"Processing streaming message: {message}")
        
        # Create initial state with user message
        state = initial_state()
        state["message"] = message
        state["user_session_id"] = session_id
        
        logger.info(f"Session ID: {session_id}")
        save_debug_state(state, "initial_state_streaming")
        
        # Yield initial processing message
        yield "Đang xử lý"
        await asyncio.sleep(0.1)
        yield "..."
        await asyncio.sleep(0.1)
        
        try:
            # Run the graph
            result = self.app.invoke(state)
            
            # Log final state
            logger.info(f"Final streaming state: intent={result.get('intent')}, response={result.get('response')}")
            save_debug_state(result, "final_state_streaming")
            
            response = result.get("response", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
            
            # Clear the processing message
            yield "\r🤖 Bot: "
            await asyncio.sleep(0.05)
            
            # Stream the actual response word by word
            words = response.split()
            for i, word in enumerate(words):
                yield word
                if i < len(words) - 1:  # Không thêm space sau từ cuối
                    yield " "
                # Delay ngẫu nhiên để tạo hiệu ứng typing tự nhiên
                await asyncio.sleep(0.03 + (len(word) * 0.01))
                
        except Exception as e:
            logger.error(f"Error in streaming processing: {str(e)}")
            yield "\r🤖 Bot: Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn."