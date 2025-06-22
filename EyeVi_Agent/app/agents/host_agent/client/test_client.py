#!/usr/bin/env python3
"""
Test client cho Host Agent
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Any, List

class HostAgentClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def chat(self, message: str, user_id: str = None, session_id: str = None, file_paths: List[str] = None) -> Dict[str, Any]:
        """Gửi message tới host agent (có thể kèm files)"""
        try:
            # Prepare form data
            data = {"message": message}
            if user_id:
                data["user_id"] = user_id
            if session_id:
                data["session_id"] = session_id

            # Prepare files if any
            files = []
            if file_paths:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            files.append(('files', (os.path.basename(file_path), f.read(), 'image/jpeg')))

            response = await self.client.post(
                f"{self.base_url}/chat",
                data=data,
                files=files if files else None
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "detail": response.text
                }
                
        except Exception as e:
            return {"error": str(e)}

    async def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Lấy chat history cho session"""
        try:
            response = await self.client.get(f"{self.base_url}/sessions/{session_id}/history")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def clear_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Xóa chat history cho session"""
        try:
            response = await self.client.delete(f"{self.base_url}/sessions/{session_id}/history")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def list_sessions(self) -> Dict[str, Any]:
        """Liệt kê các active sessions"""
        try:
            response = await self.client.get(f"{self.base_url}/sessions")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Kiểm tra health của host agent"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def get_agents_status(self) -> Dict[str, Any]:
        """Lấy status của tất cả agents"""
        try:
            response = await self.client.get(f"{self.base_url}/agents/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def create_test_image(self, filename: str = "test_image.jpg") -> str:
        """Tạo file ảnh test đơn giản"""
        try:
            # Tạo ảnh test 100x100 pixel màu đỏ đơn giản
            import base64
            
            # JPEG header nhỏ nhất
            jpeg_data = base64.b64decode('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A==')
            
            with open(filename, 'wb') as f:
                f.write(jpeg_data)
            
            return filename
            
        except Exception as e:
            print(f"Failed to create test image: {e}")
            return None

    async def close(self):
        """Close client"""
        await self.client.aclose()

async def main():
    """Test function"""
    client = HostAgentClient()
    
    print("🧪 Bắt đầu test Host Agent Client...")
    
    try:
        # Test health check
        print("\n1. 🏥 Kiểm tra health...")
        health = await client.health_check()
        print(f"Health: {json.dumps(health, indent=2, ensure_ascii=False)}")
        
        # Test agents status
        print("\n2. 📊 Kiểm tra status các agents...")
        status = await client.get_agents_status()
        print(f"Agents Status: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # Test với session ID để test chat history
        session_id = "test_session_123"
        
        # Test chat - tư vấn
        print(f"\n3. 💬 Test chat - yêu cầu tư vấn (Session: {session_id})...")
        result = await client.chat("Tôi bị cận thị 2.5 độ, nên chọn loại kính nào?", session_id=session_id)
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Test chat - câu hỏi tiếp theo với context
        print("\n4. 💬 Test chat - câu hỏi tiếp theo với context...")
        result = await client.chat("Vậy có loại nào rẻ hơn không?", session_id=session_id)
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Test chat - tìm kiếm
        print("\n5. 🔍 Test chat - yêu cầu tìm kiếm...")
        result = await client.chat("Tìm kính cận thị cho nam màu đen", session_id=session_id)
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Test chat - đặt hàng
        print("\n6. 🛍️ Test chat - yêu cầu đặt hàng...")
        result = await client.chat("Tôi muốn xem thông tin sản phẩm ID 123", session_id=session_id)
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Test lấy chat history
        print(f"\n7. 📖 Test lấy chat history...")
        history = await client.get_chat_history(session_id)
        print(f"Chat History: {json.dumps(history, indent=2, ensure_ascii=False)}")
        
        # Test list sessions
        print(f"\n8. 📋 Test list active sessions...")
        sessions = await client.list_sessions()
        print(f"Active Sessions: {json.dumps(sessions, indent=2, ensure_ascii=False)}")
        
        # Test chat với file upload
        print(f"\n9. 📎 Test chat với file upload...")
        test_image_path = await client.create_test_image("test_image.jpg")
        if test_image_path:
            result = await client.chat(
                message="Hãy phân tích ảnh này giúp tôi", 
                session_id=session_id,
                file_paths=[test_image_path]
            )
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Xóa file test sau khi dùng
            try:
                os.remove(test_image_path)
                print(f"Đã xóa file test: {test_image_path}")
            except:
                pass
        else:
            print("Không thể tạo file test image")
        
        # Test clear history
        print(f"\n10. 🗑️ Test clear chat history...")
        clear_result = await client.clear_chat_history(session_id)
        print(f"Clear Result: {json.dumps(clear_result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ Lỗi khi test: {e}")
    
    finally:
        await client.close()
        print("\n✅ Test hoàn tất!")

if __name__ == "__main__":
    asyncio.run(main()) 