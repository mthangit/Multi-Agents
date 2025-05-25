import json
import logging
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings
from src.chatbot.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    PARAMETER_EXTRACTION_PROMPT,
    RESPONSE_GENERATION_PROMPT
)

# Thiết lập logger
logger = logging.getLogger("chatbot_debug")

# Khởi tạo LLM Gemini từ settings
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)

def process_llm_json_output(text, intent, message):
    """
    Xử lý output từ LLM để trích xuất JSON, xử lý nhiều trường hợp khác nhau
    
    Args:
        text (str): Chuỗi đầu ra từ LLM
        intent (str): Intent hiện tại
        message (str): Message gốc của user
        
    Returns:
        dict: Dictionary chứa các parameters đã trích xuất
    """    
    # 1. Tạo default parameters dựa trên intent
    default_params = {}
    if intent == "view_cart" or intent == "clear_cart" or intent == "start_order":
        default_params = {"user_id": 1}
    
    # 2. Xử lý trường hợp kết quả có dạng ```json ... ```
    clean_text = text
    if "```json" in text and "```" in text:
        try:
            # Trích xuất nội dung giữa ```json và ```
            json_content = text.split("```json")[1].split("```")[0].strip()
            clean_text = json_content
            logger.info(f"Extracted JSON from code block: {clean_text}")
        except Exception as e:
            logger.warning(f"Failed to extract JSON from code block: {e}")
    
    # 3. Xử lý trường hợp kết quả có dạng ```{...}```
    elif "```" in text:
        try:
            # Trích xuất nội dung giữa ``` và ```
            json_content = text.split("```")[1].strip()
            clean_text = json_content
            logger.info(f"Extracted content from code block: {clean_text}")
        except Exception as e:
            logger.warning(f"Failed to extract content from code block: {e}")
    
    # 4. Xử lý các trường hợp đặc biệt trước khi parse JSON
    # 4.1 Trường hợp trả về "name" hoặc tên trường khác
    if clean_text.strip().startswith('"') and clean_text.strip().endswith('"'):
        field_name = clean_text.strip('"').lower()
        logger.info(f"Detected simple field name: '{field_name}'")
        
        # Nếu là field "name" và intent là find_product_by_name
        if field_name == "name" and intent == "find_product_by_name":
            return extract_product_name_from_message(message)
            
        # Các field khác
        if field_name in ["product_id", "order_id", "user_id", "quantity"]:
            logger.warning(f"Simple field name '{field_name}' without value, using defaults")
            return default_params
    
    # 5. Thử parse JSON tiêu chuẩn
    try:
        parameters = json.loads(clean_text)
        if isinstance(parameters, dict):
            logger.info(f"Successfully parsed JSON: {parameters}")
            return parameters
        else:
            logger.warning(f"Parsed JSON is not a dictionary: {parameters}")
            return default_params
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        
        # 6. Xử lý các trường hợp không parse được JSON
        # 6.1 Nếu intent là find_product_by_name
        if intent == "find_product_by_name":
            # Mẫu 1: "name": "Kính Mát Nữ"
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', clean_text)
            if name_match:
                product_name = name_match.group(1)
                logger.info(f"Extracted product name using pattern 1: {product_name}")
                return {"name": product_name}
            
            # Mẫu 2: name: Kính Mát Nữ
            name_match2 = re.search(r'name\s*:\s*([^,\n\r]+)', clean_text)
            if name_match2:
                product_name = name_match2.group(1).strip().strip('"\'')
                logger.info(f"Extracted product name using pattern 2: {product_name}")
                return {"name": product_name}
            
            # Mẫu 3: Trực tiếp từ tin nhắn
            return extract_product_name_from_message(message)
        
        # 6.2 Nếu intent là find_product_by_id
        elif intent == "find_product_by_id":
            # Tìm số trong text
            id_match = re.search(r'\b(\d+)\b', clean_text)
            if id_match:
                product_id = id_match.group(1)
                logger.info(f"Extracted product ID: {product_id}")
                return {"product_id": product_id}
        
        # 6.3 Nếu intent là add_to_cart
        elif intent == "add_to_cart":
            # Tìm product_id và quantity
            product_id_match = re.search(r'product_id\s*[=:]\s*(\d+)', clean_text, re.IGNORECASE)
            quantity_match = re.search(r'quantity\s*[=:]\s*(\d+)', clean_text, re.IGNORECASE)
            
            result = {}
            if product_id_match:
                result["product_id"] = product_id_match.group(1)
            if quantity_match:
                result["quantity"] = int(quantity_match.group(1))
                
            if result:
                logger.info(f"Extracted add_to_cart parameters: {result}")
                return result
    
    # 7. Fallback: dùng default parameters
    logger.info(f"Using default parameters for intent {intent}: {default_params}")
    return default_params


