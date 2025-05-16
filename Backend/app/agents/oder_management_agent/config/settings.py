"""
Cấu hình chung cho shopping agent
"""
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Cấu hình database
DB_CONFIG: Dict[str, Any] = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "shopping_db"),
    "port": int(os.getenv("DB_PORT", "3306"))
}

# Cấu hình Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ADK config
APP_NAME = "shopping_assistant"
DEFAULT_USER_ID = "default_user"

# Agent cấu hình
AGENT_CONFIG = {
    "temperature": 0.2,  # Độ sáng tạo của model (0.0 - 1.0)
    "top_p": 0.95,       # Sampling parameter
    "top_k": 40,         # Top k tokens to sample from
    "max_tokens": 8192,  # Số tokens tối đa cho mỗi phản hồi
}

# Tool timeout (seconds)
TOOL_TIMEOUT = 30

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 