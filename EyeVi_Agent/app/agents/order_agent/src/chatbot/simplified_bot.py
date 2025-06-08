import logging
from typing import AsyncIterator, Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.config import settings
from src.chatbot.tools import all_tools

# === Logging setup ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simplified_chatbot")

# === Memory Setup with LangChain ===
def create_memory_for_session(session_id: str, k: int = 10) -> ConversationBufferWindowMemory:
    """Create LangChain memory for a session with window of k messages."""
    return ConversationBufferWindowMemory(
        k=k,  # Keep last k exchanges (k*2 messages total)
        return_messages=True,
        memory_key="chat_history",
        input_key="input",
        output_key="output"
    )

# Global memory store for sessions
session_memories: Dict[str, ConversationBufferWindowMemory] = {}

def get_or_create_memory(session_id: str) -> ConversationBufferWindowMemory:
    """Get or create LangChain memory for a session."""
    if session_id not in session_memories:
        session_memories[session_id] = create_memory_for_session(session_id)
        logger.info(f"Created new memory for session {session_id}")
    return session_memories[session_id]

# === LLM Setup ===
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-05-20", 
    api_key=settings.GEMINI_API_KEY
).bind_tools(all_tools)

# LLM for analysis steps (without tools)
analysis_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-05-20", 
    api_key=settings.GEMINI_API_KEY
)

def analyze_intent(state):
    """Use LLM to analyze user intent intelligently."""
    messages = state.get("messages", [])
    
    # Debug: track user message preservation
    logger.info(f"analyze_intent: received {len(messages)} messages")
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            logger.info(f"  HumanMessage {i}: {msg.content[:50]}...")
    
    # Get the latest human message
    user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            user_message = msg.content.strip()
            break
    
    if not user_message:
        logger.error("No valid user message found in analyze_intent")
        state["intent_info"] = {
            "intent": "general",
            "confidence": 0.0,
            "description": "No user message found",
            "reasoning": "Empty or invalid user input"
        }
        return state
    
    logger.info(f"Analyzing intent for: '{user_message[:100]}...'")
    
    # Simplified intent analysis prompt
    intent_prompt = f"""Phân tích câu sau và trả về JSON:

User: "{user_message}"

Trả về format:
{{"intent": "search_product|add_to_cart|view_cart|create_order|general", "confidence": 0.85, "description": "mô tả ngắn"}}

Intent types:
- search_product: tìm sản phẩm
- add_to_cart: mua/thêm vào giỏ 
- view_cart: xem giỏ hàng
- create_order: đặt hàng
- general: trò chuyện thông thường"""

    try:
        response = analysis_llm.invoke([HumanMessage(content=intent_prompt)])
        intent_text = response.content.strip()
        
        # Extract JSON
        import json
        if '```' in intent_text:
            intent_text = intent_text.split('```')[1].replace('json', '').strip()
        
        intent_info = json.loads(intent_text)
        logger.info(f"Intent detected: {intent_info}")
        
    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        intent_info = {
            "intent": "general",
            "confidence": 0.5,
            "description": "Could not determine intent",
            "reasoning": f"Error: {str(e)}"
        }
    
    # Add intent info to state (preserve existing state)
    state["intent_info"] = intent_info
    state["original_user_message"] = user_message  # Store for later access
    logger.info(f"analyze_intent: returning state with {len(state.get('messages', []))} messages")
    return state

