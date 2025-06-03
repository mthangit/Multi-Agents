#!/usr/bin/env python3
"""
Main Application cho PDF RAG System với Google Gemini
Sử dụng kiến trúc tách biệt: Data Ingestion (script) + Chatbot (class)
"""

import os
import sys
from pathlib import Path
from typing import List

from chatbot import PDFChatbot, create_chatbot, get_chatbot
from config import Config

def check_data_folder():
    """
    Kiểm tra thư mục data có tồn tại không
    """
    data_folder = Path("data")
    
    if not data_folder.exists():
        print("❌ Thư mục 'data' không tồn tại!")
        print("💡 Tạo thư mục data và đặt file PDF:")
        print("   mkdir data")
        print("   cp your_files.pdf data/")
        return False
    
    # Kiểm tra có PDF không
    import glob
    pdf_files = glob.glob("data/**/*.pdf", recursive=True)
    
    if not pdf_files:
        print("❌ Không có file PDF nào trong thư mục 'data'!")
        print("💡 Đặt file PDF vào thư mục data:")
        print("   cp your_files.pdf data/")
        print("   # Hoặc tạo subfolder:")
        print("   mkdir data/documents && cp *.pdf data/documents/")
        return False
    
    print(f"✅ Tìm thấy {len(pdf_files)} PDF files trong data/")
    return True

def demo_chatbot():
    """
    Demo sử dụng chatbot class
    """
    print("=" * 60)
    print("🚀 DEMO PDF CHATBOT (GOOGLE GEMINI)")
    print("=" * 60)
    
    try:
        # Tạo chatbot instance
        chatbot = create_chatbot()
        
        # Kiểm tra trạng thái
        stats = chatbot.get_collection_stats()
        if stats["status"] == "success":
            print(f"📊 Collection có {stats['vectors_count']} vectors")
        else:
            print(f"❌ Lỗi collection: {stats.get('error')}")
            print("💡 Hãy chạy data ingestion trước:")
            print("   python ingest_data.py")
            return
        
        # Demo các câu hỏi mắt kính
        demo_questions = [
            "Tôi bị cận thị 2.5 độ, nên chọn loại tròng kính nào?",
            "Kính chống ánh sáng xanh có thực sự hiệu quả không?",
            "Khuôn mặt tròn phù hợp với kiểu gọng nào?",
            "So sánh tròng kính đa tròng và đơn tròng?",
            "Chất liệu gọng titan có ưu điểm gì?"
        ]
        
        print(f"\n📋 DEMO: Đặt câu hỏi với Chatbot")
        for i, question in enumerate(demo_questions, 1):
            print(f"\n❓ [{i}] {question}")
            print("-" * 50)
            
            # Sử dụng invoke method
            result = chatbot.invoke(question, verbose=True)
            
            if result["status"] == "success":
                print(f"🤖 Trả lời:")
                print(result["answer"])
                print(f"\n📊 Thông tin:")
                print(f"   - Số docs liên quan: {result['relevant_docs_count']}")
                print(f"   - Nguồn: {', '.join(result['sources'])}")
            else:
                print(f"❌ Lỗi: {result['error']}")
        
        # Chuyển sang chế độ tương tác
        interactive_chat(chatbot)
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo chatbot: {e}")
        print("💡 Hãy kiểm tra:")
        print("   1. Qdrant server đang chạy")
        print("   2. Đã chạy ingest_data.py")
        print("   3. Google API key đã được cấu hình")

