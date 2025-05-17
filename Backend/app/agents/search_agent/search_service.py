import torch
import logging
import requests
import os
from typing import List, Dict, Optional, Union, Any, Generator
from PIL import Image
from io import BytesIO
from collections import defaultdict
from functools import lru_cache

from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductSearch:
    """Lớp tìm kiếm sản phẩm sử dụng CLIP và Qdrant."""

    def __init__(
        self,
        qdrant_host="localhost",
        qdrant_port=6333,
        model_name="openai/clip-vit-base-patch32",
        default_limit=5,
        cache_size=100,
        custom_model_path=None
    ):
        """Khởi tạo ProductSearch.

        Args:
            qdrant_host: Host của Qdrant server
            qdrant_port: Port của Qdrant server
            model_name: Tên model CLIP sử dụng
            default_limit: Số lượng kết quả mặc định trả về
            cache_size: Kích thước cache cho các phương thức tìm kiếm
            custom_model_path: Đường dẫn đến mô hình tùy chỉnh (nếu có)
        """
        try:
            # Khởi tạo model và processor mặc định
            logger.info(f"Đang tải model mặc định {model_name}")
            self.model = CLIPModel.from_pretrained(model_name)
            
            # Nếu có đường dẫn mô hình tùy chỉnh, thử tải
            if custom_model_path and os.path.exists(custom_model_path):
                logger.info(f"Đang tải mô hình tùy chỉnh từ {custom_model_path}")
                try:
                    # Tải mô hình từ file .pt với map_location để chuyển sang CPU
                    checkpoint = torch.load(custom_model_path, map_location=torch.device('cpu'))
                    
                    # Kiểm tra xem có phải checkpoint từ quá trình fine-tuning không
                    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                        logger.info("Phát hiện checkpoint từ quá trình fine-tuning")
                        # Chỉ lấy model_state_dict từ checkpoint
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                        logger.info("Đã tải thành công model_state_dict từ checkpoint")
                    elif isinstance(checkpoint, dict):
                        # Thử tải trực tiếp nếu có vẻ như là state_dict thuần túy
                        logger.info("Thử tải state_dict trực tiếp")
                        self.model.load_state_dict(checkpoint)
                        logger.info("Đã tải thành công state_dict")
                    else:
                        logger.warning(f"Không hỗ trợ định dạng mô hình {type(checkpoint)}")
                except Exception as e:
                    logger.error(f"Lỗi khi tải mô hình tùy chỉnh: {e}")
                    logger.warning("Tiếp tục sử dụng mô hình mặc định")
            
            # Tải processor
            try:
                self.processor = CLIPProcessor.from_pretrained(model_name)
                logger.info("Đã tải processor thành công")
            except ImportError:
                logger.warning("Torchvision không khả dụng, sử dụng processor chậm")
                self.processor = CLIPProcessor.from_pretrained(model_name, use_fast=False)
                
        except Exception as e:
            logger.error(f"Lỗi khi tải model: {e}")
            raise

        # Khởi tạo Qdrant client
        self.qdrant_client = QdrantClient(qdrant_host, port=qdrant_port)
        logger.info(f"Đã kết nối đến Qdrant tại {qdrant_host}:{qdrant_port}")

        # Số lượng kết quả trả về mặc định
        self.default_limit = default_limit

        # Kích thước cache
        self.cache_size = cache_size

        # Cache các kết quả tìm kiếm
        self.process_image = lru_cache(maxsize=cache_size)(self._process_image)
        self.process_text = lru_cache(maxsize=cache_size)(self._process_text)

    def _process_image(self, image_bytes: bytes) -> torch.Tensor:
        """Xử lý ảnh và tạo vector (phiên bản nội bộ).

        Args:
            image_bytes: Dữ liệu ảnh dạng bytes

        Returns:
            Vector đặc trưng của ảnh
        """
        try:
            image = Image.open(BytesIO(image_bytes)).convert('RGB')
            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt")
                image_features = self.model.get_image_features(**inputs)
                return image_features.numpy()[0]
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None

    def _process_text(self, text: str) -> torch.Tensor:
        """Xử lý text và tạo vector (phiên bản nội bộ).

        Args:
            text: Chuỗi văn bản cần xử lý

        Returns:
            Vector đặc trưng của văn bản
        """
        try:
            with torch.no_grad():
                text_inputs = self.processor(
                    text=text, return_tensors="pt", padding=True
                )
                text_features = self.model.get_text_features(**text_inputs)
                return text_features.numpy()[0]
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return None

    def prepare_image(self, image: Union[str, Image.Image, bytes]) -> bytes:
        """Chuẩn bị ảnh thành dạng bytes cho xử lý.

        Args:
            image: Ảnh đầu vào (URL, đường dẫn, đối tượng Image, hoặc bytes)

        Returns:
            Dữ liệu ảnh dạng bytes
        """
        # Nếu image là URL
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            response = requests.get(image)
            return response.content
        # Nếu image là đường dẫn local
        elif isinstance(image, str):
            with open(image, 'rb') as f:
                return f.read()
        # Nếu image là đối tượng PIL.Image
        elif isinstance(image, Image.Image):
            byte_arr = BytesIO()
            image.save(byte_arr, format='JPEG')
            return byte_arr.getvalue()
        # Nếu image đã là bytes
        elif isinstance(image, bytes):
            return image
        else:
            raise ValueError("Không hỗ trợ định dạng ảnh này")

    def search_by_image(
        self,
        image: Union[str, Image.Image, bytes],
        limit: int = None,
        filter_params: Dict = None,
        streaming: bool = False
    ) -> Union[List[Dict], Generator[Dict, None, None]]:
        """Tìm kiếm sản phẩm bằng ảnh.

        Args:
            image: Ảnh đầu vào (URL, đường dẫn, đối tượng Image, hoặc bytes)
            limit: Số lượng kết quả trả về
            filter_params: Điều kiện lọc bổ sung
            streaming: Trả về kết quả theo stream

        Returns:
            Danh sách sản phẩm hoặc generator các sản phẩm
        """
        limit = limit or self.default_limit
        image_bytes = self.prepare_image(image)
        image_vector = self.process_image(image_bytes)

        if image_vector is None:
            return [] if not streaming else (yield from [])

        # Tạo filter nếu có
        search_filter = None
        if filter_params:
            conditions = []
            for field, value in filter_params.items():
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
            search_filter = Filter(must=conditions)

        # Thực hiện tìm kiếm
        search_results = self.qdrant_client.search(
            collection_name="product_images",
            query_vector=image_vector.tolist(),
            limit=limit,
            query_filter=search_filter
        )

        # Streaming hoặc trả về tất cả
        if streaming:
            for hit in search_results:
                yield hit.payload
        else:
            return [hit.payload for hit in search_results]

    def search_by_text(
        self,
        text: str,
        limit: int = None,
        filter_params: Dict = None,
        streaming: bool = False
    ) -> Union[List[Dict], Generator[Dict, None, None]]:
        """Tìm kiếm sản phẩm bằng text.

        Args:
            text: Văn bản tìm kiếm
            limit: Số lượng kết quả trả về
            filter_params: Điều kiện lọc bổ sung
            streaming: Trả về kết quả theo stream

        Returns:
            Danh sách sản phẩm hoặc generator các sản phẩm
        """
        limit = limit or self.default_limit
        text_vector = self.process_text(text)

        if text_vector is None:
            return [] if not streaming else (yield from [])

        # Tạo filter nếu có
        search_filter = None
        if filter_params:
            conditions = []
            for field, value in filter_params.items():
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
            search_filter = Filter(must=conditions)

        # Thực hiện tìm kiếm
        search_results = self.qdrant_client.search(
            collection_name="product_texts",
            query_vector=text_vector.tolist(),
            limit=limit,
            query_filter=search_filter
        )

        # Streaming hoặc trả về tất cả
        if streaming:
            for hit in search_results:
                yield hit.payload
        else:
            return [hit.payload for hit in search_results]

    def search_combined(
        self,
        text: Optional[str] = None,
        image: Optional[Union[str, Image.Image, bytes]] = None,
        limit: int = None,
        filter_params: Dict = None,
        w_image: float = 0.4,
        w_text: float = 0.6,
        streaming: bool = False
    ) -> Union[List[Dict], Generator[Dict, None, None]]:
        """Tìm kiếm kết hợp cả ảnh và text với trọng số.

        Args:
            text: Câu query text
            image: Ảnh query
            limit: Số lượng kết quả trả về
            filter_params: Các điều kiện lọc
            w_image: Trọng số cho điểm ảnh (mặc định 0.4)
            w_text: Trọng số cho điểm text (mặc định 0.6)
            streaming: Trả về kết quả theo stream

        Returns:
            Danh sách sản phẩm hoặc generator các sản phẩm
        """
        limit = limit or self.default_limit
        product_scores = defaultdict(float)
        product_details = {}

        if image:
            # Chuẩn bị ảnh
            image_bytes = self.prepare_image(image)
            image_vector = self.process_image(image_bytes)
            if image_vector is not None:
                # Tạo filter nếu có
                search_filter = None
                if filter_params:
                    filter_conditions = [
                        FieldCondition(key=k, match=MatchValue(value=v))
                        for k, v in filter_params.items()
                    ]
                    search_filter = Filter(must=filter_conditions)

                # Lấy kết quả tìm kiếm ảnh với score
                image_results = self.qdrant_client.search(
                    collection_name="product_images",
                    query_vector=image_vector.tolist(),
                    limit=limit * 3,  # Tăng limit để có nhiều kết quả hơn
                    query_filter=search_filter,
                    with_payload=True,
                    score_threshold=0.0
                )

                # Cộng điểm từ kết quả ảnh (có trọng số)
                for hit in image_results:
                    product_id = hit.payload.get("product_id")
                    if product_id:
                        product_scores[product_id] += hit.score * w_image
                        if product_id not in product_details:
                            product_details[product_id] = hit.payload

        if text:
            text_vector = self.process_text(text)
            if text_vector is not None:
                # Tạo filter nếu có
                search_filter = None
                if filter_params:
                    filter_conditions = [
                        FieldCondition(key=k, match=MatchValue(value=v))
                        for k, v in filter_params.items()
                    ]
                    search_filter = Filter(must=filter_conditions)

                # Lấy kết quả tìm kiếm text với score
                text_results = self.qdrant_client.search(
                    collection_name="product_texts",
                    query_vector=text_vector.tolist(),
                    limit=limit * 3,
                    query_filter=search_filter,
                    with_payload=True,
                    score_threshold=0.0
                )

                # Cộng điểm từ kết quả text (có trọng số)
                for hit in text_results:
                    product_id = hit.payload.get("product_id")
                    if product_id:
                        product_scores[product_id] += hit.score * w_text
                        if product_id not in product_details:
                            product_details[product_id] = hit.payload

        # Sắp xếp kết quả theo tổng điểm
        sorted_results = sorted(
            [
                {
                    "product_id": product_id,
                    "score": score,
                    **product_details[product_id]
                }
                for product_id, score in product_scores.items()
            ],
            key=lambda x: x["score"],
            reverse=True
        )

        # Trả về top k kết quả (streaming hoặc tất cả)
        results = sorted_results[:limit]
        if streaming:
            for result in results:
                yield result
        else:
            return results

    def format_search_results(
        self, 
        results: List[Dict], 
        query_text: Optional[str] = None,
        recommended_shapes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Định dạng kết quả tìm kiếm thành JSON phù hợp.

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
                "image_url": product.get("image_url", ""),
                "frame_shape": product.get("frame_shape", ""),
                "frame_color": product.get("frame_color", ""),
                "frame_material": product.get("frame_material", ""),
                "score": product.get("score", 0),
            })
        
        # Tạo summary dựa trên kết quả
        if not products:
            summary = "Không tìm thấy sản phẩm phù hợp."
        else:
            summary_parts = []
            
            # Nếu có recommended_shapes, thêm vào summary
            if recommended_shapes:
                shapes_text = ", ".join(recommended_shapes)
                summary_parts.append(f"dựa trên phân tích khuôn mặt của bạn, chúng tôi đề xuất gọng kính dạng {shapes_text}")
            
            # Thêm thông tin về số lượng sản phẩm tìm thấy
            summary_parts.append(f"đã tìm thấy {len(products)} sản phẩm phù hợp")
            
            # Nếu có query_text, thêm vào summary
            if query_text:
                summary_parts.append(f"với yêu cầu '{query_text}'")
            
            # Liệt kê 3 sản phẩm đầu tiên
            if products:
                top_products = products[:3]
                product_mentions = [f"{p['brand']} {p['name']}" for p in top_products]
                summary_parts.append(f"bao gồm {', '.join(product_mentions)}")
            
            summary = ". ".join(summary_parts).capitalize() + "."
        
        return {
            "products": products,
            "query": query_text,
            "recommended_shapes": recommended_shapes,
            "count": len(products),
            "summary": summary
        }