def parse_arguments(state):
    """Use LLM to parse and extract arguments based on detected intent."""
    messages = state.get("messages", [])
    intent_info = state.get("intent_info", {})
    intent = intent_info.get("intent", "general")
    
    # Debug: track user message preservation
    logger.info(f"parse_arguments: received {len(messages)} messages")
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            logger.info(f"  HumanMessage {i}: {msg.content[:50]}...")
    
    # Get the latest human message
    user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            user_message = msg.content.strip()
            break
    
    if not user_message:
        logger.error("No valid user message found in parse_arguments")
        state["parsed_args"] = {
            "intent": intent,
            "entities": {},
            "needs_tools": False,
            "suggested_action": None
        }
        return state
    
    logger.info(f"Parsing arguments for intent: {intent}")
    
    if intent == "general":
        parsed_args = {
            "intent": intent,
            "entities": {},
            "needs_tools": False,
            "suggested_action": None
        }
    else:
        # Simplified argument parsing prompt
        parse_prompt = f"""Trích xuất thông tin từ câu sau:

Intent: {intent}
User: "{user_message}"

Trả về JSON:
{{"entities": {{}}, "suggested_action": "tool_name"}}

Ví dụ:
- search_product: {{"entities": {{"product_id": "123", "product_name": "iPhone"}}, "suggested_action": "find_product_by_name"}}
- add_to_cart: {{"entities": {{"product_id": "123", "quantity": 2}}, "suggested_action": "add_to_cart"}}
- view_cart: {{"entities": {{}}, "suggested_action": "view_cart"}}"""

        try:
            response = analysis_llm.invoke([HumanMessage(content=parse_prompt)])
            args_text = response.content.strip()
            
            # Extract JSON
            import json
            if '```' in args_text:
                args_text = args_text.split('```')[1].replace('json', '').strip()
            
            parsed_data = json.loads(args_text)
            
            parsed_args = {
                "intent": intent,
                "entities": parsed_data.get("entities", {}),
                "needs_tools": intent != "general",
                "suggested_action": parsed_data.get("suggested_action")
            }
            
            logger.info(f"Parsed arguments: {parsed_args}")
            
        except Exception as e:
            logger.error(f"Error parsing arguments: {e}")
            # Fallback
            parsed_args = {
                "intent": intent,
                "entities": {},
                "needs_tools": intent != "general",
                "suggested_action": {
                    "search_product": "find_product_by_name",
                    "add_to_cart": "add_to_cart", 
                    "view_cart": "view_cart",
                    "create_order": "create_order"
                }.get(intent)
            }
    
    # Add parsed args to state (preserve existing state)
    state["parsed_args"] = parsed_args
    logger.info(f"parse_arguments: returning state with {len(state.get('messages', []))} messages")
    return state

def should_continue(state):
    """Determine the next step in the workflow."""
    messages = state.get("messages", [])
    if not messages:
        logger.info("No messages found, ending workflow")
        return END
        
    last_message = messages[-1]
    logger.info(f"Last message type: {type(last_message)}")
    
    # If the LLM makes a tool call, route to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"Tool calls detected: {[call.get('name', 'unknown') for call in last_message.tool_calls]}")
        return "tools"
    # If no tool calls from agent_with_tools, go directly to final response
    else:
        logger.info("No tool calls, going to final response")
        return "agent_final_response"