def interactive_chat(chatbot: PDFChatbot):
    """
    Chế độ chat tương tác với chatbot
    """
    print(f"\n🎯 CHẾ ĐỘ CHAT TƯƠNG TÁC")
    print("Commands:")
    print("  - 'exit' hoặc 'quit': Thoát")
    print("  - 'help': Hiển thị trợ giúp")
    print("  - 'stats': Thống kê collection")
    print("  - 'health': Kiểm tra sức khỏe chatbot")
    print("  - Hoặc đặt câu hỏi trực tiếp")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n💬 Bạn: ").strip()
            
            if not user_input:
                continue
                
            # Commands
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Tạm biệt!")
                break
                
            elif user_input.lower() == 'help':
                print("""
🔧 HƯỚNG DẪN SỬ DỤNG CHATBOT:
- Đặt câu hỏi về nội dung tài liệu PDF
- 'stats': Xem thống kê collection
- 'health': Kiểm tra trạng thái hệ thống
- 'exit': Thoát chương trình

💡 Tips:
- Câu hỏi rõ ràng, cụ thể sẽ có kết quả tốt hơn
- Chatbot sẽ trả lời dựa trên nội dung đã được nạp
                """)
                
            elif user_input.lower() == 'stats':
                stats = chatbot.get_collection_stats()
                print(f"📊 Thống kê Collection:")
                if stats["status"] == "success":
                    print(f"   Collection: {stats['collection_name']}")
                    print(f"   Vectors: {stats['vectors_count']}")
                    print(f"   Status: {stats['collection_status']}")
                else:
                    print(f"   Lỗi: {stats['error']}")
                    
            elif user_input.lower() == 'health':
                health = chatbot.health_check()
                print(f"🏥 Trạng thái Chatbot:")
                print(f"   Status: {health['status']}")
                if "components" in health:
                    print(f"   Components:")
                    for comp, status in health["components"].items():
                        print(f"     - {comp}: {status}")
                    print(f"   Collection vectors: {health.get('collection_vectors', 0)}")
                
            else:
                # Xử lý câu hỏi
                print("🤖 Đang suy nghĩ...")
                result = chatbot.invoke(user_input)
                
                if result["status"] == "success":
                    print(f"\n🤖 Trả lời:")
                    print(result["answer"])
                    
                    if result["sources"]:
                        print(f"\n📚 Nguồn: {', '.join(result['sources'])}")
                        
                    if result["relevant_docs_count"] > 0:
                        print(f"📊 Dựa trên {result['relevant_docs_count']} đoạn văn liên quan")
                else:
                    print(f"❌ {result['answer']}")
                
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")

def batch_demo():
    """
    Demo xử lý batch queries
    """
    print("=" * 60)
    print("📝 DEMO BATCH PROCESSING")
    print("=" * 60)
    
    try:
        chatbot = create_chatbot()
        
        # Batch questions cho domain mắt kính
        questions = [
            "Tôi bị loạn thị, có những lựa chọn tròng kính nào?",
            "Gọng kim loại và gọng nhựa khác nhau như thế nào?", 
            "Kính photochromic hoạt động ra sao?",
            "Làm sao để chăm sóc và bảo quản kính đúng cách?",
            "Xu hướng kính mắt năm 2024 là gì?"
        ]
        
        print(f"🔄 Xử lý {len(questions)} câu hỏi...")
        results = chatbot.batch_invoke(questions, verbose=True)
        
        print(f"\n📋 KẾT QUẢ BATCH:")
        for i, (question, result) in enumerate(zip(questions, results), 1):
            print(f"\n[{i}] {question}")
            if result["status"] == "success":
                print(f"✅ Đã trả lời (từ {result['relevant_docs_count']} docs)")
            else:
                print(f"❌ Lỗi: {result.get('error')}")
                
    except Exception as e:
        print(f"❌ Lỗi batch demo: {e}")

def check_data_ingestion():
    """
    Kiểm tra xem đã có dữ liệu chưa và hướng dẫn nếu chưa
    """
    print("🔍 Kiểm tra dữ liệu...")
    
    # Kiểm tra thư mục data trước
    if not check_data_folder():
        return False
    
    try:
        chatbot = create_chatbot()
        stats = chatbot.get_collection_stats()
        
        if stats["status"] == "success" and stats["vectors_count"] > 0:
            print(f"✅ Đã có {stats['vectors_count']} vectors trong collection")
            return True
        else:
            print("❌ Collection rỗng hoặc chưa tồn tại")
            print("\n💡 HƯỚNG DẪN NẠP DỮ LIỆU:")
            print("   1. Đã có PDF trong data/ ✅")
            print("   2. Chạy script nạp dữ liệu:")
            print("      python ingest_data.py")
            print("   3. Hoặc với options:")
            print("      python ingest_data.py --clear  # Xóa dữ liệu cũ")
            print("   4. Chạy lại chương trình này")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kiểm tra: {e}")
        return False

def show_system_info():
    """
    Hiển thị thông tin hệ thống
    """
    print("📋 THÔNG TIN HỆ THỐNG")
    print("=" * 60)
    print(f"🤖 LLM Model: {Config.GEMINI_MODEL}")
    print(f"🧮 Embedding Model: {Config.EMBEDDING_MODEL}")
    print(f"🗄️  Qdrant URL: {Config.QDRANT_URL}")
    print(f"📁 Collection: {Config.COLLECTION_NAME}")
    print(f"🌡️  Temperature: {Config.GEMINI_TEMPERATURE}")
    print(f"📊 Top K Documents: {Config.TOP_K_DOCUMENTS}")
    print(f"🎯 Similarity Threshold: {Config.SIMILARITY_THRESHOLD}")
    
    # Kiểm tra API key
    if Config.GOOGLE_API_KEY == "your_google_api_key_here":
        print(f"\n⚠️  CHƯA CẤU HÌNH GOOGLE_API_KEY")
        print(f"   Lấy API key tại: https://makersuite.google.com/app/apikey")
    else:
        print(f"✅ Google API Key đã được cấu hình")
    
    # Kiểm tra data folder
    print(f"\n📁 Data Folder:")
    if check_data_folder():
        print(f"   ✅ Thư mục data sẵn sàng")
    else:
        print(f"   ❌ Thư mục data chưa ready")

