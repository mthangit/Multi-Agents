from typing import Dict, Any, Optional, List
import logging
import json
import base64
import traceback
from io import BytesIO
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.search_prompts import IMAGE_ANALYSIS_PROMPT

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageAnalysisNode:
    """Node phân tích nội dung hình ảnh sử dụng Gemini Vision."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo node phân tích hình ảnh.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.2,  # Nhiệt độ thấp để đảm bảo kết quả ổn định
        )
        logger.info("ImageAnalysisNode đã được khởi tạo")
        
        # Cache đơn giản cho demo
        self._cache = {}
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân tích nội dung hình ảnh.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa kết quả phân tích hình ảnh
        """
        # Lấy dữ liệu hình ảnh từ state
        image_data = state.get("image_data")
        
        # Lấy kết quả phân tích từ text nếu có
        # text_normalized_query = state.get("text_normalized_query", "")
        # text_extracted_attributes = state.get("text_extracted_attributes", {})
        
        # # Lưu lại các giá trị quan trọng từ state ban đầu
        # has_image = state.get("has_image")
        # search_type = state.get("search_type")
        
        # # Log các giá trị quan trọng
        # logger.info(f"ImageAnalysisNode - has_image: {has_image}")
        # logger.info(f"ImageAnalysisNode - search_type: {search_type}")
        # logger.info(f"ImageAnalysisNode - text_normalized_query: {text_normalized_query}")
        
        # Kiểm tra nếu không có dữ liệu hình ảnh
        if not image_data:
            logger.warning("Không có dữ liệu hình ảnh, bỏ qua phân tích")
            # Trả về kết quả với các biến tạm thời trống
            result = {
                "image_normalized_query": "",
                "image_extracted_attributes": {}
            }
            # Giữ lại các giá trị quan trọng
            self._preserve_important_values(result, state)
            return result
        
        try:
            # Tạo hash đơn giản từ image_data để làm key cho cache
            image_hash = self._get_image_hash(image_data)
            
            # Kiểm tra cache
            if image_hash in self._cache:
                logger.info("Sử dụng kết quả phân tích từ cache")
                cached_result = self._cache[image_hash]
                
                # Tạo kết quả từ cache
                result = {
                    "image_analysis": cached_result.get("image_analysis"),
                    "image_normalized_query": cached_result.get("image_normalized_query", ""),
                    "image_extracted_attributes": cached_result.get("image_extracted_attributes", {})
                }
            else:
                # Phân tích hình ảnh
                image_analysis = self._analyze_image(image_data)
                
                # Tạo normalized_query và extracted_attributes chỉ khi hình ảnh có chứa kính mắt
                if image_analysis.get("contains_eyewear", False):
                    image_normalized_query = self._create_query_from_analysis(image_analysis)
                    image_extracted_attributes = self._create_attributes_from_analysis(image_analysis)
                else:
                    image_normalized_query = ""
                    image_extracted_attributes = {}
                
                # Tạo kết quả
                result = {
                    "image_analysis": image_analysis,
                    "image_normalized_query": image_normalized_query,
                    "image_extracted_attributes": image_extracted_attributes
                }
                
                # Lưu vào cache
                self._cache[image_hash] = result
            
            # Giữ lại các giá trị quan trọng từ state ban đầu
            self._preserve_important_values(result, state)
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi phân tích hình ảnh: {e}")
            logger.error(f"Chi tiết lỗi: {traceback.format_exc()}")
            result = {
                "image_analysis": {
                    "contains_eyewear": False,
                    "error": str(e)
                },
                "image_normalized_query": "",
                "image_extracted_attributes": {},
                "error": f"Lỗi khi phân tích hình ảnh: {str(e)}"
            }
            # Giữ lại các giá trị quan trọng
            self._preserve_important_values(result, state)
            return result
    
    def _get_image_hash(self, image_data: str) -> str:
        """
        Tạo hash từ dữ liệu hình ảnh.
        
        Args:
            image_data: Dữ liệu hình ảnh dạng base64
            
        Returns:
            Chuỗi hash
        """
        import hashlib
        return hashlib.md5(image_data.encode() if isinstance(image_data, str) else image_data).hexdigest()
    
    def _analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        Phân tích hình ảnh sử dụng Gemini Vision.
        
        Args:
            image_data: Dữ liệu hình ảnh dạng base64
            
        Returns:
            Dict chứa kết quả phân tích
        """
        try:
            # Chuẩn bị dữ liệu hình ảnh
            if "base64," in image_data:
                # Nếu image_data đã có định dạng data URL
                image_for_model = image_data
            else:
                # Nếu image_data chỉ là chuỗi base64 thuần túy
                # Thử xác định loại hình ảnh
                try:
                    # Giải mã base64
                    decoded_data = base64.b64decode(image_data)
                    img = Image.open(BytesIO(decoded_data))
                    mime_type = f"image/{img.format.lower()}" if img.format else "image/jpeg"
                    image_for_model = f"data:{mime_type};base64,{image_data}"
                except Exception as e:
                    logger.warning(f"Không thể xác định loại hình ảnh: {e}")
                    image_for_model = f"data:image/jpeg;base64,{image_data}"
            
            # Gọi Gemini Vision để phân tích hình ảnh
            from langchain_core.messages import HumanMessage
            message = HumanMessage(
                content=[
                    {"type": "text", "text": IMAGE_ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_for_model}}
                ]
            )
            
            response = self.llm.invoke([message])
            # logger.info("Đã nhận phản hồi từ Gemini Vision")
            
            # Phân tích kết quả JSON
            result = self._parse_analysis_result(response.content)
            logger.info(f"Kết quả phân tích hình ảnh: {json.dumps(result, ensure_ascii=False)[:200]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi phân tích hình ảnh: {e}")
            logger.error(traceback.format_exc())
            return {
                "contains_eyewear": False,
                "contains_person": False,
                "eyewear_type": "",
                "eyewear_description": {
                    "brand": "",
                    "color": "",
                    "frame_material": "",
                    "frame_shape": "",
                    "gender": "",
                    "style": "",
                    "detailed_description": ""
                },
                "face_description": "",
                "general_description": "Không thể phân tích hình ảnh",
                "suggested_search_terms": []  # Không đặt giá trị mặc định "kính mắt"
            }
    
    def _parse_analysis_result(self, result_text: str) -> Dict[str, Any]:
        """
        Phân tích kết quả từ Gemini Vision.
        
        Args:
            result_text: Kết quả trả về từ Gemini Vision
            
        Returns:
            Dict chứa kết quả đã được phân tích
        """
        try:
            # Tìm JSON trong kết quả
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                logger.debug(f"Chuỗi JSON được trích xuất: {json_str}")
                parsed_result = json.loads(json_str)
                return parsed_result
            else:
                logger.warning(f"Không tìm thấy JSON trong kết quả phân tích: {result_text}")
                return {
                    "contains_eyewear": False,
                    "contains_person": False,
                    "eyewear_type": "",
                    "eyewear_description": {
                        "brand": "",
                        "color": "",
                        "frame_material": "",
                        "frame_shape": "",
                        "gender": "",
                        "style": "",
                        "detailed_description": ""
                    },
                    "face_description": "",
                    "general_description": "Không thể phân tích hình ảnh",
                    "suggested_search_terms": []
                }
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi khi phân tích JSON: {e}")
            logger.error(f"Chuỗi JSON gây lỗi: {result_text}")
            # Thử tìm và sửa JSON không hợp lệ
            try:
                # Thử thay thế các ký tự có thể gây lỗi
                fixed_json = result_text.replace("'", '"').replace('\n', ' ')
                start_idx = fixed_json.find('{')
                end_idx = fixed_json.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    fixed_json_str = fixed_json[start_idx:end_idx]
                    logger.info(f"Thử phân tích JSON đã sửa: {fixed_json_str}")
                    return json.loads(fixed_json_str)
            except:
                logger.error("Không thể sửa JSON")
            
            return {
                "contains_eyewear": False,
                "contains_person": False,
                "eyewear_type": "",
                "eyewear_description": {
                    "brand": "",
                    "color": "",
                    "frame_material": "",
                    "frame_shape": "",
                    "gender": "",
                    "style": "",
                    "detailed_description": ""
                },
                "face_description": "",
                "general_description": "Không thể phân tích hình ảnh",
                "suggested_search_terms": []
            }
    
    def _create_query_from_analysis(self, image_analysis: Dict[str, Any]) -> str:
        """
        Tạo normalized_query từ kết quả phân tích.
        
        Args:
            image_analysis: Kết quả phân tích hình ảnh
            
        Returns:
            Chuỗi normalized_query
        """
        # Kiểm tra nếu hình ảnh có chứa kính mắt
        if not image_analysis.get("contains_eyewear", False):
            return ""
        
        # Lấy thông tin từ eyewear_description
        eyewear_desc = image_analysis.get("eyewear_description", {})
        eyewear_type = image_analysis.get("eyewear_type", "")
        
        # Tạo các thành phần của query
        parts = []
        
        # Thêm loại kính
        if eyewear_type:
            parts.append(eyewear_type)
        else:
            parts.append("Kính Mát" if "mát" in image_analysis.get("general_description", "").lower() else "Gọng Kính")
        
        # Thêm giới tính
        gender = eyewear_desc.get("gender", "")
        if gender:
            parts.append(gender)
        
        # Thêm thương hiệu
        brand = eyewear_desc.get("brand", "")
        if brand:
            parts.append(brand)
        
        # Thêm màu sắc
        # color = eyewear_desc.get("color", "")
        # if color:
        #     parts.append(f"màu {color}")
        
        # Thêm chất liệu
        # material = eyewear_desc.get("frame_material", "")
        # if material:
        #     parts.append(f"khung {material}")
        
        # Thêm hình dáng
        shape = eyewear_desc.get("frame_shape", "")
        if shape:
            parts.append(f"kiểu dáng {shape}")
        
        # Nếu không có đủ thông tin, thêm style
        if len(parts) < 3 and eyewear_desc.get("style", ""):
            parts.append(f"phong cách {eyewear_desc['style']}")
        
        # Tạo query
        query = " ".join(parts)
        logger.info(f"Đã tạo normalized_query từ phân tích hình ảnh: {query}")
        
        return query
    
    def _create_attributes_from_analysis(self, image_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo extracted_attributes từ kết quả phân tích.
        
        Args:
            image_analysis: Kết quả phân tích hình ảnh
            
        Returns:
            Dict chứa các thuộc tính đã trích xuất
        """
        if not image_analysis.get("contains_eyewear", False):
            return {}
        
        # Lấy thông tin từ eyewear_description
        eyewear_desc = image_analysis.get("eyewear_description", {})
        eyewear_type = image_analysis.get("eyewear_type", "")
        
        # Tạo attributes
        attributes = {}
        
        # Thêm category
        if eyewear_type:
            attributes["category"] = eyewear_type
        elif "mát" in image_analysis.get("general_description", "").lower():
            attributes["category"] = "Kính Mát"
        else:
            attributes["category"] = "Gọng Kính"
        
        # Thêm gender
        if eyewear_desc.get("gender", ""):
            attributes["gender"] = eyewear_desc["gender"]
        
        # Thêm brand
        if eyewear_desc.get("brand", ""):
            attributes["brand"] = eyewear_desc["brand"]
        
        # Thêm color
        # if eyewear_desc.get("color", ""):
        #     attributes["color"] = eyewear_desc["color"]
        
        # Thêm frame_material
        if eyewear_desc.get("frame_material", ""):
            attributes["frame_material"] = eyewear_desc["frame_material"]
        
        # Thêm frame_shape
        if eyewear_desc.get("frame_shape", ""):
            attributes["recommended_shapes"] = [eyewear_desc["frame_shape"]]
        
        logger.info(f"Đã tạo extracted_attributes từ phân tích hình ảnh: {attributes}")
        
        return attributes

    def _preserve_important_values(self, result: Dict[str, Any], state: Dict[str, Any]) -> None:
        """
        Giữ lại các giá trị quan trọng từ state ban đầu.
        
        Args:
            result: Dict kết quả sẽ được trả về
            state: Dict trạng thái ban đầu
        """
        # Danh sách các key quan trọng cần giữ lại
        important_keys = [
            "has_image", "search_type", "image_data", "original_query", 
            "text_normalized_query", "text_extracted_attributes"
        ]
        
        # Giữ lại các giá trị quan trọng
        for key in important_keys:
            if key in state and state[key] is not None:
                result[key] = state[key]
        
        # logger.info(f"Đã giữ lại các giá trị quan trọng: has_image={result.get('has_image')}, search_type={result.get('search_type')}")

# Hàm tiện ích để tạo node
def get_image_analysis_node(api_key: Optional[str] = None) -> ImageAnalysisNode:
    """
    Tạo một instance của ImageAnalysisNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        ImageAnalysisNode instance
    """
    return ImageAnalysisNode(api_key=api_key) 