def agent_with_tools(state):
    """Agent that decides which tools to call based on user intent."""
    messages = state.get("messages", [])
    intent_info = state.get("intent_info", {})
    parsed_args = state.get("parsed_args", {})
    
    # Debug: log state contents
    logger.info(f"agent_with_tools: received state with keys: {list(state.keys())}")
    logger.info(f"agent_with_tools: intent_info: {intent_info}")
    logger.info(f"agent_with_tools: parsed_args: {parsed_args}")
    logger.info(f"agent_with_tools: {len(messages)} messages")
    
    # Get user message
    user_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            user_message = msg
            break
    
    if not user_message:
        logger.error("No valid user message found in agent_with_tools")
        error_response = AIMessage(content="Xin lỗi, không tìm thấy tin nhắn hợp lệ để xử lý.")
        state["messages"] = messages + [error_response]
        return state
    
    intent = intent_info.get("intent", "general")
    entities = parsed_args.get("entities", {})
    
    # System prompt focused on tool calling decisions
    system_content = f"""Bạn là trợ lý mua sắm. Nhiệm vụ của bạn là CHỌN VÀ GỌI TOOLS phù hợp.

INTENT: {intent}
THÔNG TIN: {entities}

CÁC CÔNG CỤ:
- find_product_by_id(product_id: int)
- find_product_by_name(name: str) 
- add_to_cart(product_id: int, quantity: int = 1, user_id: int = 1)
- view_cart(user_id: int = 1)
- create_order(user_id: int = 1, shipping_address: str = None, phone: str = None, payment_method: str = None)
- clear_cart(user_id: int = 1)
- get_order_by_id(order_id: int)
- test_tool()

QUY TẮC:
- CHỈ gọi tools, KHÔNG trả lời người dùng
- Gọi đúng 1 tool phù hợp nhất
- Không giải thích, chỉ gọi tool"""

    # Prepare messages for LLM with tools
    if not system_content or not system_content.strip():
        system_content = "Bạn là trợ lý mua sắm. Hãy sử dụng các công cụ để giúp người dùng."
        
    llm_messages = [SystemMessage(content=system_content)]
    
    # Add conversation context (only HumanMessage with validation)
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            llm_messages.append(msg)
    
    # Validate that we have at least SystemMessage + 1 HumanMessage
    if len(llm_messages) < 2:
        logger.warning(f"Not enough valid messages for agent_with_tools: {len(llm_messages)}")
        # Add a fallback message
        llm_messages.append(HumanMessage(content="Tôi cần hỗ trợ."))
    
    # Debug: log messages being sent
    logger.info(f"agent_with_tools sending {len(llm_messages)} messages")
    for i, msg in enumerate(llm_messages):
        logger.info(f"  Message {i}: {type(msg)} - {msg.content[:50] if hasattr(msg, 'content') else 'No content'}...")
    
    try:
        logger.info(f"agent_with_tools: Sending {len(llm_messages)} messages to LLM")
        
        response = llm.invoke(llm_messages)
        
        # Debug tool calls
        logger.info(f"agent_with_tools response has tool_calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"Tool calls: {[call.get('name') for call in response.tool_calls]}")
        
        # Add response to messages and return updated state
        new_messages = messages + [response]
        state["messages"] = new_messages
        return state
        
    except Exception as e:
        logger.error(f"Error in agent_with_tools: {e}", exc_info=True)
        error_response = AIMessage(content="Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn.")
        new_messages = messages + [error_response]
        state["messages"] = new_messages
        return state

def agent_final_response(state):
    """Agent that generates final response based on tool results."""
    messages = state.get("messages", [])
    intent_info = state.get("intent_info", {})
    
    # Debug: log state contents
    logger.info(f"agent_final_response: received state with keys: {list(state.keys())}")
    logger.info(f"agent_final_response: intent_info: {intent_info}")
    
    # Debug: log all messages in state
    logger.info(f"agent_final_response: received {len(messages)} messages")
    for i, msg in enumerate(messages):
        logger.info(f"  Message {i}: {type(msg)} - {msg.content[:50] if hasattr(msg, 'content') and msg.content else 'No content'}")
    
    # Get user message
    user_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            user_message = msg
            break
    
    # Fallback to original user message from state
    original_user_message = state.get("original_user_message", "")
    
    if not user_message and original_user_message:
        logger.info("Using original_user_message from state as fallback")
        user_message = HumanMessage(content=original_user_message)
    
    if not user_message:
        logger.error("No valid user message found in agent_final_response")
        # Instead of failing, let's try to continue without requiring user message
        # because we have tool results and can generate response from them
        logger.info("Continuing without user message, using available context")
    
    intent = intent_info.get("intent", "general")
    
    # System prompt focused on generating final response
    if user_message:
        system_content = f"""Bạn là trợ lý mua sắm thân thiện. Nhiệm vụ của bạn là TẠO PHẢN HỒI CUỐI cho người dùng.

INTENT GỐC: {intent}

QUAN TRỌNG:
- Bạn đang trong cuộc trò chuyện liên tục với người dùng
- Hãy tham khảo lịch sử trò chuyện để hiểu ngữ cảnh
- Trả lời một cách tự nhiên và nhất quán với cuộc hội thoại

HƯỚNG DẪN:
- Dựa vào kết quả từ các tools đã thực hiện
- Trả lời một cách tự nhiên, thân thiện
- Tóm tắt thông tin hữu ích
- KHÔNG gọi tools nữa
- Nếu có lỗi từ tools, giải thích và đưa ra gợi ý
- Nhớ ngữ cảnh của cuộc trò chuyện trước đó

NGUYÊN TẮC:
- Luôn hữu ích và rõ ràng
- Sử dụng tiếng Việt tự nhiên
- Đưa ra bước tiếp theo nếu cần
- Duy trì tính nhất quán trong cuộc hội thoại"""
    else:
        system_content = """Bạn là trợ lý mua sắm thân thiện. Tạo phản hồi dựa trên kết quả từ các tools đã thực hiện.

QUAN TRỌNG:
- Bạn đang trong cuộc trò chuyện liên tục với người dùng
- Hãy tham khảo lịch sử trò chuyện để hiểu ngữ cảnh

HƯỚNG DẪN:
- Tóm tắt kết quả tool một cách tự nhiên
- Đưa ra thông tin hữu ích cho người dùng
- KHÔNG gọi tools nữa
- Duy trì tính nhất quán trong cuộc hội thoại"""

    # Prepare messages for LLM without tools
    if not system_content or not system_content.strip():
        system_content = "Bạn là trợ lý hữu ích. Hãy trả lời dựa trên thông tin có sẵn."
        
    llm_messages = [SystemMessage(content=system_content)]
    
    # Add all conversation context including tool results with validation
    # We need to maintain proper message sequence: Human -> AI (with tool_calls) -> Tool -> AI (final)
    valid_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content and msg.content.strip():
            valid_messages.append(msg)
        elif isinstance(msg, AIMessage) and msg.content and msg.content.strip():
            # Add AI messages with tool calls (they're part of conversation flow)
            valid_messages.append(msg)
        elif isinstance(msg, ToolMessage) and msg.content and msg.content.strip():
            # Debug ToolMessage format
            logger.info(f"Adding ToolMessage: content={msg.content[:100]}, tool_call_id={getattr(msg, 'tool_call_id', 'None')}")
            valid_messages.append(msg)
    
    # Add valid messages to llm_messages
    llm_messages.extend(valid_messages)
    
    # Ensure we have the original user message for context
    has_user_message = any(isinstance(msg, HumanMessage) for msg in llm_messages)
    if not has_user_message and original_user_message:
        logger.info("Adding original user message to ensure context")
        # Insert user message after SystemMessage
        llm_messages.insert(1, HumanMessage(content=original_user_message))
    
    # Validate that we have at least SystemMessage + 1 other message
    if len(llm_messages) < 2:
        logger.warning(f"Not enough valid messages for LLM: {len(llm_messages)}")
        # Add a fallback message
        fallback_msg = original_user_message or "Tôi cần hỗ trợ."
        llm_messages.append(HumanMessage(content=fallback_msg))
    
    # Debug: log final messages
    logger.info(f"Final llm_messages count: {len(llm_messages)}")
    for i, msg in enumerate(llm_messages):
        logger.info(f"  Final Message {i}: {type(msg)} - {msg.content[:50] if hasattr(msg, 'content') else 'No content'}...")
    
    try:
        logger.info(f"agent_final_response: Sending {len(llm_messages)} messages to analysis_llm")
        
        # Use analysis_llm (without tools) for final response
        response = analysis_llm.invoke(llm_messages)
        
        logger.info(f"agent_final_response generated: {response.content[:100]}...")
        
        # Add response to messages and return updated state
        new_messages = messages + [response]
        state["messages"] = new_messages
        return state
        
    except Exception as e:
        logger.error(f"Error in agent_final_response: {e}", exc_info=True)
        error_response = AIMessage(content="Xin lỗi, đã xảy ra lỗi khi tạo phản hồi cuối.")
        new_messages = messages + [error_response]
        state["messages"] = new_messages
        return state

def custom_tool_node(state):
    """Custom tool node that preserves state and ensures proper message handling."""
    from langgraph.prebuilt import ToolNode
    
    messages = state.get("messages", [])
    
    # Debug: log state before tool execution
    logger.info(f"custom_tool_node: received state with keys: {list(state.keys())}")
    logger.info(f"custom_tool_node: {len(messages)} messages before tool execution")
    
    # Use the standard ToolNode to execute tools
    tool_node = ToolNode(all_tools)
    tool_result = tool_node.invoke({"messages": messages})
    
    # Extract new messages from tool result
    tool_messages = tool_result.get("messages", [])
    
    # Debug: log tool execution results
    logger.info(f"custom_tool_node: {len(tool_messages)} messages after tool execution")
    for i, msg in enumerate(tool_messages[len(messages):]):  # Only log new messages
        if isinstance(msg, ToolMessage):
            logger.info(f"  New ToolMessage {i}: {msg.content[:100] if msg.content else 'No content'}...")
    
    # Update state with all messages and preserve other state data
    state["messages"] = tool_messages
    return state

# === Graph Setup ===
def create_llm_powered_graph():
    """Create a LLM-powered workflow with LangGraph checkpointing."""
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("parse_arguments", parse_arguments)
    workflow.add_node("agent_with_tools", agent_with_tools)
    workflow.add_node("agent_final_response", agent_final_response)
    workflow.add_node("tools", custom_tool_node)  # Use custom tool node
    
    # Set entry point
    workflow.set_entry_point("analyze_intent")
    
    # Add sequential edges
    workflow.add_edge("analyze_intent", "parse_arguments")
    workflow.add_edge("parse_arguments", "agent_with_tools")
    workflow.add_edge("tools", "agent_final_response")  # After tools, go to final response
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent_with_tools",
        should_continue,  # Decides: tools -> "tools" or no tools -> END
    )
    workflow.add_edge("agent_final_response", END)  # Final response always ends
    
    # Compile with memory saver for checkpointing
    memory_saver = MemorySaver()
    return workflow.compile(checkpointer=memory_saver)

