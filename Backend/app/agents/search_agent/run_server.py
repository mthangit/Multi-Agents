#!/usr/bin/env python
"""
Script khởi động server API cho Search Agent
"""

import os
import argparse
import uvicorn
import logging

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse các tham số dòng lệnh."""
    parser = argparse.ArgumentParser(description='Khởi động Search Agent API server')
    parser.add_argument(
        '--host', 
        type=str, 
        default='0.0.0.0',
        help='Host để lắng nghe (mặc định: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8001,
        help='Port để lắng nghe (mặc định: 8001)'
    )
    parser.add_argument(
        '--reload', 
        action='store_true',
        help='Bật chế độ tự động reload khi code thay đổi'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Bật chế độ debug'
    )
    return parser.parse_args()

def main():
    """Hàm chính khởi động server."""
    args = parse_args()
    
    # Hiển thị thông tin khởi động
    logger.info(f"Khởi động Search Agent API server tại http://{args.host}:{args.port}")
    logger.info(f"OpenAPI docs: http://{args.host}:{args.port}/docs")
    logger.info(f"Agent Card: http://{args.host}:{args.port}/.well-known/agent.json")
    
    # Thiết lập level logging nếu ở chế độ debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Lưu thông tin host và port vào môi trường
    os.environ["SEARCH_AGENT_HOST"] = args.host
    os.environ["SEARCH_AGENT_PORT"] = str(args.port)
    
    # Khởi động server
    uvicorn.run(
        "api.endpoints:app", 
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main() 