#!/usr/bin/env python3
"""
Ví dụ sử dụng hệ thống PDF RAG với Google Gemini
Mô tả các scenario sử dụng khác nhau
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow.langgraph_workflow import PDFRAGWorkflow
from main import PDFRAGSystem

def example_1_basic_usage():
    """
    Ví dụ 1: Sử dụng cơ bản - thêm PDF và hỏi đáp với Gemini
    """
    print("=" * 60)
    print("📋 VÍ DỤ 1: SỬ DỤNG CƠ BẢN (GEMINI)")
    print("=" * 60)
    
    # Khởi tạo hệ thống
    system = PDFRAGSystem()
    
    # Giả sử có file PDF mẫu
    sample_pdfs = [
        "data/research_paper.pdf",
        "data/technical_manual.pdf"
    ]
    
    # Kiểm tra file tồn tại
    existing_pdfs = [pdf for pdf in sample_pdfs if os.path.exists(pdf)]
    
    if existing_pdfs:
        print(f"📄 Thêm {len(existing_pdfs)} file PDF...")
        success = system.add_documents(existing_pdfs)
        
        if success:
            # Đặt câu hỏi
            questions = [
                "Tài liệu này nói về chủ đề gì?",
                "Có những phương pháp nào được đề cập?",
                "Kết luận chính là gì?"
            ]
            
            for q in questions:
                result = system.ask_question(q)
                print()
    else:
        print("⚠️  Không tìm thấy file PDF mẫu")
        print("   Hãy đặt file PDF vào thư mục 'data/' để test")

def example_2_workflow_direct():
    """
    Ví dụ 2: Sử dụng trực tiếp LangGraph workflow với Gemini
    """
    print("\n" + "=" * 60)
    print("🔧 VÍ DỤ 2: SỬ DỤNG TRỰC TIẾP WORKFLOW (GEMINI)")
    print("=" * 60)
    
    # Khởi tạo workflow
    workflow = PDFRAGWorkflow()
    
    # Xử lý documents trước
    pdf_paths = ["data/document1.pdf"]
    
    if any(os.path.exists(pdf) for pdf in pdf_paths):
        print("📄 Xử lý documents...")
        doc_result = workflow.run_document_processing(pdf_paths)
        print(f"📊 Kết quả: {doc_result}")
        
        # Truy vấn
        query_result = workflow.run_query("Tóm tắt nội dung chính")
        print(f"🤖 Câu trả lời (Gemini): {query_result['answer']}")
        print(f"📚 Nguồn: {query_result['sources']}")
    else:
        print("⚠️  Không tìm thấy file PDF để test")

def example_3_batch_questions():
    """
    Ví dụ 3: Xử lý nhiều câu hỏi liên tiếp với Gemini
    """
    print("\n" + "=" * 60)
    print("📝 VÍ DỤ 3: BATCH PROCESSING (GEMINI)")
    print("=" * 60)
    
    system = PDFRAGSystem()
    
    # Danh sách câu hỏi research
    research_questions = [
        "Vấn đề nghiên cứu chính là gì?",
        "Phương pháp nghiên cứu được sử dụng?",
        "Kết quả quan trọng nào được tìm thấy?",
        "Những hạn chế của nghiên cứu?",
        "Hướng nghiên cứu tương lai được đề xuất?"
    ]
    
    print("📋 Xử lý batch questions với Gemini...")
    for i, question in enumerate(research_questions, 1):
        print(f"\n🔍 Câu hỏi {i}: {question}")
        result = system.ask_question(question)
        if result.get("status") == "success":
            print(f"✅ Đã trả lời (từ {result.get('relevant_docs_count', 0)} docs)")
        else:
            print(f"❌ Lỗi: {result.get('error')}")

def example_4_collection_management():
    """
    Ví dụ 4: Quản lý collection và monitoring
    """
    print("\n" + "=" * 60)
    print("📊 VÍ DỤ 4: QUẢN LÝ COLLECTION")
    print("=" * 60)
    
    workflow = PDFRAGWorkflow()
    
    # Kiểm tra collection info
    print("📋 Thông tin collection:")
    info = workflow.qdrant_manager.get_collection_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Demo thêm/xóa documents
    print("\n🔧 Thử nghiệm các operations:")
    
    # Thử tìm kiếm với query rỗng (chỉ để test)
    try:
        # Tạo embedding cho query test
        test_embedding = workflow.embedding_manager.embed_query("test")
        results = workflow.qdrant_manager.search_similar_documents(
            test_embedding.tolist(), 
            limit=3
        )
        print(f"🔍 Tìm thấy {len(results)} documents trong collection")
        
        if results:
            print("📄 Top documents:")
            for i, doc in enumerate(results[:3], 1):
                print(f"   {i}. Score: {doc['score']:.3f} - Source: {doc['source']}")
    
    except Exception as e:
        print(f"⚠️  Collection có thể chưa có dữ liệu: {e}")

def example_5_error_handling():
    """
    Ví dụ 5: Xử lý lỗi và edge cases với Gemini
    """
    print("\n" + "=" * 60)
    print("⚠️  VÍ DỤ 5: XỬ LÝ LỖI (GEMINI)")
    print("=" * 60)
    
    system = PDFRAGSystem()
    
    # Test với file không tồn tại
    print("🧪 Test 1: File không tồn tại")
    result = system.add_documents(["nonexistent.pdf"])
    print(f"   Kết quả: {'Thành công' if result else 'Thất bại'} (như mong đợi)")
    
    # Test với query rỗng
    print("\n🧪 Test 2: Query rỗng")
    try:
        result = system.ask_question("")
        print(f"   Kết quả: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"   Lỗi được bắt: {e}")
    
    # Test với query rất dài
    print("\n🧪 Test 3: Query rất dài")
    long_query = "Hãy giải thích chi tiết " * 100 + "vấn đề này?"
    try:
        result = system.ask_question(long_query)
        print(f"   Kết quả: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"   Lỗi được bắt: {e}")

def example_6_custom_configuration():
    """
    Ví dụ 6: Tùy chỉnh cấu hình Gemini
    """
    print("\n" + "=" * 60)
    print("⚙️  VÍ DỤ 6: TÙY CHỈNH CẤU HÌNH GEMINI")
    print("=" * 60)
    
    from config import Config
    
    print("📋 Cấu hình Gemini hiện tại:")
    print(f"   Gemini Model: {Config.GEMINI_MODEL}")
    print(f"   Temperature: {Config.GEMINI_TEMPERATURE}")
    print(f"   Max Output Tokens: {Config.GEMINI_MAX_OUTPUT_TOKENS}")
    print(f"   Embedding Model: {Config.EMBEDDING_MODEL}")
    print(f"   Chunk Size: {Config.CHUNK_SIZE}")
    print(f"   Top K Documents: {Config.TOP_K_DOCUMENTS}")
    print(f"   Similarity Threshold: {Config.SIMILARITY_THRESHOLD}")
    
    # Có thể dynamic thay đổi config
    print(f"\n🔧 Có thể điều chỉnh config runtime:")
    print(f"   Config.GEMINI_MODEL = 'gemini-1.5-pro'  # Model chất lượng cao hơn")
    print(f"   Config.GEMINI_TEMPERATURE = 0.2  # Creative hơn")
    print(f"   Config.GEMINI_MAX_OUTPUT_TOKENS = 4096  # Output dài hơn")
    print(f"   Config.TOP_K_DOCUMENTS = 10  # Lấy nhiều docs hơn")
    print(f"   Config.SIMILARITY_THRESHOLD = 0.6  # Threshold thấp hơn")

def example_7_gemini_specific():
    """
    Ví dụ 7: Các tính năng đặc biệt của Gemini
    """
    print("\n" + "=" * 60)
    print("🌟 VÍ DỤ 7: TÍNH NĂNG ĐẶC BIỆT GEMINI")
    print("=" * 60)
    
    print("🤖 Ưu điểm của Google Gemini:")
    print("   ✅ Miễn phí với quota hào phóng")
    print("   ✅ Hỗ trợ tiếng Việt tự nhiên")
    print("   ✅ Context window lớn (tới 2M tokens)")
    print("   ✅ Tốc độ response nhanh")
    print("   ✅ Không cần thẻ tín dụng để bắt đầu")
    
    print(f"\n📊 Models available:")
    models = [
        ("gemini-1.5-flash", "Nhanh, phù hợp hầu hết tác vụ"),
        ("gemini-1.5-pro", "Chất lượng cao, phức tạp hơn"),
        ("gemini-1.0-pro", "Phiên bản cũ, ổn định")
    ]
    
    for model, desc in models:
        print(f"   🔹 {model}: {desc}")
    
    print(f"\n💡 Tips sử dụng Gemini hiệu quả:")
    print("   • Sử dụng prompt rõ ràng, cụ thể")
    print("   • Gemini 1.5 Flash cho tốc độ")
    print("   • Gemini 1.5 Pro cho chất lượng")
    print("   • Điều chỉnh temperature cho creativity")
    print("   • Tận dụng context window lớn")

def main():
    """
    Chạy tất cả ví dụ với Google Gemini
    """
    print("🚀 CHẠY TẤT CẢ VÍ DỤ SỬ DỤNG PDF RAG SYSTEM (GOOGLE GEMINI)")
    
    examples = [
        example_1_basic_usage,
        example_2_workflow_direct,
        example_3_batch_questions,
        example_4_collection_management,
        example_5_error_handling,
        example_6_custom_configuration,
        example_7_gemini_specific
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ Lỗi trong {example_func.__name__}: {e}")
        
        input("\n⏯️  Nhấn Enter để tiếp tục...")
    
    print("\n✅ Hoàn thành tất cả ví dụ với Google Gemini!")

if __name__ == "__main__":
    main() 