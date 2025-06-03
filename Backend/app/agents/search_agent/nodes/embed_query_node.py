from typing import Dict, Any, Optional, Union, List
import logging
import torch
import os
import base64
from io import BytesIO
from PIL import Image
import requests

from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)

class EmbedQueryNode:
    """Node chuyển đổi query thành vector embedding sử dụng CLIP."""
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        custom_model_path: Optional[str] = None
    ):
        """
        Khởi tạo node embedding.
        
        Args:
            model_name: Tên model CLIP sử dụng
            custom_model_path: Đường dẫn đến mô hình tùy chỉnh (nếu có)
        """
        try:
            # Khởi tạo model và processor mặc định
            logger.info(f"Đang tải model mặc định {model_name}")
            self.model = CLIPModel.from_pretrained(model_name)
            self.processor = CLIPProcessor.from_pretrained(model_name)
            
            # Tải mô hình tùy chỉnh nếu có
            if custom_model_path and os.path.exists(custom_model_path):
                logger.info(f"Đang tải mô hình tùy chỉnh từ {custom_model_path}")
                try:
                    checkpoint = torch.load(custom_model_path, map_location=torch.device('cpu'))
                    
                    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                        logger.info("Phát hiện checkpoint từ quá trình fine-tuning")
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                    elif isinstance(checkpoint, dict):
                        logger.info("Thử tải state_dict trực tiếp")
                        self.model.load_state_dict(checkpoint)
                    else:
                        logger.warning(f"Không hỗ trợ định dạng mô hình {type(checkpoint)}")
                except Exception as e:
                    logger.error(f"Lỗi khi tải mô hình tùy chỉnh: {e}")
                    logger.warning("Tiếp tục sử dụng mô hình mặc định")
            
        except Exception as e:
            logger.error(f"Lỗi khi tải model: {e}")
            raise
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chuyển đổi query thành vector embedding.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa vector embedding
        """
        # Lấy thông tin từ state
        normalized_query = state.get("normalized_query", "")
        image_data = state.get("image_data")
        
        # Kiểm tra loại tìm kiếm
        has_text = bool(normalized_query)
        has_image = bool(image_data)
        
        # Khởi tạo kết quả
        result = {
            "search_type": None,
            "text_embedding": None,
            "image_embedding": None
        }
        
        try:
            # Tìm kiếm bằng text
            if has_text and not has_image:
                result["search_type"] = "text"
                result["text_embedding"] = self._embed_text(normalized_query)
                
            # Tìm kiếm bằng image
            elif has_image and not has_text:
                result["search_type"] = "image"
                result["image_embedding"] = self._embed_image(image_data)
                
            # Tìm kiếm kết hợp
            elif has_text and has_image:
                result["search_type"] = "combined"
                result["text_embedding"] = self._embed_text(normalized_query)
                result["image_embedding"] = self._embed_image(image_data)
                
            else:
                logger.warning("Không có dữ liệu tìm kiếm (text hoặc image)")
                result["search_type"] = "unknown"
                result["error"] = "Không có dữ liệu tìm kiếm"
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo embedding: {e}")
            return {
                "search_type": "error",
                "error": str(e)
            }
    
    def _embed_text(self, text: str) -> List[float]:
        """
        Chuyển đổi text thành vector embedding.
        
        Args:
            text: Văn bản cần chuyển đổi
            
        Returns:
            Vector embedding của văn bản
        """
        with torch.no_grad():
            text_inputs = self.processor(
                text=text, return_tensors="pt", padding=True
            )
            text_features = self.model.get_text_features(**text_inputs)
            # Chuẩn hóa vector
            text_embedding = text_features / text_features.norm(dim=-1, keepdim=True)
            return text_embedding.numpy()[0].tolist()
    
    def _embed_image(self, image_data: str) -> List[float]:
        """
        Chuyển đổi image thành vector embedding.
        
        Args:
            image_data: Dữ liệu hình ảnh dạng base64
            
        Returns:
            Vector embedding của hình ảnh
        """
        # Giải mã base64
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
            
        # Chuyển đổi thành đối tượng PIL.Image
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt")
            image_features = self.model.get_image_features(**inputs)
            # Chuẩn hóa vector
            image_embedding = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_embedding.numpy()[0].tolist()

# Hàm tiện ích để tạo node
def get_embed_query_node(
    model_name: str = "openai/clip-vit-base-patch32",
    custom_model_path: Optional[str] = None
) -> EmbedQueryNode:
    """
    Tạo một instance của EmbedQueryNode.
    
    Args:
        model_name: Tên model CLIP sử dụng
        custom_model_path: Đường dẫn đến mô hình tùy chỉnh (nếu có)
        
    Returns:
        EmbedQueryNode instance
    """
    return EmbedQueryNode(
        model_name=model_name,
        custom_model_path=custom_model_path
    ) 