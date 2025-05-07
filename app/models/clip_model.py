import torch
from transformers import CLIPProcessor, CLIPModel
import logging
import os
from PIL import Image
from typing import List, Dict, Union, Optional, Any
import numpy as np

from app.config.settings import CLIP_MODEL_NAME, CLIP_MODEL_PATH

logger = logging.getLogger(__name__)

class CLIPModelWrapper:
    def __init__(self):
        """
        Khởi tạo CLIP model wrapper - có thể tải mô hình tinh chỉnh từ file .pt hoặc mô hình từ Hugging Face
        """
        self.clip_model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo CLIP model: {str(e)}")
            raise
    
    def _load_model(self) -> None:
        """
        Tải mô hình CLIP từ file .pt nếu tồn tại, nếu không thì tải từ Hugging Face
        Hỗ trợ cả hai trường hợp:
        1. File .pt chứa toàn bộ mô hình
        2. File .pt chứa checkpoint (model_state_dict)
        """
        try:
            if CLIP_MODEL_PATH and os.path.exists(CLIP_MODEL_PATH):
                logger.info(f"Đang tải mô hình CLIP từ file: {CLIP_MODEL_PATH}")
                
                # Tải checkpoint từ file
                checkpoint = torch.load(CLIP_MODEL_PATH, map_location=self.device)
                
                # Kiểm tra xem file chứa toàn bộ mô hình hay chỉ là state_dict
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    # Trường hợp 2: File chứa checkpoint với model_state_dict
                    logger.info("Phát hiện checkpoint format với model_state_dict")
                    
                    # Tải mô hình cơ bản từ Hugging Face
                    self.clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
                    
                    # Áp dụng model_state_dict từ checkpoint
                    self.clip_model.load_state_dict(checkpoint['model_state_dict'])
                    
                    # Tải processor từ Hugging Face
                    self.processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
                else:
                    # Trường hợp 1: File chứa toàn bộ mô hình
                    logger.info("Tải toàn bộ mô hình từ file")
                    self.clip_model = checkpoint
                    self.processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
                
                # Đưa mô hình lên device thích hợp
                self.clip_model.to(self.device)
                logger.info(f"Đã tải mô hình CLIP từ file thành công")
            else:
                logger.info(f"Đang tải mô hình CLIP từ Hugging Face: {CLIP_MODEL_NAME}")
                self.clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
                self.processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
                self.clip_model.to(self.device)
                logger.info(f"Đã tải mô hình CLIP từ Hugging Face thành công")
        except Exception as e:
            logger.error(f"Lỗi khi tải mô hình CLIP: {str(e)}")
            raise
    
    def encode_image(self, image: Union[str, Image.Image]) -> Optional[List[float]]:
        """
        Mã hóa ảnh thành vector đặc trưng
        
        Args:
            image: Đường dẫn ảnh hoặc object PIL Image
            
        Returns:
            Vector đặc trưng của ảnh (normalized)
        """
        try:
            # Nếu đầu vào là đường dẫn, tải ảnh từ đường dẫn
            if isinstance(image, str):
                if not os.path.exists(image):
                    logger.error(f"Không tìm thấy file ảnh: {image}")
                    return None
                try:
                    image = Image.open(image).convert('RGB')
                except Exception as e:
                    logger.error(f"Lỗi khi đọc ảnh từ {image}: {str(e)}")
                    return None
            
            # Kiểm tra xem đầu vào có phải là object PIL Image không
            if not isinstance(image, Image.Image):
                logger.error(f"Đầu vào không phải là ảnh hợp lệ")
                return None
            
            # Xử lý ảnh
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            # Tắt gradient để tăng tốc độ và giảm bộ nhớ
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
            
            # Chuyển về CPU và normalize
            image_features = image_features.cpu().numpy()[0]
            normalized_features = image_features / np.linalg.norm(image_features)
            
            return normalized_features.tolist()
        
        except Exception as e:
            logger.error(f"Lỗi khi mã hóa ảnh: {str(e)}")
            return None
    
    def encode_text(self, text: str) -> Optional[List[float]]:
        """
        Mã hóa văn bản thành vector đặc trưng
        
        Args:
            text: Văn bản cần mã hóa
            
        Returns:
            Vector đặc trưng của văn bản (normalized)
        """
        try:
            # Xử lý văn bản
            inputs = self.processor(text=text, return_tensors="pt", padding=True).to(self.device)
            
            # Tắt gradient để tăng tốc độ và giảm bộ nhớ
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
            
            # Chuyển về CPU và normalize
            text_features = text_features.cpu().numpy()[0]
            normalized_features = text_features / np.linalg.norm(text_features)
            
            return normalized_features.tolist()
        
        except Exception as e:
            logger.error(f"Lỗi khi mã hóa văn bản: {str(e)}")
            return None
    
    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Tính toán độ tương đồng cosine giữa hai vector
        
        Args:
            vector1: Vector thứ nhất
            vector2: Vector thứ hai
            
        Returns:
            Độ tương đồng cosine (từ -1 đến 1, càng gần 1 càng giống nhau)
        """
        try:
            if not vector1 or not vector2:
                return 0.0
                
            # Chuyển sang numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Tính cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            # Tránh chia cho 0
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
                
            similarity = dot_product / (norm_v1 * norm_v2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Lỗi khi tính toán độ tương đồng: {str(e)}")
            return 0.0 