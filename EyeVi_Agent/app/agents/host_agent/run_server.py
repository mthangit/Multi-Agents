#!/usr/bin/env python3
"""
Script để chạy Host Agent Server
"""

import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function để chạy server"""
    try:
        # Lấy config từ environment variables
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8080"))
        reload = os.getenv("RELOAD", "true").lower() == "true"
        
        logger.info("🚀 Đang khởi động Host Agent Server...")
        logger.info(f"📍 Host: {host}")
        logger.info(f"🔌 Port: {port}")
        logger.info(f"🔄 Reload: {reload}")
        
        # Kiểm tra GOOGLE_API_KEY
        if not os.getenv("GOOGLE_API_KEY"):
            logger.error("❌ GOOGLE_API_KEY environment variable is required!")
            sys.exit(1)
        
        # Chạy server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi động server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
