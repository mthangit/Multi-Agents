from typing import Dict, List, Any, Optional, TypedDict
import base64
import os
import logging

from langgraph.graph import StateGraph, END


from nodes.intent_classifier_node import get_intent_classifier_node
from nodes.attribute_extraction_node import get_attribute_extraction_node
from nodes.embed_query_node import get_embed_query_node
from nodes.semantic_search_node import get_semantic_search_node
from nodes.format_response_node import get_format_response_node
from nodes.image_analysis_node import get_image_analysis_node
from nodes.recommendation_node import get_recommendation_node
from nodes.query_combiner_node import get_query_combiner_node

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchState(TypedDict):
    """Định nghĩa trạng thái của workflow tìm kiếm."""
    query: Optional[str]
    original_query: Optional[str]  # Lưu trữ câu query gốc của người dùng
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
    image_analysis: Optional[Dict[str, Any]]
    recommendation: Optional[str]
    # Thêm các biến tạm thời để lưu kết quả phân tích
    text_normalized_query: Optional[str]
    text_extracted_attributes: Optional[Dict[str, Any]]
    image_normalized_query: Optional[str]
    image_extracted_attributes: Optional[Dict[str, Any]]

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
        self.image_analyzer = get_image_analysis_node(api_key=api_key)
        self.recommendation_node = get_recommendation_node(api_key=api_key)
        self.query_combiner = get_query_combiner_node()
        
        # Đường dẫn đến mô hình tùy chỉnh
        if custom_model_path and not os.path.exists(custom_model_path):
            logger.warning(f"Không tìm thấy mô hình tại {custom_model_path}")
            custom_model_path = None
            
        self.embed_query = get_embed_query_node(custom_model_path=custom_model_path)
        self.semantic_search = get_semantic_search_node(
            qdrant_host="http://eyevi.devsecopstech.click",  # Cố định localhost
            qdrant_port=qdrant_port
        )
        self.format_response = get_format_response_node(api_key=api_key)
        
        # Xây dựng workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Xây dựng workflow cho việc tìm kiếm."""
        # Khởi tạo StateGraph với SearchState
        workflow = StateGraph(SearchState)
        
        # Thêm các node vào workflow
        workflow.add_node("intent_classifier", self.intent_classifier)
        workflow.add_node("intent_router", self._intent_router)  # Đăng ký intent_router như một node
        workflow.add_node("image_analyzer", self.image_analyzer)  # Node mới với tên đã sửa
        workflow.add_node("attribute_extractor", self.attribute_extractor)
        workflow.add_node("recommendation_node", self.recommendation_node)  # Thêm node mới
        workflow.add_node("query_combiner", self.query_combiner)  # Thêm node kết hợp query
        workflow.add_node("embed_query", self.embed_query)
        workflow.add_node("semantic_search", self.semantic_search)
        workflow.add_node("format_response", self.format_response)
        
        # Định nghĩa luồng xử lý
        # Bắt đầu từ intent_classifier
        workflow.set_entry_point("intent_classifier")
        
        # Từ intent_classifier đến intent_router
        workflow.add_edge("intent_classifier", "intent_router")
        
        # Từ intent_router đến các node tiếp theo dựa trên loại input
        workflow.add_conditional_edges(
            "intent_router",
            self._route_by_input_type,
            {
                "image_analyzer": "image_analyzer",
                "attribute_extractor": "attribute_extractor",
                "recommendation_node": "recommendation_node"  # Thêm edge mới
            }
        )
        
        # Từ attribute_extractor đến image_analyzer khi có cả text và image
        workflow.add_conditional_edges(
            "attribute_extractor",
            self._should_go_to_image_analyzer,
            {
                "image_analyzer": "image_analyzer",
                "query_combiner": "query_combiner"
            }
        )
        
        # Từ image_analyzer đến query_combiner khi có cả text và image
        workflow.add_conditional_edges(
            "image_analyzer",
            self._should_combine_queries,
            {
                "query_combiner": "query_combiner",
                "embed_query": "embed_query"
            }
        )
        
        # Từ query_combiner đến embed_query
        workflow.add_edge("query_combiner", "embed_query")
        
        # Từ recommendation_node đến END (kết thúc luồng)
        workflow.add_edge("recommendation_node", END)
        
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
        # Node này chỉ chuyển tiếp state, việc định tuyến được thực hiện bởi _route_by_input_type
        return state
    
    def _route_by_input_type(self, state: Dict[str, Any]) -> str:
        """
        Hàm định tuyến dựa trên loại input (text/image).
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Tên của node tiếp theo
        """
        query = state.get("query", "")
        image_data = state.get("image_data")
        intent = state.get("intent", "unknown")
        
        # Lưu trữ query gốc
        if query:
            state["original_query"] = query
        
        # Log thông tin đầu vào
        logger.info(f"_route_by_input_type - query: {query}")
        logger.info(f"_route_by_input_type - image_data exists: {image_data is not None}")
        logger.info(f"_route_by_input_type - intent: {intent}")
        
        # Nếu chỉ có image_data, không có query
        if image_data and not query:
            logger.info("Phát hiện tìm kiếm chỉ bằng hình ảnh, chuyển đến image_analyzer")
            # Đánh dấu đây là tìm kiếm chỉ bằng ảnh
            state["search_type"] = "image"
            return "image_analyzer"
        
        # Nếu có cả text và image, và intent là search_product
        if query and image_data and intent == "search_product":
            logger.info("Phát hiện tìm kiếm kết hợp (text + image), chuyển đến attribute_extractor trước")
            state["search_type"] = "combined"
            return "attribute_extractor"
        
        # Xử lý intent recommend_product
        if intent == "recommend_product":
            logger.info("Phát hiện intent tư vấn sản phẩm, chuyển đến recommendation_node")
            return "recommendation_node"
        
        # Các trường hợp khác, dựa vào intent để định tuyến
        logger.info(f"Định tuyến dựa trên intent: {intent}")
        return self._route_by_intent(state)
    
    def _should_go_to_image_analyzer(self, state: Dict[str, Any]) -> str:
        """
        Kiểm tra xem có nên chuyển đến image_analyzer sau attribute_extractor không.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Tên của node tiếp theo
        """
        # Thêm log để kiểm tra giá trị của image_data và has_image
        image_data_exists = state.get('image_data') is not None
        # has_image = state.get('has_image')
        # search_type = state.get('search_type')
        
        # logger.info(f"_should_go_to_image_analyzer - image_data exists: {image_data_exists}")
        # logger.info(f"_should_go_to_image_analyzer - has_image: {has_image}")
        # logger.info(f"_should_go_to_image_analyzer - search_type: {search_type}")
        
        # Đơn giản hóa logic: chỉ cần kiểm tra sự tồn tại của image_data
        if image_data_exists:
            logger.info("Phát hiện có dữ liệu hình ảnh, chuyển đến image_analyzer")
            return "image_analyzer"
        
        # Nếu không có image_data
        logger.info("Không có dữ liệu hình ảnh, chuyển đến query_combiner")
        return "query_combiner"
    
    def _should_combine_queries(self, state: Dict[str, Any]) -> str:
        """
        Kiểm tra xem có nên kết hợp kết quả từ text và image không.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Tên của node tiếp theo
        """
        # Lấy các giá trị cần thiết
        text_normalized_query = state.get("text_normalized_query", "")
        image_normalized_query = state.get("image_normalized_query", "")
        text_extracted_attributes = state.get("text_extracted_attributes", {})
        image_extracted_attributes = state.get("image_extracted_attributes", {})
        search_type = state.get("search_type")
        
        # Log thông tin
        # logger.info(f"Kết hợp Query - text_normalized_query: {text_normalized_query}")
        # logger.info(f"Kết hợp Query - image_normalized_query: {image_normalized_query}")
        # logger.info(f"Kết hợp Query - search_type: {search_type}")
        
        # Kiểm tra nếu có cả kết quả từ text và image
        has_text_results = bool(text_normalized_query) or bool(text_extracted_attributes)
        has_image_results = bool(image_normalized_query) or bool(image_extracted_attributes)
        
        # Nếu có cả kết quả từ text và image, hoặc search_type là combined
        if (has_text_results and has_image_results) or search_type == "combined":
            logger.info("Có cả kết quả từ text và image, chuyển đến query_combiner")
            return "query_combiner"
        
        logger.info("Không cần kết hợp kết quả, chuyển đến embed_query")
        return "embed_query"
    
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
            state["search_type"] = "text"
            return "attribute_extractor"
        elif intent == "recommend_product":
            # Xử lý intent recommend_product
            return "recommendation_node"
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
            "original_query": query,  # Lưu trữ query gốc
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
            "original_query": query,  # Lưu trữ query gốc
            "image_data": base64.b64encode(image_data).decode('utf-8') if image_data else None,
            "analysis_result": analysis_result
        }
        
        logger.info(f"Bắt đầu tìm kiếm với query: {query}")
        result = self.workflow.invoke(initial_state)
        return result.get("final_response", {}) 