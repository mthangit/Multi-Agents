#!/usr/bin/env python3
"""
Chatbot Class cho PDF RAG System
Xử lý queries từ user dựa trên dữ liệu đã được nạp vào vector database
"""

from typing import Dict, List, Optional
from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager
from agents.rag_agent import RAGAgent
from config import Config

class PDFChatbot:
    def __init__(self):
        """
        Khởi tạo Chatbot với các components cần thiết cho query processing
        """
        print("🤖 Khởi tạo PDF Chatbot...")
        
        # Chỉ khởi tạo components cần thiết cho chat
        self.embedding_manager = EmbeddingManager()
        self.qdrant_manager = QdrantManager()
        self.rag_agent = RAGAgent()
        
        # Kiểm tra kết nối và dữ liệu
        self._check_readiness()
        
        print("✅ Chatbot đã sẵn sàng!")
    
    def _check_readiness(self):
        """
        Kiểm tra xem chatbot có sẵn sàng xử lý queries không
        """
        try:
            # Kiểm tra collection có dữ liệu không
            collection_info = self.qdrant_manager.get_collection_info()
            
            if "error" in collection_info:
                raise Exception(f"Collection không tồn tại: {collection_info['error']}")
            
            vector_count = collection_info.get('vectors_count', 0)
            if vector_count == 0:
                raise Exception("Collection rỗng, cần chạy data ingestion trước")
            
            print(f"📊 Collection ready: {vector_count} vectors")
            
        except Exception as e:
            print(f"⚠️  Cảnh báo: {e}")
            print("💡 Hãy chạy script ingest_data.py trước khi sử dụng chatbot")
    
    def invoke(self, query: str, **kwargs) -> Dict:
        """
        Method chính để xử lý một câu hỏi từ user
        
        Args:
            query: Câu hỏi của user
            **kwargs: Các tham số tùy chọn
                - top_k: Số documents tối đa để retrieve (default từ config)
                - similarity_threshold: Ngưỡng similarity (default từ config)
                - verbose: In chi tiết quá trình xử lý
        
        Returns:
            Dict chứa kết quả:
            {
                "query": str,
                "answer": str,
                "sources": List[str],
                "relevant_docs_count": int,
                "total_retrieved_count": int,
                "status": str,
                "error": str (nếu có),
                "metadata": Dict (thông tin bổ sung)
            }
        """
        if not query or not query.strip():
            return {
                "query": query,
                "answer": "Xin lỗi, bạn chưa đặt câu hỏi gì.",
                "sources": [],
                "relevant_docs_count": 0,
                "total_retrieved_count": 0,
                "status": "error",
                "error": "Query rỗng",
                "metadata": {}
            }
        
        verbose = kwargs.get('verbose', False)
        
        try:
            if verbose:
                print(f"❓ Đang xử lý: {query}")
            
            # Bước 1: Tạo embedding cho query
            query_embedding = self._create_query_embedding(query, verbose)
            
            # Bước 2: Retrieve documents từ vector DB
            retrieved_docs = self._retrieve_documents(
                query_embedding, 
                top_k=kwargs.get('top_k'),
                similarity_threshold=kwargs.get('similarity_threshold'),
                verbose=verbose
            )
            
            # Bước 3: Xử lý với RAG Agent
            result = self._process_with_rag_agent(query, retrieved_docs, verbose)
            
            if verbose:
                print(f"✅ Hoàn thành xử lý query")
            
            return result
            
        except Exception as e:
            error_msg = f"Lỗi khi xử lý query: {str(e)}"
            if verbose:
                print(f"❌ {error_msg}")
            
            return {
                "query": query,
                "answer": f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: {error_msg}",
                "sources": [],
                "relevant_docs_count": 0,
                "total_retrieved_count": 0,
                "status": "error",
                "error": error_msg,
                "metadata": {}
            }
    
    def _create_query_embedding(self, query: str, verbose: bool = False) -> List[float]:
        """
        Tạo embedding cho query
        """
        if verbose:
            print("🧮 Tạo embedding cho query...")
        
        query_embedding = self.embedding_manager.embed_query(query)
        return query_embedding.tolist()
    
    def _retrieve_documents(self, query_embedding: List[float], top_k: Optional[int] = None, 
                           similarity_threshold: Optional[float] = None, verbose: bool = False) -> List[Dict]:
        """
        Retrieve documents từ vector database
        """
        if verbose:
            print("🔍 Tìm kiếm documents liên quan...")
        
        # Sử dụng config mặc định nếu không được cung cấp
        actual_top_k = top_k or Config.TOP_K_DOCUMENTS
        actual_threshold = similarity_threshold or Config.SIMILARITY_THRESHOLD
        
        # Temporarily override config nếu cần
        original_top_k = Config.TOP_K_DOCUMENTS
        original_threshold = Config.SIMILARITY_THRESHOLD
        
        try:
            Config.TOP_K_DOCUMENTS = actual_top_k
            Config.SIMILARITY_THRESHOLD = actual_threshold
            
            retrieved_docs = self.qdrant_manager.search_similar_documents(query_embedding)
            
            if verbose:
                print(f"📄 Tìm thấy {len(retrieved_docs)} documents")
            
            return retrieved_docs
            
        finally:
            # Restore original config
            Config.TOP_K_DOCUMENTS = original_top_k
            Config.SIMILARITY_THRESHOLD = original_threshold
    
    def _process_with_rag_agent(self, query: str, retrieved_docs: List[Dict], verbose: bool = False) -> Dict:
        """
        Xử lý với RAG Agent để tạo câu trả lời
        """
        if verbose:
            print("🤖 Tạo câu trả lời với RAG Agent...")
        
        result = self.rag_agent.process_query(query, retrieved_docs)
        
        # Thêm metadata
        result["status"] = "success"
        result["metadata"] = {
            "embedding_model": Config.EMBEDDING_MODEL,
            "llm_model": Config.GEMINI_MODEL,
            "collection_name": Config.COLLECTION_NAME,
            "similarity_threshold": Config.SIMILARITY_THRESHOLD,
            "top_k": Config.TOP_K_DOCUMENTS
        }
        
        return result
    
    def get_collection_stats(self) -> Dict:
        """
        Lấy thống kê về collection hiện tại
        """
        try:
            collection_info = self.qdrant_manager.get_collection_info()
            return {
                "status": "success",
                "collection_name": Config.COLLECTION_NAME,
                "vectors_count": collection_info.get('vectors_count', 0),
                "indexed_vectors_count": collection_info.get('indexed_vectors_count', 0),
                "collection_status": collection_info.get('status', 'unknown')
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def health_check(self) -> Dict:
        """
        Kiểm tra sức khỏe của chatbot
        """
        try:
            # Test embedding
            test_embedding = self.embedding_manager.embed_query("test")
            embedding_ok = len(test_embedding) > 0
            
            # Test Qdrant
            collection_info = self.qdrant_manager.get_collection_info()
            qdrant_ok = "error" not in collection_info
            
            # Test RAG Agent (lightweight test)
            rag_ok = self.rag_agent is not None
            
            overall_status = embedding_ok and qdrant_ok and rag_ok
            
            return {
                "status": "healthy" if overall_status else "unhealthy",
                "components": {
                    "embedding_manager": "ok" if embedding_ok else "error",
                    "qdrant_manager": "ok" if qdrant_ok else "error", 
                    "rag_agent": "ok" if rag_ok else "error"
                },
                "collection_vectors": collection_info.get('vectors_count', 0) if qdrant_ok else 0,
                "embedding_dimension": len(test_embedding) if embedding_ok else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def batch_invoke(self, queries: List[str], **kwargs) -> List[Dict]:
        """
        Xử lý nhiều queries cùng lúc
        """
        verbose = kwargs.get('verbose', False)
        
        if verbose:
            print(f"📝 Xử lý batch {len(queries)} queries...")
        
        results = []
        for i, query in enumerate(queries, 1):
            if verbose:
                print(f"\n[{i}/{len(queries)}] Processing: {query[:50]}...")
            
            result = self.invoke(query, verbose=False, **kwargs)
            results.append(result)
        
        if verbose:
            print(f"✅ Hoàn thành batch processing")
        
        return results

# Convenience function để tạo chatbot instance
def create_chatbot() -> PDFChatbot:
    """
    Factory function để tạo chatbot instance
    """
    return PDFChatbot()

# Singleton instance (tùy chọn)
_chatbot_instance = None

def get_chatbot() -> PDFChatbot:
    """
    Lấy singleton instance của chatbot
    """
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = PDFChatbot()
    return _chatbot_instance 