def extract_product_name_from_message(message):
    """Trích xuất tên sản phẩm từ message gốc"""
    try:
        # Pattern 1: "tìm sản phẩm tên là X"
        product_regex1 = re.compile(r'(?:tìm|kiếm|sản phẩm|tên).*?(?:là|có tên|có tên là|:)?\s+([^.?!]+)', re.IGNORECASE)
        match1 = product_regex1.search(message)
        if match1:
            product_name = match1.group(1).strip()
            logger.info(f"Extracted product name from message (pattern 1): {product_name}")
            return {"name": product_name}
            
        # Pattern 2: "X là gì", "cần tìm X"
        product_regex2 = re.compile(r'([\w\s]+)(?:\s+là gì|\s+có|cần tìm\s+)', re.IGNORECASE)
        match2 = product_regex2.search(message)
        if match2:
            product_name = match2.group(1).strip()
            logger.info(f"Extracted product name from message (pattern 2): {product_name}")
            return {"name": product_name}
            
        # Pattern 3: Lấy từ cuối cùng, thường là tên sản phẩm
        words = message.split()
        if words:
            last_part = " ".join(words[-min(3, len(words)):])
            logger.info(f"Using last part of message as product name: {last_part}")
            return {"name": last_part}
            
    except Exception as ex:
        logger.warning(f"Failed to extract product name from message: {ex}")
    
    # Fallback: sử dụng toàn bộ message làm tên
    return {"name": message.strip()}


def intent_classification_node(state):
    """Node phân tích và xác định intent từ message của user với context"""
    message = state["message"]
    context_summary = state.get("context_summary", "")
    
    # Enhanced prompt với context
    enhanced_prompt = f"""
{INTENT_CLASSIFICATION_PROMPT.format(message=message)}

## Context từ cuộc trò chuyện:
{context_summary}

Xem xét context trên để hiểu rõ hơn ý định của user.
"""
    
    # Gọi LLM để nhận intent
    intent = llm.invoke(enhanced_prompt).content.strip().lower()
    logger.info(f"Classified intent: '{intent}'")
    
    # Cập nhật state với intent
    return {"intent": intent}

def parameter_extraction_node(state):
    """Node trích xuất tham số từ message dựa trên intent đã xác định"""
    message = state["message"]
    intent = state["intent"]
    logger.info(f"Parameter extraction for intent: '{intent}'")
    
    # Format prompt với message và intent
    prompt = PARAMETER_EXTRACTION_PROMPT.format(message=message, intent=intent)
    
    # Gọi LLM để trích xuất tham số
    result = llm.invoke(prompt).content
    
    # Xử lý kết quả bằng hàm chuyên biệt
    parameters = process_llm_json_output(result, intent, message)
    logger.info(f"Final extracted parameters: {parameters}")
    
    return {"parameters": parameters}

def generate_response_node(state):
    """Node tạo câu trả lời cuối cùng từ kết quả xử lý với context"""
    message = state["message"]
    intent = state["intent"]
    context_summary = state.get("context_summary", "")
    logger.info(f"Generating response for intent: '{intent}'")
    
    # Tạo result dict từ các trường dữ liệu trong state
    result = {}
    if state.get("product"):
        result["product"] = state["product"]
    if state.get("products"):
        result["products"] = state["products"]
    if state.get("order_id"):
        result["order_id"] = state["order_id"]
    if state.get("order"):
        result["order"] = state["order"]
    if state.get("error"):
        result["error"] = state["error"]    
    # Enhanced prompt với context
    enhanced_prompt = f"""
{RESPONSE_GENERATION_PROMPT.format(message=message, intent=intent, result=result)}

## Context từ cuộc trò chuyện:
{context_summary}

Hãy tạo phản hồi tự nhiên dựa trên context và kết quả xử lý. Nếu có liên quan đến cuộc trò chuyện trước đó, hãy tham chiếu một cách tự nhiên mà không lặp lại nội dung cũng như câu hỏi của user.
"""
    
    # Gọi LLM để tạo câu trả lời
    response = llm.invoke(enhanced_prompt).content
    
    # Cập nhật state với response
    return {"response": response} 