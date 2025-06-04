#!/usr/bin/env python3
"""
CLI Chat Interface cho Order Management Agent
"""
import asyncio
import sys
import os
import logging
from typing import AsyncIterator
import signal
from datetime import datetime

# Thêm src vào Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import configuration và dependencies
from src.config import settings
from src.database import initialize_database_connections
from src.chatbot.langgraph_bot import ChatbotGraph

# Thiết lập logging cho CLI
logging.basicConfig(
    level=logging.WARNING,  # Chỉ hiển thị warning và error để CLI sạch sẽ
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("cli.log")
    ]
)
logger = logging.getLogger("cli")

class ChatCLI:
    def __init__(self):
        self.chatbot = None
        self.session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.running = True
        
    async def initialize(self):
        """Khởi tạo chatbot và database connections"""
        try:
            print("🚀 Đang khởi tạo hệ thống...")
            
            # Khởi tạo database connections
            initialize_database_connections()
            print("✅ Database đã kết nối thành công")
            
            # Khởi tạo chatbot
            self.chatbot = ChatbotGraph()
            print("✅ Chatbot đã khởi tạo thành công")
            
            print("🎉 Hệ thống đã sẵn sàng!")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo: {str(e)}")
            logger.error(f"Failed to initialize: {str(e)}")
            sys.exit(1)
    
    def print_welcome(self):
        """In thông điệp chào mừng"""
        print("\n" + "="*60)
        print("🤖 CHÀO MỪNG ĐÊN ORDER MANAGEMENT CHATBOT CLI")
        print("="*60)
        print("Gõ 'help' để xem hướng dẫn")
        print("Gõ 'quit', 'exit' hoặc Ctrl+C để thoát")
        print("Gõ 'clear' để xóa màn hình")
        print("="*60 + "\n")
    
    def print_commands_help(self):
        """In danh sách lệnh CLI"""
        print("\n📋 CÁC LỆNH CLI:")
        print("  help    - Hiển thị trợ giúp từ chatbot")
        print("  quit    - Thoát chương trình")
        print("  exit    - Thoát chương trình") 
        print("  clear   - Xóa màn hình")
        print("  status  - Kiểm tra trạng thái hệ thống")
        print("\n💬 Hoặc bạn có thể chat trực tiếp với bot!")
        print("   Ví dụ: 'Tìm sản phẩm iPhone'")
        print("   Ví dụ: 'Thêm sản phẩm ID 123 vào giỏ hàng'\n")
    
    async def process_user_input(self, user_input: str) -> bool:
        """Xử lý input từ user, trả về False nếu muốn thoát"""
        user_input = user_input.strip()
        
        # Xử lý các lệnh CLI đặc biệt
        if user_input.lower() in ['quit', 'exit']:
            return False
        elif user_input.lower() == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_welcome()
            return True
        elif user_input.lower() == 'status':
            await self.print_status()
            return True
        elif user_input.lower() == 'cli-help':
            self.print_commands_help()
            return True
        
        # Nếu không có input, không làm gì
        if not user_input:
            return True
        
        # Xử lý tin nhắn chat
        await self.chat_with_streaming(user_input)
        return True
    
    async def chat_with_streaming(self, message: str):
        """Chat với bot sử dụng streaming response"""
        try:
            print(f"\n👤 Bạn: {message}")
            
            # Sử dụng streaming version nếu có
            if hasattr(self.chatbot, 'process_message_streaming'):
                bot_label_printed = False
                response_buffer = ""
                
                async for chunk in self.chatbot.process_message_streaming(message, self.session_id):
                    # Xử lý chunk đặc biệt để clear processing message
                    if chunk.startswith("\r🤖 Bot: "):
                        print(f"\r🤖 Bot: ", end="", flush=True)
                        bot_label_printed = True
                        continue
                    
                    # In label bot nếu chưa in
                    if not bot_label_printed:
                        print("🤖 Bot: ", end="", flush=True)
                        bot_label_printed = True
                    
                    print(chunk, end="", flush=True)
                    response_buffer += chunk
                
                print()  # New line sau khi hoàn thành
                
                # Log response để debug nếu cần
                if response_buffer:
                    logger.info(f"Complete response: {response_buffer}")
                    
            else:
                # Fallback về sync version nếu streaming không có
                print("🤖 Bot: ", end="", flush=True)
                response = self.chatbot.process_message(message, self.session_id)
                
                # Giả lập streaming với hiệu ứng typing
                for char in response:
                    print(char, end="", flush=True)
                    await asyncio.sleep(0.02)  # Delay nhỏ để tạo hiệu ứng
                print()
                
        except Exception as e:
            print(f"\n❌ Lỗi khi xử lý tin nhắn: {str(e)}")
            logger.error(f"Error processing message: {str(e)}")
            # In gợi ý cách sử dụng
            print("💡 Hãy thử lại hoặc gõ 'help' để xem hướng dẫn")
    
    async def print_status(self):
        """In trạng thái hệ thống"""
        print("\n📊 TRẠNG THÁI HỆ THỐNG:")
        print(f"  Session ID: {self.session_id}")
        print(f"  Chatbot: {'✅ Hoạt động' if self.chatbot else '❌ Không hoạt động'}")
        
        # Kiểm tra kết nối database
        try:
            from src.database import DatabaseConnection
            db = DatabaseConnection.get_instance()
            print("  MySQL Database: ✅ Đã kết nối")
        except Exception as e:
            print(f"  MySQL Database: ❌ Lỗi - {str(e)}")
        
        try:
            from src.database import MongoDBConnection
            mongo = MongoDBConnection.get_instance()
            print("  MongoDB: ✅ Đã kết nối")
        except Exception as e:
            print(f"  MongoDB: ❌ Lỗi - {str(e)}")
        
        print()
    
    def setup_signal_handlers(self):
        """Setup signal handlers cho graceful shutdown"""
        def signal_handler(signum, frame):
            print("\n\n👋 Đang thoát chương trình...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_interactive_loop(self):
        """Chạy vòng lặp tương tác chính"""
        self.setup_signal_handlers()
        self.print_welcome()
        
        while self.running:
            try:
                # Sử dụng input thông thường vì asyncio input phức tạp
                user_input = input("💬 Bạn: ")
                should_continue = await self.process_user_input(user_input)
                
                if not should_continue:
                    break
                    
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Đang thoát chương trình...")
                break
            except Exception as e:
                print(f"❌ Lỗi không mong muốn: {str(e)}")
                logger.error(f"Unexpected error: {str(e)}")
    
    async def run(self):
        """Chạy CLI application"""
        try:
            await self.initialize()
            await self.run_interactive_loop()
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng: {str(e)}")
            logger.error(f"Critical error: {str(e)}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Dọn dẹp resources khi thoát"""
        try:
            print("🧹 Đang dọn dẹp...")
            
            # Đóng database connections
            try:
                from src.database import DatabaseConnection, MongoDBConnection
                DatabaseConnection.get_instance().close()
                MongoDBConnection.get_instance().close()
            except:
                pass
                
            print("✅ Dọn dẹp hoàn tất")
            
        except Exception as e:
            print(f"⚠️ Lỗi khi dọn dẹp: {str(e)}")

async def main():
    """Entry point cho CLI"""
    cli = ChatCLI()
    await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
        sys.exit(0) 