import os
import logging
from typing import Dict, List, Optional, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from .tools.search_tools import get_search_tools
from .prompts.search_prompts import SEARCH_AGENT_PROMPT, get_search_prompt_with_analysis
from .chains.search_chain import SearchChain


# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchAgent:
    """Agent tìm kiếm sản phẩm kính mắt.
    
    Cung cấp khả năng tìm kiếm sản phẩm kính mắt dựa trên văn bản và/hoặc hình ảnh.
    Có thể kết hợp với phân tích khuôn mặt từ host agent để tìm kiếm sản phẩm phù hợp.
    """
    
    def __init__(self, api_key=None, streaming=True):
        """Khởi tạo SearchAgent.
        
        Args:
            api_key: API key cho mô hình LLM (mặc định lấy từ biến môi trường GOOGLE_API_KEY)
            streaming: Bật/tắt chế độ streaming kết quả
        """
        # Lấy API key từ biến môi trường nếu không được cung cấp
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.streaming = streaming
        
        # Khởi tạo search chain
        self.search_chain = SearchChain(api_key=self.api_key, streaming=streaming)
    
    async def process_request(
        self, 
        query_text: Optional[str] = None, 
        image_data: Optional[bytes] = None, 
        analysis_result: Optional[Dict] = None,
        callbacks: Optional[List] = None
    ) -> Dict[str, Any]:
        """Xử lý yêu cầu tìm kiếm từ người dùng hoặc host agent.
        
        Args:
            query_text: Văn bản truy vấn từ người dùng
            image_data: Dữ liệu hình ảnh (nếu có)
            analysis_result: Kết quả phân tích khuôn mặt từ host agent (nếu có)
            callbacks: Các callback handler (cho streaming)
            
        Returns:
            Kết quả tìm kiếm sản phẩm định dạng JSON
        """
        logger.info(f"Xử lý yêu cầu tìm kiếm: {query_text}")
        
        # Áp dụng callback streaming nếu được bật
        if self.streaming and not callbacks:
            callbacks = [StreamingStdOutCallbackHandler()]
        
        # Lọc analysis_result để đảm bảo định dạng chính xác
        filtered_analysis = self._validate_analysis_result(analysis_result)
        
        # Gọi search chain để xử lý yêu cầu
        try:
            result = await self.search_chain.arun(
                query=query_text,
                image_data=image_data,
                analysis_result=filtered_analysis,
                callbacks=callbacks
            )
            return self._format_response(result)
        except Exception as e:
            logger.error(f"Lỗi khi xử lý yêu cầu tìm kiếm: {str(e)}")
            return self._format_error_response(str(e))
    
    def _validate_analysis_result(self, analysis_result: Optional[Dict]) -> Optional[Dict]:
        """Xác thực và lọc kết quả phân tích khuôn mặt.
        
        Args:
            analysis_result: Kết quả phân tích khuôn mặt từ host agent
            
        Returns:
            Kết quả phân tích đã được xác thực
        """
        if not analysis_result:
            return None
        
        # Kiểm tra các trường bắt buộc
        required_fields = ["face_detected"]
        for field in required_fields:
            if field not in analysis_result:
                logger.warning(f"Kết quả phân tích thiếu trường {field}")
                return None
        
        # Xác thực face_detected
        if not analysis_result.get("face_detected"):
            logger.info("Không phát hiện khuôn mặt trong kết quả phân tích")
        
        return analysis_result
    
    def _format_response(self, result: Dict) -> Dict:
        """Định dạng kết quả để trả về cho người dùng hoặc host agent.
        
        Args:
            result: Kết quả từ search_chain
            
        Returns:
            Kết quả đã được định dạng
        """
        # Đảm bảo kết quả luôn có định dạng nhất quán
        response = {
            "success": True,
            "results": result.get("results", {}) or {},
            "analysis": result.get("analysis", None),
            "message": result.get("message", "")
        }
        
        # Đảm bảo results có các trường bắt buộc
        if "results" in response and isinstance(response["results"], dict):
            if "summary" not in response["results"]:
                response["results"]["summary"] = "Kết quả tìm kiếm sản phẩm kính mắt."
            
            if "products" not in response["results"]:
                response["results"]["products"] = []
            
            if "count" not in response["results"]:
                response["results"]["count"] = len(response["results"].get("products", []))
        
        return response
    
    def _format_error_response(self, error_message: str) -> Dict:
        """Định dạng thông báo lỗi.
        
        Args:
            error_message: Thông báo lỗi
            
        Returns:
            Thông báo lỗi đã được định dạng
        """
        return {
            "success": False,
            "results": {
                "products": [],
                "count": 0,
                "summary": "Đã xảy ra lỗi khi tìm kiếm sản phẩm."
            },
            "message": f"Lỗi: {error_message}"
        }
