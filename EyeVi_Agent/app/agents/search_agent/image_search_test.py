#!/usr/bin/env python3
"""
Script kiểm tra chức năng tìm kiếm bằng ảnh qua A2A
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

from client import AdvisorAgentClient

async def test_image_search(image_path: str, description: str = "", agent_url: str = "http://localhost:10002"):
    """
    Kiểm tra chức năng tìm kiếm bằng ảnh.
    
    Args:
        image_path: Đường dẫn đến file ảnh
        description: Mô tả về ảnh (tùy chọn)
        agent_url: URL của agent
    """
    print("=" * 60)
    print("🔍 KIỂM TRA TÌM KIẾM BẰNG ẢNH")
    print("=" * 60)
    
    # Kiểm tra file ảnh tồn tại
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy file ảnh: {image_path}")
        return
    
    print(f"🖼️ File ảnh: {image_path}")
    print(f"📝 Mô tả: {description}")
    print(f"🔗 Agent URL: {agent_url}")
    print("─" * 60)
    
    # Khởi tạo client
    client = AdvisorAgentClient(base_url=agent_url)
    
    try:
        # Khởi tạo kết nối
        await client.initialize()
        print("✅ Đã kết nối đến agent")
        
        # Gửi ảnh để tìm kiếm
        print("🔄 Đang gửi ảnh để tìm kiếm...")
        result = await client.send_message_with_image(
            message=description,
            image_path=image_path
        )
        
        # Hiển thị kết quả
        if result["status"] == "success":
            print("\n🔍 KẾT QUẢ TÌM KIẾM:")
            print("─" * 60)
            print(result["content"])
            print("─" * 60)
            print(f"📊 Task ID: {result['task_id']}")
        else:
            print(f"❌ Lỗi: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {str(e)}")
    finally:
        # Đóng kết nối
        await client.close()
        print("👋 Đã đóng kết nối")

def main():
    """Hàm chính xử lý tham số dòng lệnh."""
    parser = argparse.ArgumentParser(description="Kiểm tra chức năng tìm kiếm bằng ảnh qua A2A")
    parser.add_argument("image_path", help="Đường dẫn đến file ảnh cần tìm kiếm")
    parser.add_argument("-d", "--description", default="", help="Mô tả về ảnh (tùy chọn)")
    parser.add_argument("-u", "--url", default="http://localhost:10002", help="URL của agent (mặc định: http://localhost:10002)")
    
    args = parser.parse_args()
    
    # Chạy hàm kiểm tra
    asyncio.run(test_image_search(args.image_path, args.description, args.url))

if __name__ == "__main__":
    main() 