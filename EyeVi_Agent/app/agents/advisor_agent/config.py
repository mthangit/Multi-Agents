import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Google Gemini API configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "your_google_api_key_here")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Database configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "eyewear_advisor")  # Domain-specific name
    
    # Embedding Model - Optimized for Vietnamese + Technical Terms
    # Domain: Optical/Eyewear - cần balance giữa Vietnamese và technical terms
    # Recommendation: multilingual-e5-base cho quality cao với medical/technical terms
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    
    # Chunking Strategy - Optimized for Product Catalog + Technical Info
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))        # Nhỏ hơn cho product specificity
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))  # Vừa phải cho technical content
    
    # Retrieval settings - Tuned for Product Recommendations
    TOP_K_DOCUMENTS = int(os.getenv("TOP_K_DOCUMENTS", "8"))            # Tăng cho đa dạng sản phẩm
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.68"))  # Cao hơn cho precision
    
    # Advanced chunking options - Eyewear domain specific
    CHUNK_STRATEGY = os.getenv("CHUNK_STRATEGY", "recursive")  # Tốt cho mixed content
    OVERLAP_METHOD = os.getenv("OVERLAP_METHOD", "sentence")   # Preserve technical definitions
    
    # Gemini specific settings - Tuned for advisory responses
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))  # Cao hơn cho creative recommendations
    GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    
    # Embedding optimization
    NORMALIZE_EMBEDDINGS = os.getenv("NORMALIZE_EMBEDDINGS", "true").lower() == "true"
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Domain-specific settings
    DOMAIN = "eyewear_advisor"
    ENABLE_PRODUCT_RECOMMENDATIONS = os.getenv("ENABLE_PRODUCT_RECOMMENDATIONS", "true").lower() == "true"
    ENABLE_TECHNICAL_ADVICE = os.getenv("ENABLE_TECHNICAL_ADVICE", "true").lower() == "true"
    
    

# Model recommendations by use case
EMBEDDING_RECOMMENDATIONS = {
    "eyewear_optimal": {
        "model": "intfloat/multilingual-e5-base",
        "dimension": 768,
        "description": "Tối ưu cho domain mắt kính - balanced Vietnamese + technical terms",
        "chunk_size": 700,
        "chunk_overlap": 120,
        "top_k": 8,
        "threshold": 0.68
    },
    "eyewear_fast": {
        "model": "intfloat/multilingual-e5-small", 
        "dimension": 384,
        "description": "Nhanh hơn cho demo, vẫn tốt cho technical content",
        "chunk_size": 600,
        "chunk_overlap": 100,
        "top_k": 6,
        "threshold": 0.65
    },
    "eyewear_precision": {
        "model": "sentence-transformers/all-mpnet-base-v2",
        "dimension": 768,
        "description": "Precision cao cho medical advice (nếu content chủ yếu English)",
        "chunk_size": 800,
        "chunk_overlap": 150,
        "top_k": 10,
        "threshold": 0.72
    }
}

# Domain-specific keywords for enhanced retrieval
EYEWEAR_KEYWORDS = {
    "vision_conditions": [
        "cận thị", "myopia", "viễn thị", "hyperopia", "loạn thị", "astigmatism",
        "lão thị", "presbyopia", "tật khúc xạ", "refractive error"
    ],
    "lens_types": [
        "tròng kính", "lens", "đơn tròng", "đa tròng", "progressive", "bifocal",
        "kính chống ánh sáng xanh", "blue light", "kính photochromic", "transition"
    ],
    "frame_styles": [
        "gọng kính", "frame", "gọng tròn", "round", "gọng vuông", "square",
        "gọng kim loại", "metal", "gọng nhựa", "plastic", "rimless", "semi-rimless"
    ],
    "brands_materials": [
        "titan", "titanium", "acetate", "TR90", "memory metal",
        "kính cường lực", "tempered", "coating", "lớp phủ"
    ]
} 