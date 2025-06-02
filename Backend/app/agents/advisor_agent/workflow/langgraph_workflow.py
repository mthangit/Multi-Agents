from typing import Dict, List, Any, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import os

from utils.pdf_processor import PDFProcessor
from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager
from agents.rag_agent import RAGAgent

class WorkflowState(TypedDict):
    """
    Định nghĩa state cho LangGraph workflow
    """
    # Input
    query: str
    pdf_paths: List[str]
    
    # Processing state
    documents: List[Dict]
    query_embedding: List[float]
    retrieved_documents: List[Dict]
    
    # Output
    answer: str
    sources: List[str]
    relevant_docs_count: int
    error: str
    
    # Status
    step: str
    messages: List[BaseMessage]

class PDFRAGWorkflow:
    def __init__(self):
        """
        Khởi tạo LangGraph Workflow cho hệ thống PDF Q&A
        """
        print("🚀 Đang khởi tạo PDF RAG Workflow...")
        
        # Khởi tạo các components
        self.pdf_processor = PDFProcessor()
        self.embedding_manager = EmbeddingManager()
        self.qdrant_manager = QdrantManager()
        self.rag_agent = RAGAgent()
        
        # Tạo workflow graph
        self.workflow = self._create_workflow()
        
        print("✅ PDF RAG Workflow đã sẵn sàng!")
    
    def _create_workflow(self) -> StateGraph:
        """
        Tạo LangGraph workflow với các nodes và edges
        """
        workflow = StateGraph(WorkflowState)
        
        # Thêm các nodes
        workflow.add_node("check_documents", self.check_documents_node)
        workflow.add_node("process_pdfs", self.process_pdfs_node)
        workflow.add_node("create_embeddings", self.create_embeddings_node)
        workflow.add_node("store_in_qdrant", self.store_in_qdrant_node)
        workflow.add_node("process_query", self.process_query_node)
        workflow.add_node("retrieve_documents", self.retrieve_documents_node)
        workflow.add_node("generate_answer", self.generate_answer_node)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Định nghĩa entry point
        workflow.set_entry_point("check_documents")
        
        # Định nghĩa conditional edges
        workflow.add_conditional_edges(
            "check_documents",
            self.should_process_pdfs,
            {
                "process": "process_pdfs",
                "query": "process_query"
            }
        )
        
        # Định nghĩa linear edges cho document processing
        workflow.add_edge("process_pdfs", "create_embeddings")
        workflow.add_edge("create_embeddings", "store_in_qdrant")
        workflow.add_edge("store_in_qdrant", "process_query")
        
        # Định nghĩa edges cho query processing
        workflow.add_edge("process_query", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def check_documents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node kiểm tra xem có cần xử lý PDFs không
        """
        try:
            state["step"] = "Kiểm tra tài liệu"
            print("📋 Kiểm tra trạng thái collection và PDFs...")
            
            # Kiểm tra collection info
            collection_info = self.qdrant_manager.get_collection_info()
            
            if "error" in collection_info:
                # Collection chưa tồn tại, cần xử lý PDFs
                state["step"] = "Cần xử lý PDFs"
                print("📁 Collection chưa tồn tại, sẽ xử lý PDFs...")
            elif collection_info.get("vectors_count", 0) == 0:
                # Collection tồn tại nhưng rỗng
                state["step"] = "Cần xử lý PDFs"
                print("📁 Collection rỗng, sẽ xử lý PDFs...")
            else:
                # Collection đã có dữ liệu
                state["step"] = "Chỉ xử lý query"
                print(f"✅ Collection đã có {collection_info['vectors_count']} vectors")
            
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi kiểm tra documents: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def should_process_pdfs(self, state: WorkflowState) -> str:
        """
        Conditional function quyết định có cần xử lý PDFs không
        """
        if state["step"] == "Cần xử lý PDFs":
            return "process"
        else:
            return "query"
    
    def process_pdfs_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 2.1: Tải và Phân Tách Tài Liệu PDF
        """
        try:
            state["step"] = "Xử lý PDFs"
            print("📄 Bắt đầu xử lý PDFs...")
            
            all_documents = []
            
            if not state.get("pdf_paths"):
                raise Exception("Không có đường dẫn PDF nào được cung cấp")
            
            for pdf_path in state["pdf_paths"]:
                if not os.path.exists(pdf_path):
                    print(f"⚠️ File không tồn tại: {pdf_path}")
                    continue
                
                documents = self.pdf_processor.process_pdf(pdf_path)
                all_documents.extend(documents)
            
            if not all_documents:
                raise Exception("Không thể xử lý bất kỳ PDF nào")
            
            state["documents"] = all_documents
            print(f"✅ Đã xử lý {len(all_documents)} chunks từ {len(state['pdf_paths'])} files")
            
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi xử lý PDFs: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def create_embeddings_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 2.2: Tạo Vector Embedding cho Tài Liệu
        """
        try:
            state["step"] = "Tạo embeddings"
            print("🧮 Tạo embeddings cho documents...")
            
            documents_with_embeddings = self.embedding_manager.embed_documents(state["documents"])
            state["documents"] = documents_with_embeddings
            
            print("✅ Đã tạo embeddings thành công")
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi tạo embeddings: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def store_in_qdrant_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 2.3: Lưu Trữ Vector vào Qdrant
        """
        try:
            state["step"] = "Lưu vào Qdrant"
            print("💾 Lưu documents vào Qdrant...")
            
            # Tạo collection nếu chưa có
            vector_size = self.embedding_manager.embedding_dimension
            self.qdrant_manager.create_collection(vector_size)
            
            # Thêm documents vào collection
            self.qdrant_manager.add_documents(state["documents"])
            
            print("✅ Đã lưu documents vào Qdrant thành công")
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi lưu vào Qdrant: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def process_query_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 3.1: Tiếp Nhận và Xử Lý Câu Hỏi Người Dùng
        """
        try:
            state["step"] = "Xử lý câu hỏi"
            print(f"❓ Xử lý câu hỏi: {state['query']}")
            
            # Tạo embedding cho query
            query_embedding = self.embedding_manager.embed_query(state["query"])
            state["query_embedding"] = query_embedding.tolist()
            
            print("✅ Đã tạo embedding cho câu hỏi")
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi xử lý câu hỏi: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def retrieve_documents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 3.2: Truy Xuất Thông Tin Liên Quan từ Qdrant
        """
        try:
            state["step"] = "Truy xuất documents"
            print("🔍 Tìm kiếm documents liên quan...")
            
            # Tìm kiếm trong Qdrant
            retrieved_docs = self.qdrant_manager.search_similar_documents(
                state["query_embedding"]
            )
            
            state["retrieved_documents"] = retrieved_docs
            
            print(f"✅ Đã tìm thấy {len(retrieved_docs)} documents liên quan")
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi truy xuất documents: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def generate_answer_node(self, state: WorkflowState) -> WorkflowState:
        """
        Bước 3.3-3.6: Đánh giá, Tổng hợp và Tạo câu trả lời
        """
        try:
            state["step"] = "Tạo câu trả lời"
            print("🤖 Tạo câu trả lời với RAG Agent...")
            
            # Sử dụng RAG Agent để xử lý
            result = self.rag_agent.process_query(
                state["query"], 
                state["retrieved_documents"]
            )
            
            # Cập nhật state với kết quả
            state["answer"] = result["answer"]
            state["sources"] = result["sources"]
            state["relevant_docs_count"] = result["relevant_documents_count"]
            state["step"] = "Hoàn thành"
            
            print("✅ Đã tạo câu trả lời thành công")
            return state
            
        except Exception as e:
            state["error"] = f"Lỗi khi tạo câu trả lời: {str(e)}"
            state["step"] = "Lỗi"
            return state
    
    def handle_error_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node xử lý lỗi
        """
        print(f"❌ Xử lý lỗi: {state.get('error', 'Lỗi không xác định')}")
        state["answer"] = f"Xin lỗi, đã xảy ra lỗi: {state.get('error', 'Lỗi không xác định')}"
        return state
    
    def run_document_processing(self, pdf_paths: List[str]) -> Dict:
        """
        Chạy workflow cho việc xử lý documents (Giai đoạn 1)
        """
        print("🔄 Bắt đầu xử lý documents...")
        
        initial_state = {
            "pdf_paths": pdf_paths,
            "query": "",
            "step": "Bắt đầu",
            "messages": []
        }
        
        # Chỉ chạy các steps xử lý documents
        result = self.workflow.invoke(initial_state)
        
        return {
            "status": "success" if result.get("step") != "Lỗi" else "error",
            "step": result.get("step"),
            "error": result.get("error"),
            "documents_processed": len(result.get("documents", []))
        }
    
    def run_query(self, query: str, pdf_paths: List[str] = None) -> Dict:
        """
        Chạy workflow cho việc trả lời câu hỏi (Giai đoạn 2)
        """
        print(f"🔄 Bắt đầu xử lý câu hỏi: {query}")
        
        initial_state = {
            "query": query,
            "pdf_paths": pdf_paths or [],
            "step": "Bắt đầu",
            "messages": []
        }
        
        # Chạy full workflow
        result = self.workflow.invoke(initial_state)
        
        return {
            "query": query,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "relevant_docs_count": result.get("relevant_docs_count", 0),
            "status": "success" if result.get("step") != "Lỗi" else "error",
            "error": result.get("error"),
            "step": result.get("step")
        } 