# Create the agent
agent = create_llm_powered_graph()

class SimplifiedChatbot:
    """
    A LLM-powered chatbot with intelligent workflow and proper error handling.
    """
    
    SUPPORTED_CONTENT_TYPES = ['text/plain']
    
    def __init__(self):
        self.agent = agent

    def _get_last_ai_message(self, messages) -> str:
        """Extract the last AI message content."""
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content
        return "Xin lỗi, tôi không thể tạo phản hồi."

    def process_message(self, message: str, session_id: str = None) -> str:
        """
        Processes a single user message through the LLM-powered workflow with conversation history.
        """
        if not message or not message.strip():
            return "Xin lỗi, tôi không nhận được tin nhắn nào."
        
        # Use default session if none provided
        if not session_id:
            session_id = "default"
            
        logger.info(f"Processing message for session {session_id}: '{message[:100]}...'")
        
        try:
            # Get conversation history
            memory = get_or_create_memory(session_id)
            
            # Get existing messages from memory
            history_messages = []
            if memory.chat_memory.messages:
                history_messages = memory.chat_memory.messages
            
            # Create new user message
            user_message = HumanMessage(content=message.strip())
            
            # Create initial state with history + new message
            all_messages = history_messages + [user_message]
            state = {"messages": all_messages}
            
            logger.info(f"Processing with {len(all_messages)} total messages ({len(history_messages)} from history)")
            
            # Run the LLM-powered workflow
            result = self.agent.invoke(state)
            
            # Extract final messages and response
            final_messages = result.get("messages", [])
            response = self._get_last_ai_message(final_messages)
            
            # Store conversation in memory using LangChain's save_context
            memory.save_context(
                {"input": message.strip()},
                {"output": response}
            )
            
            logger.info(f"Final response for session {session_id}: '{response[:100]}...'")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn: {str(e)}"

    async def stream(self, query: str, context_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Streams the agent's response through the LLM-powered workflow with conversation history.
        """
        if not query or not query.strip():
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': "Xin lỗi, tôi không nhận được tin nhắn nào."
            }
            return
            
        logger.info(f"Streaming message for session {context_id}: '{query[:100]}...'")

        try:
            # Get conversation history
            memory = get_or_create_memory(context_id)
            
            # Get existing messages from memory
            history_messages = []
            if memory.chat_memory.messages:
                history_messages = memory.chat_memory.messages
            
            # Create new user message
            user_message = HumanMessage(content=query.strip())
            
            # Create initial state with history + new message
            all_messages = history_messages + [user_message]
            state = {"messages": all_messages}
            
            logger.info(f"Streaming with {len(all_messages)} total messages ({len(history_messages)} from history)")
            
            # Stream through the LLM-powered workflow
            config = {"configurable": {"thread_id": context_id}}
            
            # Track final response for memory storage
            final_response = None
            
            async for chunk in self.agent.astream(state, config=config):
                logger.debug(f"Received chunk: {chunk}")
                
                # Skip start chunk
                if "__start__" in chunk:
                    continue
                
                # Handle different workflow steps
                if "analyze_intent" in chunk:
                    intent_info = chunk.get("analyze_intent", {}).get("intent_info", {})
                    if intent_info:
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': f'🎯 Phân tích: {intent_info.get("description", "N/A")} ({intent_info.get("confidence", 0):.0%})',
                        }
                
                elif "parse_arguments" in chunk:
                    parsed_args = chunk.get("parse_arguments", {}).get("parsed_args", {})
                    if parsed_args.get("entities"):
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': f'🔍 Trích xuất: {parsed_args["entities"]}',
                        }
                    elif parsed_args.get("suggested_action"):
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': f'⚡ Chuẩn bị: {parsed_args["suggested_action"]}',
                        }
                
                elif "agent_with_tools" in chunk:
                    messages = chunk.get("agent_with_tools", {}).get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        
                        # If it's an AI message with tool calls
                        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            tool_names = [call.get('name', 'unknown') for call in last_message.tool_calls]
                            yield {
                                'is_task_complete': False,
                                'require_user_input': False,
                                'content': f'🛠️ Thực hiện: {", ".join(tool_names)}...',
                            }
                        # If it's a final AI response
                        elif isinstance(last_message, AIMessage) and (not hasattr(last_message, 'tool_calls') or not last_message.tool_calls):
                            response_content = last_message.content
                            if response_content:
                                final_response = response_content
                                logger.info(f"Final streamed response for session {context_id}: '{response_content[:100]}...'")
                                yield {
                                    'is_task_complete': True,
                                    'require_user_input': False,
                                    'content': response_content
                                }
                
                elif "agent_final_response" in chunk:
                    messages = chunk.get("agent_final_response", {}).get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        
                        # If it's a final AI response
                        if isinstance(last_message, AIMessage) and (not hasattr(last_message, 'tool_calls') or not last_message.tool_calls):
                            response_content = last_message.content
                            if response_content:
                                final_response = response_content
                                logger.info(f"Final streamed response for session {context_id}: '{response_content[:100]}...'")
                                yield {
                                    'is_task_complete': True,
                                    'require_user_input': False,
                                    'content': response_content
                                }
                
                elif "tools" in chunk:
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': '💾 Xử lý dữ liệu...',
                    }
            
            # Store conversation in memory after completion
            if final_response:
                memory.save_context(
                    {"input": query.strip()},
                    {"output": final_response}
                )
                logger.info(f"Stored conversation for session {context_id}")

        except Exception as e:
            logger.error(f"Error in stream method for session {context_id}: {e}", exc_info=True)
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f"❌ Lỗi: {str(e)}"
            }

    def clear_conversation(self, session_id: str) -> str:
        """Clear conversation history for a session."""
        if session_id in session_memories:
            session_memories[session_id].clear()
            logger.info(f"Cleared memory for session {session_id}")
        return f"Đã xóa lịch sử trò chuyện cho session {session_id}."
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        total_messages = 0
        for memory in session_memories.values():
            total_messages += len(memory.chat_memory.messages)
        
        return {
            "active_sessions": len(session_memories),
            "total_messages": total_messages,
            "memory_limit_per_session": 10 * 2  # k=10 means 10 exchanges = 20 messages
        }
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session in a readable format."""
        if session_id not in session_memories:
            return []
        
        memory = session_memories[session_id]
        history = memory.chat_memory.messages
        readable_history = []
        
        for msg in history:
            if isinstance(msg, HumanMessage):
                readable_history.append({
                    "type": "user",
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None)
                })
            elif isinstance(msg, AIMessage):
                readable_history.append({
                    "type": "assistant", 
                    "content": msg.content,
                    "tool_calls": getattr(msg, 'tool_calls', None),
                    "timestamp": getattr(msg, 'timestamp', None)
                })
            elif isinstance(msg, ToolMessage):
                readable_history.append({
                    "type": "tool",
                    "content": msg.content,
                    "tool_call_id": getattr(msg, 'tool_call_id', None),
                    "timestamp": getattr(msg, 'timestamp', None)
                })
        
        return readable_history

# Singleton instance
simplified_chatbot_instance = SimplifiedChatbot()