from typing import Dict, Any, Optional, List
import logging
from collections import defaultdict
import os
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

class FormatResponseNode:
    """Node xử lý kết quả tìm kiếm và tạo phản hồi cho client."""
    
    def __init__(self, api_key=None):
        """
        Khởi tạo FormatResponseNode.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.llm = None
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        else:
            logger.warning("GOOGLE_API_KEY không được cung cấp, sẽ không sử dụng LLM")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý kết quả tìm kiếm và tạo phản hồi.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa phản hồi đã được định dạng
        """
        # Lấy thông tin từ state
        search_results = state.get("search_results", [])
        query = state.get("query", "")
        normalized_query = state.get("normalized_query", "")
        extracted_attributes = state.get("extracted_attributes", {})
        
        # Lấy recommended_shapes từ extracted_attributes
        recommended_shapes = extracted_attributes.get("recommended_shapes", [])
        
        # Định dạng kết quả
        formatted_response = self._format_search_results(
            results=search_results,
            query_text=query or normalized_query,
            recommended_shapes=recommended_shapes
        )
        
        # Tạo câu trả lời từ LLM
        llm_response = self._generate_llm_response(
            products=formatted_response["products"],
            query=query or normalized_query,
            extracted_attributes=extracted_attributes,
        )
        
        # Thêm câu trả lời LLM vào response
        formatted_response["llm_response"] = llm_response
        
        return {"final_response": formatted_response}
    
    def _format_search_results(
        self, 
        results: List[Dict[str, Any]], 
        query_text: Optional[str] = None,
        recommended_shapes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Định dạng kết quả tìm kiếm thành JSON phù hợp.
        
        Args:
            results: Danh sách kết quả tìm kiếm
            query_text: Văn bản tìm kiếm ban đầu
            recommended_shapes: Các hình dạng gọng kính được đề xuất
            
        Returns:
            Kết quả được định dạng thành JSON
        """
        products = []
        for product in results:
            products.append({
                "product_id": product.get("product_id", ""),
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "price": product.get("price", 0),
                "description": product.get("description", ""),
                "image_url": product.get("images", [""])[0] if product.get("images") else "",
                "frame_color": product.get("color", ""),
                "category": product.get("category", ""),
                "gender": product.get("gender", ""),
                "score": product.get("score", 0),
            })

        return {
            "products": products,
            "count": len(products),
        }
    
    def _generate_llm_response(
        self,
        products: List[Dict[str, Any]],
        query: str,
        extracted_attributes: Dict[str, Any],
    ) -> str:
        """
        Tạo câu trả lời từ LLM dựa trên kết quả tìm kiếm.
        
        Args:
            products: Danh sách sản phẩm
            query: Câu truy vấn gốc
            extracted_attributes: Các thuộc tính được trích xuất
            summary: Tóm tắt kết quả tìm kiếm
            
        Returns:
            Câu trả lời từ LLM
        """
        summary = "Không tìm thấy sản phẩm, bạn hãy tìm lại thử xem, Eyevi sẽ hỗ trợ bạn tìm kiếm sản phẩm phù hợp nhất."
        if not self.llm or not products:
            # Nếu không có LLM hoặc không có sản phẩm, trả về summary
            return summary
        
        try:
            # Tạo prompt cho LLM
            prompt = self._create_llm_prompt(products, query, extracted_attributes)
            
            # Gọi LLM để tạo câu trả lời
            from langchain.schema import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content="""Bạn là Eyevi - chatbot chuyên gia tư vấn kính mắt cho cửa hàng thương mại điện tử. 
                Hãy trả lời câu hỏi của khách hàng dựa trên kết quả tìm kiếm sản phẩm.
                Hãy viết câu trả lời thân thiện, gần gũi với khách hàng, chuyên nghiệp và giải thích tại sao những sản phẩm này phù hợp với yêu cầu của khách hàng. Trả lời như một sale chuyên nghiệp, dùng kỹ năng bán hàng tuyệt đỉnh để khách hàng đọc và muốn mua. Đ
                Đưa ra lời khuyên về việc lựa chọn kính phù hợp dựa trên thông tin đã cung cấp.
                Trả lời bằng tiếng Việt nhé."""),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo câu trả lời từ LLM: {e}")
            return summary
    
    def _create_llm_prompt(
        self,
        products: List[Dict[str, Any]],
        query: str,
        extracted_attributes: Dict[str, Any],
    ) -> str:
        """
        Tạo prompt cho LLM.
        
        Args:
            products: Danh sách sản phẩm
            query: Câu truy vấn gốc
            extracted_attributes: Các thuộc tính được trích xuất
            summary: Tóm tắt kết quả tìm kiếm
            
        Returns:
            Prompt cho LLM
        """
        # Tạo thông tin chi tiết về các sản phẩm (tối đa 5 sản phẩm)
        product_details = []
        for i, product in enumerate(products[:5], 1):
            detail = f"""
            Sản phẩm {i}:
            - Mô tả: {product['description']}
            """
            product_details.append(detail)
        
        # Tạo thông tin về các thuộc tính được trích xuất
        attribute_details = []
        for key, value in extracted_attributes.items():
            if value and key != "recommended_shapes":
                attribute_details.append(f"- {key}: {value}")
        
        # Tạo prompt
        prompt = f"""
        Câu hỏi của khách hàng: "{query}"
        
        Các thuộc tính được trích xuất từ câu hỏi:
        {chr(10).join(attribute_details) if attribute_details else "- Không có thuộc tính cụ thể"}

        Chi tiết các sản phẩm đã tìm dược từ query: 
        {chr(10).join(product_details)}
        
        Hãy tạo một câu trả lời thân thiện và chuyên nghiệp cho khách hàng, giới thiệu các sản phẩm phù hợp và đưa ra lời khuyên về việc lựa chọn kính mắt. Câu trả lời nên ngắn gọn, súc tích nhưng đầy đủ thông tin.
        """
        
        return prompt

# Hàm tiện ích để tạo node
def get_format_response_node(api_key=None) -> FormatResponseNode:
    """
    Tạo một instance của FormatResponseNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        FormatResponseNode instance
    """
    return FormatResponseNode(api_key=api_key) 