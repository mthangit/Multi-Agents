from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np
from config import Config

class EmbeddingManager:
    def __init__(self):
        """
        Bước 2.2: Tạo Vector Embedding cho Tài Liệu (Document Embedding)
        Khởi tạo mô hình embedding
        """
        print(f"Đang tải mô hình embedding: {Config.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        print(f"Kích thước vector embedding: {self.embedding_dimension}")
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Tạo vector embeddings cho danh sách văn bản
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            raise Exception(f"Lỗi khi tạo embeddings: {str(e)}")
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """
        Tạo vector embedding cho một văn bản đơn lẻ
        """
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)
            return embedding[0]
        except Exception as e:
            raise Exception(f"Lỗi khi tạo embedding cho text: {str(e)}")
    
    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Tạo embeddings cho danh sách documents và gắn vào metadata
        """
        print(f"Đang tạo embeddings cho {len(documents)} documents...")
        
        # Lấy nội dung text từ documents
        texts = [doc["content"] for doc in documents]
        
        # Tạo embeddings cho tất cả texts
        embeddings = self.create_embeddings(texts)
        
        # Gắn embedding vào mỗi document
        for i, doc in enumerate(documents):
            doc["embedding"] = embeddings[i].tolist()
        
        print("Hoàn thành tạo embeddings!")
        return documents
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Bước 3.1: Tiếp Nhận và Xử Lý Câu Hỏi Người Dùng
        Tạo embedding cho câu hỏi của người dùng
        """
        print(f"Đang tạo embedding cho câu hỏi: {query}")
        return self.create_single_embedding(query) 