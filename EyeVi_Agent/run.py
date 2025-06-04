import argparse
import uvicorn
import os
from dotenv import load_dotenv

from src.config.settings import API_HOST, API_PORT, DEBUG

def main():
    """Hàm chính để khởi chạy ứng dụng"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Multi-Agent RAG System")
    parser.add_argument("--host", type=str, default=API_HOST, help="Host to run the API on")
    parser.add_argument("--port", type=int, default=API_PORT, help="Port to run the API on")
    parser.add_argument("--debug", action="store_true", default=DEBUG, help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Hiển thị thông báo khởi động
    print(f"Khởi động hệ thống Multi-Agent RAG trên {args.host}:{args.port}")
    print(f"Debug mode: {args.debug}")
    
    # Khởi chạy API
    uvicorn.run(
        "src.api.app:app", 
        host=args.host, 
        port=args.port, 
        reload=args.debug
    )

if __name__ == "__main__":
    # Đảm bảo đã load biến môi trường
    load_dotenv()
    # Chạy ứng dụng
    main() 


# python -m app.agents.search_agent.run_server --host 0.0.0.0 --port 8001 --reload