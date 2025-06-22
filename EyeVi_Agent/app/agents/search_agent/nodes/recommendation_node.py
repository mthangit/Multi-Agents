from typing import Dict, Any, Optional, List
import logging
import traceback
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.search_prompts import RECOMMENDATION_PROMPT

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationNode:
    """Node tư vấn sản phẩm dựa trên cuộc trò chuyện."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo node tư vấn.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7,  # Nhiệt độ cao hơn để tạo ra câu trả lời đa dạng
            streaming=False
        )
        logger.info("RecommendationNode đã được khởi tạo")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tư vấn sản phẩm dựa trên query của người dùng.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa kết quả tư vấn
        """
        # Lấy query từ state
        query = state.get("query", "")
        original_query = state.get("original_query", query)
        
        # Kiểm tra nếu query rỗng
        if not query:
            logger.warning("Query rỗng, không thể tư vấn")
            return {
                "final_response": {
                    "text": "Xin lỗi, tôi không hiểu bạn muốn tư vấn về điều gì. Vui lòng cung cấp thêm thông tin."
                }
            }
        
        try:
            # Gọi LLM để tư vấn
            formatted_prompt = RECOMMENDATION_PROMPT.replace("{query}", query)
            response = self.llm.invoke(formatted_prompt)
            
            # Log phản hồi từ LLM
            logger.info(f"Phản hồi tư vấn từ LLM:\n{response.content[:200]}...")
            
            return {
                "recommendation": response.content,
                "final_response": {"text": response.content}
            }
        
        except Exception as e:
            logger.error(f"Lỗi khi tư vấn: {e}")
            logger.error(f"Chi tiết lỗi: {traceback.format_exc()}")
            return {
                "final_response": {
                    "text": "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn."
                },
                "error": str(e)
            }

# Hàm tiện ích để tạo node
def get_recommendation_node(api_key: Optional[str] = None) -> RecommendationNode:
    """
    Tạo một instance của RecommendationNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        RecommendationNode instance
    """
    return RecommendationNode(api_key=api_key) 