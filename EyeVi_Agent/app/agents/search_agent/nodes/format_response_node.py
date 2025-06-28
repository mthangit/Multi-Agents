from typing import Dict, Any, Optional, List
import logging
import json
import traceback

from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.search_prompts import (
    SEARCH_RESPONSE_PROMPT,
    SEARCH_RESPONSE_IMAGE_PROMPT,
    SEARCH_RESPONSE_NO_RESULTS_PROMPT,
    SEARCH_RESPONSE_IRRELEVANT_IMAGE_PROMPT,
    SEARCH_RESPONSE_COMBINED_PROMPT
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormatResponseNode:
    """Node định dạng kết quả tìm kiếm thành phản hồi cho người dùng."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo node định dạng phản hồi.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.4,
        )
        logger.info("FormatResponseNode đã được khởi tạo")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Định dạng kết quả tìm kiếm thành phản hồi.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa phản hồi cuối cùng
        """
        # Lấy thông tin từ state
        search_results = state.get("search_results", [])
        normalized_query = state.get("normalized_query", "")
        original_query = state.get("original_query", "")  # Lấy query gốc của người dùng
        search_type = state.get("search_type", "text")
        image_analysis = state.get("image_analysis", {})
        text_normalized_query = state.get("text_normalized_query", "")
        image_normalized_query = state.get("image_normalized_query", "")
        
        logger.info(f"Định dạng phản hồi cho loại tìm kiếm: {search_type}")
        logger.info(f"Query gốc: {original_query}")
        logger.info(f"Query chuẩn hóa: {normalized_query}")
        logger.info(f"Text normalized query: {text_normalized_query}")
        logger.info(f"Image normalized query: {image_normalized_query}")
        logger.info(f"Số lượng kết quả: {len(search_results)}")
        
        try:
            # Kiểm tra nếu có lỗi
            if state.get("error"):
                logger.error(f"Lỗi từ các node trước: {state['error']}")
                return {
                    "final_response": {
                        "error": state["error"],
                        "products": [],
                        "count": 0,
                        "summary": "Xin lỗi, đã xảy ra lỗi khi tìm kiếm sản phẩm."
                    }
                }
            
            # Kiểm tra nếu không có kết quả
            if not search_results:
                logger.info("Không có kết quả tìm kiếm, tạo phản hồi thông báo")
                llm_response = self._generate_no_results_response(
                    original_query or normalized_query, 
                    search_type
                )
                return {
                    "final_response": {
                        "products": [],
                        "count": 0,
                        "summary": "Không tìm thấy sản phẩm phù hợp.",
                        "llm_response": llm_response
                    }
                }
            
            # Tạo phản hồi dựa trên loại tìm kiếm
            if search_type == "image":
                logger.info("Sử dụng prompt cho tìm kiếm bằng hình ảnh")
                llm_response = self._generate_image_search_response(
                    search_results, 
                    image_analysis,
                    original_query
                )
            elif search_type == "combined":
                logger.info("Sử dụng prompt cho tìm kiếm kết hợp")
                llm_response = self._generate_combined_search_response(
                    search_results,
                    original_query,
                    text_normalized_query,
                    image_normalized_query,
                    image_analysis
                )
            else:
                logger.info("Sử dụng prompt cho tìm kiếm bằng văn bản")
                llm_response = self._generate_text_search_response(
                    search_results, 
                    original_query or normalized_query
                )
            
            # Tạo kết quả cuối cùng
            final_response = {
                "products": search_results,
                "count": len(search_results),
                "llm_response": llm_response,
                "search_type": search_type
            }
            
            logger.info("Đã tạo phản hồi cuối cùng")
            return {"final_response": final_response}
            
        except Exception as e:
            logger.error(f"Lỗi khi định dạng phản hồi: {e}")
            logger.error(traceback.format_exc())
            return {
                "final_response": {
                    "error": str(e),
                    "products": search_results,
                    "count": len(search_results),
                    "summary": "Đã xảy ra lỗi khi định dạng kết quả tìm kiếm."
                }
            }
    
    def _generate_text_search_response(
        self, 
        search_results: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """
        Tạo phản hồi cho tìm kiếm bằng văn bản.
        
        Args:
            search_results: Danh sách kết quả tìm kiếm
            query: Câu truy vấn tìm kiếm
            
        Returns:
            Phản hồi dạng văn bản
        """
        try:
            # Giới hạn số lượng sản phẩm để đưa vào prompt
            limited_results = search_results[:5]
            
            # Tạo prompt
            prompt = SEARCH_RESPONSE_PROMPT.format(
                query=query,
                products=json.dumps(limited_results, ensure_ascii=False, indent=2)
            )
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            logger.info("Đã nhận phản hồi từ LLM")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi cho tìm kiếm văn bản: {e}")
            return f"Tìm thấy {len(search_results)} sản phẩm phù hợp với yêu cầu của bạn."
    
    def _generate_image_search_response(
        self, 
        search_results: List[Dict[str, Any]], 
        image_analysis: Dict[str, Any],
        original_query: str = ""
    ) -> str:
        """
        Tạo phản hồi cho tìm kiếm bằng hình ảnh.
        
        Args:
            search_results: Danh sách kết quả tìm kiếm
            image_analysis: Kết quả phân tích hình ảnh
            original_query: Câu truy vấn gốc của người dùng (nếu có)
            
        Returns:
            Phản hồi dạng văn bản
        """
        try:
            # Kiểm tra xem hình ảnh có chứa kính mắt không
            contains_eyewear = image_analysis.get("contains_eyewear", False)
            
            if not contains_eyewear:
                # Tạo phản hồi cho trường hợp hình ảnh không chứa kính mắt
                logger.info("Hình ảnh không chứa kính mắt, sử dụng prompt cho hình ảnh không liên quan")
                prompt = SEARCH_RESPONSE_IRRELEVANT_IMAGE_PROMPT.format(
                    image_analysis=json.dumps(image_analysis, ensure_ascii=False, indent=2)
                )
            else:
                # Tạo phản hồi bình thường cho hình ảnh có chứa kính mắt
                logger.info("Hình ảnh có chứa kính mắt, sử dụng prompt tìm kiếm hình ảnh thông thường")
                # Giới hạn số lượng sản phẩm để đưa vào prompt
                limited_results = search_results[:5]
                
                # Tạo prompt
                prompt = SEARCH_RESPONSE_IMAGE_PROMPT.format(
                    user_query=original_query,
                    image_analysis=json.dumps(image_analysis, ensure_ascii=False, indent=2),
                    products=json.dumps(limited_results, ensure_ascii=False, indent=2)
                )
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            logger.info("Đã nhận phản hồi từ LLM")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi cho tìm kiếm hình ảnh: {e}")
            return f"Tìm thấy {len(search_results)} sản phẩm phù hợp với hình ảnh bạn đã gửi."
    
    def _generate_combined_search_response(
        self,
        search_results: List[Dict[str, Any]],
        original_query: str,
        text_query: str,
        image_query: str,
        image_analysis: Dict[str, Any]
    ) -> str:
        """
        Tạo phản hồi cho tìm kiếm kết hợp (text + image).
        
        Args:
            search_results: Danh sách kết quả tìm kiếm
            original_query: Câu truy vấn gốc của người dùng
            text_query: Query từ phân tích text
            image_query: Query từ phân tích image
            image_analysis: Kết quả phân tích hình ảnh
            
        Returns:
            Phản hồi dạng văn bản
        """
        try:
            # Kiểm tra xem hình ảnh có chứa kính mắt không
            contains_eyewear = image_analysis.get("contains_eyewear", False)
            
            if not contains_eyewear:
                # Nếu hình ảnh không chứa kính mắt, sử dụng kết quả tìm kiếm văn bản
                logger.info("Hình ảnh không chứa kính mắt, sử dụng kết quả tìm kiếm văn bản")
                return self._generate_text_search_response(search_results, original_query)
            
            # Giới hạn số lượng sản phẩm để đưa vào prompt
            limited_results = search_results[:5]
            logger.info(f"Kết quả tìm kiếm: {limited_results}")
            # Tạo prompt cho tìm kiếm kết hợp
            prompt = SEARCH_RESPONSE_COMBINED_PROMPT.format(
                user_query=original_query,
                text_query=text_query,
                image_query=image_query,
                image_analysis=json.dumps(image_analysis, ensure_ascii=False, indent=2),
                products=json.dumps(limited_results, ensure_ascii=False, indent=2)
            )
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            logger.info("Đã nhận phản hồi từ LLM cho tìm kiếm kết hợp")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi cho tìm kiếm kết hợp: {e}")
            return f"Tìm thấy {len(search_results)} sản phẩm phù hợp với yêu cầu kết hợp của bạn."
    
    def _generate_no_results_response(self, query: str, search_type: str) -> str:
        """
        Tạo phản hồi khi không có kết quả tìm kiếm.
        
        Args:
            query: Câu truy vấn tìm kiếm
            search_type: Loại tìm kiếm
            
        Returns:
            Phản hồi dạng văn bản
        """
        try:
            # Tạo prompt
            prompt = SEARCH_RESPONSE_NO_RESULTS_PROMPT.format(
                query=query,
                search_type=search_type
            )
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            logger.info("Đã nhận phản hồi từ LLM cho trường hợp không có kết quả")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi cho trường hợp không có kết quả: {e}")
            return "Xin lỗi, chúng tôi không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn."

# Hàm tiện ích để tạo node
def get_format_response_node(api_key: Optional[str] = None) -> FormatResponseNode:
    """
    Tạo một instance của FormatResponseNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        FormatResponseNode instance
    """
    return FormatResponseNode(api_key=api_key) 