#!/usr/bin/env python3
"""
Script nạp dữ liệu PDF vào Vector Database
Chỉ chạy một lần hoặc khi có cập nhật tài liệu
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List
import glob

from utils.pdf_processor import PDFProcessor
from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager
from config import Config

class DataIngestionPipeline:
    def __init__(self):
        """
        Khởi tạo pipeline nạp dữ liệu
        """
        print("🔧 Khởi tạo Data Ingestion Pipeline...")
        
        # Khởi tạo các components
        self.pdf_processor = PDFProcessor()
        self.embedding_manager = EmbeddingManager()
        self.qdrant_manager = QdrantManager()
        
        print("✅ Pipeline đã sẵn sàng!")
    
    def check_prerequisites(self):
        """
        Kiểm tra các điều kiện tiên quyết
        """
        print("🔍 Kiểm tra điều kiện tiên quyết...")
        
        # Kiểm tra Qdrant connection
        try:
            collection_info = self.qdrant_manager.get_collection_info()
            if "error" not in collection_info:
                print(f"✅ Kết nối Qdrant thành công")
                print(f"   Collection hiện tại: {collection_info.get('vectors_count', 0)} vectors")
            else:
                print(f"⚠️  Collection chưa tồn tại, sẽ tạo mới")
        except Exception as e:
            print(f"❌ Lỗi kết nối Qdrant: {e}")
            return False
        
        # Kiểm tra embedding model
        try:
            test_embedding = self.embedding_manager.embed_query("test")
            print(f"✅ Embedding model hoạt động (dimension: {len(test_embedding)})")
        except Exception as e:
            print(f"❌ Lỗi embedding model: {e}")
            return False
        
        return True
    
    def find_pdf_files(self, paths: List[str]) -> List[str]:
        """
        Tìm tất cả file PDF từ paths (có thể là file hoặc folder)
        """
        pdf_files = []
        
        for path in paths:
            path = Path(path)
            
            if path.is_file() and path.suffix.lower() == '.pdf':
                pdf_files.append(str(path))
                print(f"✅ Tìm thấy file: {path}")
            elif path.is_dir():
                # Tìm tất cả PDF trong folder
                pattern = str(path / "**" / "*.pdf")
                found_files = glob.glob(pattern, recursive=True)
                if found_files:
                    pdf_files.extend(found_files)
                    print(f"✅ Tìm thấy {len(found_files)} PDF files trong {path}")
                    for f in found_files:
                        print(f"   - {f}")
                else:
                    print(f"⚠️  Không tìm thấy PDF nào trong: {path}")
            else:
                print(f"⚠️  Đường dẫn không tồn tại: {path}")
        
        return pdf_files
    
    def check_data_folder(self) -> bool:
        """
        Kiểm tra thư mục data có tồn tại và có PDF không
        """
        data_folder = Path("data")
        
        if not data_folder.exists():
            print("❌ Thư mục 'data' không tồn tại!")
            print("💡 Tạo thư mục data và đặt file PDF vào đó:")
            print("   mkdir data")
            print("   cp your_files.pdf data/")
            return False
        
        pdf_files = self.find_pdf_files(["data"])
        
        if not pdf_files:
            print("❌ Không tìm thấy file PDF nào trong thư mục 'data'!")
            print("💡 Đặt file PDF vào thư mục data:")
            print("   cp your_files.pdf data/")
            print("   # Hoặc tạo subfolder:")
            print("   mkdir data/documents && cp *.pdf data/documents/")
            return False
        
        return True
    
    def process_pdfs(self, pdf_files: List[str], force_reprocess: bool = False) -> List[dict]:
        """
        Xử lý danh sách PDF files
        """
        if not pdf_files:
            print("❌ Không có file PDF nào để xử lý!")
            return []
        
        print(f"📄 Bắt đầu xử lý {len(pdf_files)} PDF files...")
        
        all_documents = []
        success_count = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                print(f"\n📖 [{i}/{len(pdf_files)}] Xử lý: {pdf_file}")
                
                # Kiểm tra file tồn tại
                if not os.path.exists(pdf_file):
                    print(f"   ❌ File không tồn tại: {pdf_file}")
                    continue
                
                # Xử lý PDF
                documents = self.pdf_processor.process_pdf(pdf_file)
                
                if documents:
                    all_documents.extend(documents)
                    success_count += 1
                    print(f"   ✅ Tạo được {len(documents)} chunks")
                else:
                    print(f"   ⚠️  Không tạo được chunk nào")
                    
            except Exception as e:
                print(f"   ❌ Lỗi xử lý {pdf_file}: {e}")
                continue
        
        print(f"\n📊 Kết quả xử lý:")
        print(f"   - Thành công: {success_count}/{len(pdf_files)} files")
        print(f"   - Tổng chunks: {len(all_documents)}")
        
        return all_documents
    
    def create_embeddings(self, documents: List[dict]) -> List[dict]:
        """
        Tạo embeddings cho documents
        """
        if not documents:
            return []
        
        print(f"\n🧮 Tạo embeddings cho {len(documents)} documents...")
        
        try:
            documents_with_embeddings = self.embedding_manager.embed_documents(documents)
            print(f"✅ Đã tạo embeddings thành công")
            return documents_with_embeddings
        except Exception as e:
            print(f"❌ Lỗi tạo embeddings: {e}")
            return []
    
    def store_in_vector_db(self, documents: List[dict], clear_existing: bool = False) -> bool:
        """
        Lưu documents vào vector database
        """
        if not documents:
            print("❌ Không có documents để lưu!")
            return False
        
        print(f"\n💾 Lưu {len(documents)} documents vào Qdrant...")
        
        try:
            # Xóa collection cũ nếu cần
            if clear_existing:
                print("🗑️  Xóa collection cũ...")
                self.qdrant_manager.delete_collection()
            
            # Tạo collection
            vector_size = self.embedding_manager.embedding_dimension
            self.qdrant_manager.create_collection(vector_size)
            
            # Lưu documents
            self.qdrant_manager.add_documents(documents)
            
            # Kiểm tra kết quả
            collection_info = self.qdrant_manager.get_collection_info()
            print(f"✅ Đã lưu thành công!")
            print(f"   Collection hiện có: {collection_info.get('vectors_count', 0)} vectors")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi lưu vào Qdrant: {e}")
            return False
    
    def run_ingestion(self, pdf_paths: List[str] = None, clear_existing: bool = False, force_reprocess: bool = False):
        """
        Chạy toàn bộ pipeline ingestion
        """
        print("🚀 BẮT ĐẦU DATA INGESTION PIPELINE")
        print("=" * 60)
        
        # Bước 1: Kiểm tra prerequisites
        if not self.check_prerequisites():
            print("❌ Không đáp ứng điều kiện tiên quyết!")
            return False
        
        # Bước 2: Xử lý paths
        if pdf_paths is None:
            # Mặc định sử dụng thư mục data
            if not self.check_data_folder():
                return False
            pdf_paths = ["data"]
        
        # Bước 3: Tìm PDF files
        print(f"\n📁 Tìm PDF files từ: {pdf_paths}")
        pdf_files = self.find_pdf_files(pdf_paths)
        
        if not pdf_files:
            print("❌ Không tìm thấy PDF files nào!")
            return False
        
        print(f"\n✅ Sẽ xử lý {len(pdf_files)} PDF files")
        
        # Bước 4: Xử lý PDFs
        documents = self.process_pdfs(pdf_files, force_reprocess)
        
        if not documents:
            print("❌ Không có documents để xử lý!")
            return False
        
        # Bước 5: Tạo embeddings
        documents_with_embeddings = self.create_embeddings(documents)
        
        if not documents_with_embeddings:
            print("❌ Không tạo được embeddings!")
            return False
        
        # Bước 6: Lưu vào vector DB
        success = self.store_in_vector_db(documents_with_embeddings, clear_existing)
        
        if success:
            print(f"\n🎉 HOÀN THÀNH DATA INGESTION!")
            print(f"📊 Thống kê:")
            print(f"   - PDF files: {len(pdf_files)}")
            print(f"   - Documents: {len(documents_with_embeddings)}")
            print(f"   - Collection: {Config.COLLECTION_NAME}")
            print(f"\n💡 Bây giờ có thể sử dụng chatbot:")
            print(f"   python main.py demo")
            return True
        else:
            print(f"\n❌ DATA INGESTION THẤT BẠI!")
            return False

def main():
    """
    Main function với argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Data Ingestion Pipeline cho PDF RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python ingest_data.py                    # Nạp tất cả PDF từ thư mục 'data'
  python ingest_data.py file.pdf          # Nạp file cụ thể
  python ingest_data.py folder/           # Nạp từ folder cụ thể
  python ingest_data.py --clear           # Xóa collection cũ và nạp từ 'data'
  python ingest_data.py --check           # Kiểm tra hệ thống
        """
    )
    
    parser.add_argument(
        "paths", 
        nargs='*',  # 0 hoặc nhiều arguments
        help="Đường dẫn đến PDF files hoặc folders (mặc định: thư mục 'data')"
    )
    
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Xóa collection cũ trước khi thêm dữ liệu mới"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force reprocess tất cả PDFs"
    )
    
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Chỉ kiểm tra prerequisites và exit"
    )
    
    args = parser.parse_args()
    
    # Khởi tạo pipeline
    pipeline = DataIngestionPipeline()
    
    # Nếu chỉ check
    if args.check:
        success = pipeline.check_prerequisites()
        if success:
            pipeline.check_data_folder()
        collection_info = pipeline.qdrant_manager.get_collection_info()
        print(f"\n📊 Trạng thái hiện tại:")
        print(f"   Collection: {Config.COLLECTION_NAME}")
        print(f"   Vectors: {collection_info.get('vectors_count', 0)}")
        sys.exit(0 if success else 1)
    
    # Xử lý paths - nếu không có paths thì dùng thư mục data mặc định
    pdf_paths = args.paths if args.paths else None
    
    # Chạy ingestion
    success = pipeline.run_ingestion(
        pdf_paths=pdf_paths,
        clear_existing=args.clear,
        force_reprocess=args.force
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 