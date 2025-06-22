from typing import Dict, Any, Optional
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.search_prompts import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

class IntentClassifierNode:
    """Node phân loại intent từ query của người dùng."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo node phân loại intent.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.1  # thấp để đảm bảo kết quả ổn định
        )
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân loại intent từ query của người dùng.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa intent được phân loại
        """
        # Lấy query từ state
        query = state.get("query", "")
        
        # Kiểm tra nếu query rỗng
        if not query:
            logger.warning("Query rỗng, không thể phân loại intent")
            return {"intent": "unknown"}
        
        try:
            # Chuẩn bị prompt
            prompt = INTENT_CLASSIFICATION_PROMPT.format(message=query)
            
            # Gọi LLM để phân loại intent
            response = self.llm.invoke(prompt)
            intent = response.content.strip().lower()
            
            logger.info(f"Đã phân loại intent: '{intent}' cho query: '{query}'")
            
            # Cập nhật state với intent đã phân loại
            return {"intent": intent}
        
        except Exception as e:
            logger.error(f"Lỗi khi phân loại intent: {e}")
            return {"intent": "unknown", "error": str(e)}

# Hàm tiện ích để tạo node
def get_intent_classifier_node(api_key: Optional[str] = None) -> IntentClassifierNode:
    """
    Tạo một instance của IntentClassifierNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        IntentClassifierNode instance
    """
    return IntentClassifierNode(api_key=api_key) 