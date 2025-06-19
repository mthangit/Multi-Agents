from typing import Dict, List, Any, Optional, TypedDict
import base64
import os
import logging

from langgraph.graph import StateGraph, END


from ..nodes.intent_classifier_node import get_intent_classifier_node
from ..nodes.attribute_extraction_node import get_attribute_extraction_node
from ..nodes.embed_query_node import get_embed_query_node
from ..nodes.semantic_search_node import get_semantic_search_node
from ..nodes.format_response_node import get_format_response_node

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchState(TypedDict):
    """Định nghĩa trạng thái của workflow tìm kiếm."""
    query: Optional[str]
    image_data: Optional[str]
    analysis_result: Optional[Dict[str, Any]]
    intent: Optional[str]
    extracted_attributes: Optional[Dict[str, Any]]
    normalized_query: Optional[str]
    search_type: Optional[str]
    text_embedding: Optional[List[float]]
    image_embedding: Optional[List[float]]
    search_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[Dict[str, Any]]
    error: Optional[str]

class SearchChain:
    """Chain xử lý tìm kiếm sản phẩm kính mắt."""
    
    def __init__(
        self,
        api_key=None,
        streaming=True,
        qdrant_host="localhost",
        qdrant_port=6333,
        custom_model_path=None
    ):
        """Khởi tạo SearchChain.
        
        Args:
            api_key: API key cho mô hình LLM
            streaming: Bật/tắt chế độ streaming
            qdrant_host: Host của Qdrant server
            qdrant_port: Port của Qdrant server
            custom_model_path: Đường dẫn đến mô hình CLIP tùy chỉnh
        """
        # Khởi tạo các node
        self.intent_classifier = get_intent_classifier_node(api_key=api_key)
        self.attribute_extractor = get_attribute_extraction_node(api_key=api_key)
        
        # Đường dẫn đến mô hình tùy chỉnh
        if custom_model_path and not os.path.exists(custom_model_path):
            logger.warning(f"Không tìm thấy mô hình tại {custom_model_path}")
            custom_model_path = None
            
        self.embed_query = get_embed_query_node(custom_model_path=custom_model_path)
        self.semantic_search = get_semantic_search_node(
            qdrant_host="http://eyevi.devsecopstech.click",  # Cố định localhost
            qdrant_port=qdrant_port
        )
        self.format_response = get_format_response_node()
        
        # Xây dựng workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Xây dựng workflow cho việc tìm kiếm."""
        # Khởi tạo StateGraph với SearchState
        workflow = StateGraph(SearchState)
        
        # Thêm các node vào workflow
        workflow.add_node("intent_classifier", self.intent_classifier)
        workflow.add_node("intent_router", self._intent_router)  # Đăng ký intent_router như một node
        workflow.add_node("attribute_extractor", self.attribute_extractor)
        workflow.add_node("embed_query", self.embed_query)
        workflow.add_node("semantic_search", self.semantic_search)
        workflow.add_node("format_response", self.format_response)
        
        # Định nghĩa luồng xử lý
        # Bắt đầu từ intent_classifier
        workflow.set_entry_point("intent_classifier")
        
        # Từ intent_classifier đến intent_router
        workflow.add_edge("intent_classifier", "intent_router")
        
        # Từ intent_router đến attribute_extractor (được xử lý trong _intent_router)
        workflow.add_conditional_edges(
            "intent_router",
            self._route_by_intent,
            {
                "attribute_extractor": "attribute_extractor"
                # Có thể thêm các node khác ở đây trong tương lai
            }
        )
        
        # Từ attribute_extractor đến embed_query
        workflow.add_edge("attribute_extractor", "embed_query")
        
        # Từ embed_query đến semantic_search
        workflow.add_edge("embed_query", "semantic_search")
        
        # Từ semantic_search đến format_response
        workflow.add_edge("semantic_search", "format_response")
        
        # Từ format_response đến END
        workflow.add_edge("format_response", END)
        
        # Biên dịch workflow
        return workflow.compile()
    
    def _intent_router(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node xử lý intent để chuẩn bị cho việc định tuyến.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            State không thay đổi
        """
        # Node này chỉ chuyển tiếp state, việc định tuyến được thực hiện bởi _route_by_intent
        return state
    
    def _route_by_intent(self, state: Dict[str, Any]) -> str:
        """
        Hàm định tuyến dựa trên intent.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Tên của node tiếp theo
        """
        intent = state.get("intent", "unknown")
        logger.info(f"Định tuyến dựa trên intent: {intent}")
        
        # Kiểm tra intent
        if intent == "search_product":
            # Nếu là tìm kiếm sản phẩm, chuyển đến node trích xuất thuộc tính
            return "attribute_extractor"
        elif intent == "product_detail":
            # TODO: Xử lý intent product_detail
            # Hiện tại vẫn chuyển đến attribute_extractor
            logger.warning(f"Intent {intent} chưa được xử lý, sử dụng luồng mặc định")
            return "attribute_extractor"
        elif intent == "compare_products":
            # TODO: Xử lý intent compare_products
            # Hiện tại vẫn chuyển đến attribute_extractor
            logger.warning(f"Intent {intent} chưa được xử lý, sử dụng luồng mặc định")
            return "attribute_extractor"
        else:
            # Các intent khác, vẫn chuyển đến attribute_extractor
            logger.warning(f"Intent {intent} chưa được xử lý, sử dụng luồng mặc định")
            return "attribute_extractor"
    
    async def arun(
        self, 
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict] = None
    ) -> Dict:
        """Chạy workflow tìm kiếm (bất đồng bộ).
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            
        Returns:
            Kết quả tìm kiếm
        """
        initial_state = {
            "query": query,
            "image_data": base64.b64encode(image_data).decode('utf-8') if image_data else None,
            "analysis_result": analysis_result
        }
        
        logger.info(f"Bắt đầu tìm kiếm với query: {query}")
        result = await self.workflow.ainvoke(initial_state)
        return result.get("final_response", {})
    
    def run(
        self, 
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict] = None
    ) -> Dict:
        """Chạy workflow tìm kiếm (đồng bộ).
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            
        Returns:
            Kết quả tìm kiếm
        """
        initial_state = {
            "query": query,
            "image_data": base64.b64encode(image_data).decode('utf-8') if image_data else None,
            "analysis_result": analysis_result
        }
        
        logger.info(f"Bắt đầu tìm kiếm với query: {query}")
        result = self.workflow.invoke(initial_state)
        return result.get("final_response", {}) 