def setup_guide():
    """
    Hướng dẫn setup lần đầu
    """
    print("=" * 60)
    print("🚀 HƯỚNG DẪN SETUP LẦN ĐẦU")
    print("=" * 60)
    
    print("📋 Các bước cần thực hiện:")
    
    # 1. Kiểm tra data folder
    print("\n1️⃣ Kiểm tra thư mục data:")
    if check_data_folder():
        print("   ✅ DONE")
    else:
        print("   ❌ TODO: Tạo thư mục data và đặt PDF")
        return
    
    # 2. Kiểm tra Qdrant
    print("\n2️⃣ Kiểm tra Qdrant server:")
    try:
        from utils.qdrant_manager import QdrantManager
        qm = QdrantManager()
        qm.get_collection_info()
        print("   ✅ DONE: Qdrant đang chạy")
    except Exception as e:
        print(f"   ❌ TODO: Khởi động Qdrant server")
        print(f"        docker-compose up -d")
        return
    
    # 3. Kiểm tra API key
    print("\n3️⃣ Kiểm tra Google API key:")
    if Config.GOOGLE_API_KEY != "your_google_api_key_here":
        print("   ✅ DONE")
    else:
        print("   ❌ TODO: Cấu hình Google API key")
        print("        export GOOGLE_API_KEY='your_key'")
        return
    
    # 4. Kiểm tra data ingestion
    print("\n4️⃣ Kiểm tra data ingestion:")
    try:
        chatbot = create_chatbot()
        stats = chatbot.get_collection_stats()
        if stats["status"] == "success" and stats["vectors_count"] > 0:
            print(f"   ✅ DONE: {stats['vectors_count']} vectors")
        else:
            print("   ❌ TODO: Chạy data ingestion")
            print("        python ingest_data.py")
            return
    except:
        print("   ❌ TODO: Chạy data ingestion")
        print("        python ingest_data.py")
        return
    
    print(f"\n🎉 SETUP HOÀN TẤT!")
    print(f"💡 Có thể bắt đầu sử dụng:")
    print(f"   python main.py demo")

def main():
    """
    Main function với multiple modes
    """
    print("🚀 PDF RAG CHATBOT SYSTEM (GOOGLE GEMINI)")
    print("Kiến trúc: Data Ingestion (script) + Chatbot (class)")
    print("📁 Data folder: ./data/")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "demo":
            demo_chatbot()
        elif mode == "interactive":
            if check_data_ingestion():
                chatbot = create_chatbot()
                interactive_chat(chatbot)
        elif mode == "batch":
            batch_demo()
        elif mode == "check":
            check_data_ingestion()
        elif mode == "info":
            show_system_info()
        elif mode == "setup":
            setup_guide()
        else:
            print(f"❌ Mode không hợp lệ: {mode}")
            print_usage()
    else:
        # Mặc định: kiểm tra dữ liệu và chạy demo
        print_usage()
        
        if check_data_ingestion():
            print(f"\n🎯 Bắt đầu demo...")
            demo_chatbot()
        else:
            print(f"\n💡 Chạy setup guide:")
            print(f"   python main.py setup")

def print_usage():
    """
    In hướng dẫn sử dụng
    """
    print(f"\n📖 CÁCH SỬ DỤNG:")
    print(f"   python main.py [mode]")
    print(f"\n🔧 Modes:")
    print(f"   demo        - Demo chatbot với câu hỏi mẫu")
    print(f"   interactive - Chế độ chat tương tác")
    print(f"   batch       - Demo xử lý batch queries")
    print(f"   check       - Kiểm tra trạng thái dữ liệu")
    print(f"   info        - Hiển thị thông tin hệ thống")
    print(f"   setup       - Hướng dẫn setup lần đầu")
    print(f"\n💾 NẠP DỮ LIỆU:")
    print(f"   1. Đặt PDF vào thư mục data/")
    print(f"   2. python ingest_data.py")
    print(f"   3. python main.py demo")

if __name__ == "__main__":
    main() 