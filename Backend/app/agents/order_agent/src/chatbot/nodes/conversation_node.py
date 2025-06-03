from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings
from src.chatbot.prompts import CONVERSATION_STAGE_PROMPT

# Khởi tạo LLM từ settings
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY)

def check_conversation_stage_node(state):
    """Xác định trạng thái hội thoại"""
    conversation_stage = state.get("conversation_stage")
    message = state.get("message", "")
    pending_questions = state.get("pending_questions", [])
    
    # Nếu không có stage hoặc không có pending_questions, không có gì để xử lý
    if not conversation_stage or not pending_questions:
        return {}
    
    # Format prompt
    prompt = CONVERSATION_STAGE_PROMPT.format(
        message=message,
        current_stage=conversation_stage,
        pending_questions=pending_questions
    )
    
    # Gọi LLM để phân tích
    stage = llm.invoke(prompt).content.strip().lower()
    
    # Cập nhật stage nếu có thay đổi
    if stage != conversation_stage:
        return {"conversation_stage": stage}
    
    return {}

def generate_question_node(state):
    """Tạo câu hỏi tiếp theo dựa trên pending_questions"""
    conversation_stage = state.get("conversation_stage")
    pending_questions = state.get("pending_questions", [])
    
    if conversation_stage != "collecting_info" or not pending_questions:
        return {}
    
    # Lấy câu hỏi hiện tại
    current_question = pending_questions[0]
    
    # Map câu hỏi sang prompt
    question_prompts = {
        "shipping_address": "Vui lòng cung cấp địa chỉ giao hàng của bạn:",
        "phone": "Vui lòng cung cấp số điện thoại liên hệ:",
        "payment_method": "Vui lòng chọn phương thức thanh toán (Tiền mặt, Thẻ tín dụng, Chuyển khoản):"
    }
    
    question = question_prompts.get(current_question, f"Vui lòng cung cấp {current_question}:")
    
    return {"response": question} 