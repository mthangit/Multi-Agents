from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
import uuid
from config import Config

class QdrantManager:
    def __init__(self):
        """
        Bước 2.3: Lưu Trữ Vector vào Qdrant (Indexing in Qdrant)
        Khởi tạo kết nối với Qdrant
        """
        print(f"Đang kết nối với Qdrant tại: {Config.QDRANT_URL}")
        
        if Config.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=Config.QDRANT_URL,
                api_key=Config.QDRANT_API_KEY
            )
        else:
            self.client = QdrantClient(url=Config.QDRANT_URL)
        
        self.collection_name = Config.COLLECTION_NAME
        print(f"Sử dụng collection: {self.collection_name}")
    
    def create_collection(self, vector_size: int):
        """
        Tạo collection mới trong Qdrant
        """
        try:
            # Kiểm tra xem collection đã tồn tại chưa
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                print(f"Collection '{self.collection_name}' đã tồn tại")
                return
            
            # Tạo collection mới
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Đã tạo collection '{self.collection_name}' thành công")
            
        except Exception as e:
            raise Exception(f"Lỗi khi tạo collection: {str(e)}")
    
    def add_documents(self, documents: List[Dict]):
        """
        Thêm documents vào Qdrant collection
        """
        try:
            points = []
            
            for doc in documents:
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=doc["embedding"],
                    payload={
                        "content": doc["content"],
                        "source": doc["metadata"]["source"],
                        "chunk_id": doc["metadata"]["chunk_id"],
                        "total_chunks": doc["metadata"]["total_chunks"]
                    }
                )
                points.append(point)
            
            # Thêm points vào collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"Đã thêm {len(points)} documents vào Qdrant")
            
        except Exception as e:
            raise Exception(f"Lỗi khi thêm documents vào Qdrant: {str(e)}")
    
    def search_similar_documents(self, query_vector: List[float], limit: int = None) -> List[Dict]:
        """
        Bước 3.2: Truy Xuất Thông Tin Liên Quan từ Qdrant
        Tìm kiếm documents tương tự với query vector
        """
        if limit is None:
            limit = Config.TOP_K_DOCUMENTS
            
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=Config.SIMILARITY_THRESHOLD
            )
            
            # Chuyển đổi kết quả thành format dễ sử dụng
            results = []
            for result in search_results:
                doc = {
                    "content": result.payload["content"],
                    "source": result.payload["source"],
                    "chunk_id": result.payload["chunk_id"],
                    "score": result.score,
                    "id": result.id
                }
                results.append(doc)
            
            print(f"Tìm thấy {len(results)} documents liên quan")
            return results
            
        except Exception as e:
            raise Exception(f"Lỗi khi tìm kiếm trong Qdrant: {str(e)}")
    
    def get_collection_info(self) -> Dict:
        """
        Lấy thông tin về collection
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status
            }
        except Exception as e:
            return {"error": f"Lỗi khi lấy thông tin collection: {str(e)}"}
    
    def delete_collection(self):
        """
        Xóa collection
        """
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Đã xóa collection '{self.collection_name}'")
        except Exception as e:
            print(f"Lỗi khi xóa collection: {str(e)}") 