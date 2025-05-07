import os
from dotenv import load_dotenv
from typing import Dict, Any

# Tải biến môi trường từ file .env
load_dotenv()

# Thông tin của ứng dụng
APP_NAME = os.getenv("APP_NAME", "glasses_search_agent")
USER_ID = os.getenv("USER_ID", "default_user")
SESSION_ID = os.getenv("SESSION_ID", "default_session")

# Cấu hình Google ADK và Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Cấu hình Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 512))
TEXT_COLLECTION_NAME = os.getenv("TEXT_COLLECTION_NAME", "product_texts")
IMAGE_COLLECTION_NAME = os.getenv("IMAGE_COLLECTION_NAME", "product_images")

# Cấu hình Tìm kiếm
SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", 5))  # Số lượng kết quả tìm kiếm từ vector database
DISPLAY_LIMIT = int(os.getenv("DISPLAY_LIMIT", 2))  # Số lượng kết quả hiển thị cho người dùng

# Cấu hình Model
CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")  # Mô hình CLIP từ Hugging Face
CLIP_MODEL_PATH = os.getenv("CLIP_MODEL_PATH")

# Cấu hình API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Cấu hình server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Cấu hình vector database
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data/vector_db")
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST", "localhost")
VECTOR_DB_PORT = int(os.getenv("VECTOR_DB_PORT", "6333"))
VECTOR_DB_COLLECTION = "glasses"

class Settings:
    """Lớp chứa các cấu hình của ứng dụng"""
    
    # Cấu hình cơ bản
    APP_NAME = "glasses_search_agent"
    USER_ID = "default_user"
    SESSION_ID = "default_session"
    
    # Cấu hình model
    MODEL_NAME = "gemini-2.0-flash"
    
    # Cấu hình vector database
    VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST", "localhost")
    VECTOR_DB_PORT = int(os.getenv("VECTOR_DB_PORT", "6333"))
    VECTOR_DB_COLLECTION = "glasses"
    
    # Cấu hình CLIP model
    CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
    CLIP_MODEL_PATH = os.getenv("CLIP_MODEL_PATH")
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> Dict[str, Any]:
        """Lấy cấu hình cho agent cụ thể"""
        configs = {
            "orchestrator": {
                "model": cls.MODEL_NAME,
                "description": "Agent điều phối các yêu cầu tìm kiếm kính mắt",
                "instruction": """Bạn là một agent thông minh chuyên xử lý các yêu cầu tìm kiếm kính mắt.
                Khi nhận được yêu cầu, hãy phân tích xem có liên quan đến kính mắt không.
                Nếu có, hãy chuyển yêu cầu cho glasses_agent xử lý.
                Nếu không, hãy thông báo rõ ràng rằng bạn chỉ có thể giúp tìm kiếm kính mắt."""
            },
            "glasses": {
                "model": cls.MODEL_NAME,
                "description": "Agent chuyên tìm kiếm kính mắt",
                "instruction": """Bạn là một agent chuyên tìm kiếm kính mắt.
                Khi nhận được yêu cầu, hãy sử dụng các công cụ tìm kiếm để tìm kính phù hợp.
                Bạn có thể tìm kiếm bằng text hoặc hình ảnh.
                Hãy trả về kết quả tìm kiếm một cách rõ ràng và chi tiết."""
            }
        }
        return configs.get(agent_name, {}) 