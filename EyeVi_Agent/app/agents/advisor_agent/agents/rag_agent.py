from typing import List, Dict, Optional, Any, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from config import Config, EYEWEAR_KEYWORDS
import re
import json
from datetime import datetime
from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager

# Định nghĩa State cho LangGraph
class RAGState(TypedDict):
    """State cho RAG workflow với LangGraph"""
    # Input
    query: str
    user_context: Dict[str, Any]
    
    # Processing
    intent_info: Dict[str, Any]
    query_embedding: Optional[List[float]]
    retrieved_documents: List[Dict]
    relevant_documents: List[Dict]
    context: str
    
    # Output
    answer: str
    sources: List[str]
    confidence_score: float
    
    # Metadata
    messages: List[BaseMessage]
    step: str
    processing_time: float
    status: str
    error: Optional[str]

class RAGAgent:
    def __init__(self):
        """
        Khởi tạo RAG Agent với LangGraph workflow và streaming support
        """
        print(f"🤖 Đang khởi tạo RAG Agent với LangGraph cho domain: {Config.DOMAIN}")
        print(f"🤖 Đang khởi tạo Gemini model: {Config.GEMINI_MODEL}")
        
        self.llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            temperature=Config.GEMINI_TEMPERATURE,
            max_output_tokens=Config.GEMINI_MAX_OUTPUT_TOKENS,
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        # Khởi tạo các managers (sẽ được inject từ workflow)
        self.embedding_manager = None
        self.qdrant_manager = None
        
        # Tạo LangGraph workflow
        self.workflow = self._create_workflow()
        self.compiled_workflow = self.workflow.compile()
        
        print("✅ RAG Agent với LangGraph đã sẵn sàng!")
    
    def set_managers(self, embedding_manager: EmbeddingManager, qdrant_manager: QdrantManager):
        """Inject các managers cần thiết với validation"""
        if embedding_manager is None:
            raise ValueError("Embedding manager không được để trống")
        if qdrant_manager is None:
            raise ValueError("Qdrant manager không được để trống")
            
        self.embedding_manager = embedding_manager
        self.qdrant_manager = qdrant_manager
        
        print("✅ Đã inject managers vào RAG Agent thành công")
        print(f"   - Embedding model: {getattr(embedding_manager, 'model', 'unknown')}")
        print(f"   - Qdrant collection: {getattr(qdrant_manager, 'collection_name', 'unknown')}")
    
    def _create_workflow(self) -> StateGraph:
        """Tạo LangGraph workflow cho RAG process"""
        workflow = StateGraph(RAGState)
        
        # Thêm các nodes
        workflow.add_node("detect_intent", self.detect_intent_node)
        workflow.add_node("retrieve_documents", self.retrieve_documents_node)
        workflow.add_node("filter_documents", self.filter_documents_node)
        workflow.add_node("aggregate_context", self.aggregate_context_node)
        workflow.add_node("generate_answer", self.generate_answer_node)
        workflow.add_node("post_process", self.post_process_node)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Định nghĩa entry point
        workflow.set_entry_point("detect_intent")
        
        # Định nghĩa edges
        workflow.add_edge("detect_intent", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "filter_documents")
        workflow.add_edge("filter_documents", "aggregate_context")
        workflow.add_edge("aggregate_context", "generate_answer")
        workflow.add_edge("generate_answer", "post_process")
        workflow.add_edge("post_process", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def detect_intent_node(self, state: RAGState) -> RAGState:
        """Node phân tích intent của câu hỏi"""
        try:
            state["step"] = "Phân tích intent"
            state["messages"] = add_messages(state.get("messages", []), 
                                           [HumanMessage(content=f"Đang phân tích intent cho: {state['query']}")])
            
            intent_info = self.detect_query_intent(state["query"])
            state["intent_info"] = intent_info
            state["status"] = "intent_detected"
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi phân tích intent: {str(e)}"
            state["status"] = "error"
            return state
    
    def retrieve_documents_node(self, state: RAGState) -> RAGState:
        """Node truy xuất documents từ vector store"""
        try:
            state["step"] = "Truy xuất documents"
            state["messages"] = add_messages(state.get("messages", []), 
                                           [HumanMessage(content="Đang tìm kiếm thông tin liên quan...")])
            
            if not self.embedding_manager or not self.qdrant_manager:
                raise Exception("Embedding manager hoặc Qdrant manager chưa được thiết lập")
            
            # Tạo embedding cho query
            query_embedding = self.embedding_manager.embed_query(state["query"])
            state["query_embedding"] = query_embedding.tolist()  # Convert numpy array to list
            
            # Tìm kiếm documents - Sửa method name và convert data type
            retrieved_docs = self.qdrant_manager.search_similar_documents(
                query_embedding.tolist(),  # Convert numpy array to list for Qdrant
                limit=Config.TOP_K_DOCUMENTS
            )
            state["retrieved_documents"] = retrieved_docs
            state["status"] = "documents_retrieved"
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi truy xuất documents: {str(e)}"
            state["status"] = "error"
            return state
    
    def filter_documents_node(self, state: RAGState) -> RAGState:
        """Node lọc và đánh giá documents"""
        try:
            state["step"] = "Lọc documents"
            state["messages"] = add_messages(state.get("messages", []), 
                                           [HumanMessage(content="Đang đánh giá độ liên quan của tài liệu...")])
            
            relevant_docs = self.grade_retrieved_documents(state["query"], state["retrieved_documents"])
            state["relevant_documents"] = relevant_docs
            state["status"] = "documents_filtered"
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi lọc documents: {str(e)}"
            state["status"] = "error"
            return state
    
    def aggregate_context_node(self, state: RAGState) -> RAGState:
        """Node tổng hợp context từ documents"""
        try:
            state["step"] = "Tổng hợp context"
            state["messages"] = add_messages(state.get("messages", []), 
                                           [HumanMessage(content="Đang tổng hợp thông tin...")])
            
            context = self.aggregate_context(state["relevant_documents"])
            enhanced_context = self.enhance_context_with_keywords(context, state["intent_info"])
            
            state["context"] = enhanced_context
            state["sources"] = list(set([doc["source"] for doc in state["relevant_documents"]]))
            state["status"] = "context_aggregated"
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi tổng hợp context: {str(e)}"
            state["status"] = "error"
            return state
    
    def generate_answer_node(self, state: RAGState) -> RAGState:
        """Node tạo câu trả lời với LLM"""
        try:
            state["step"] = "Tạo câu trả lời"
            state["messages"] = add_messages(state.get("messages", []), 
                                           [HumanMessage(content="Đang tạo câu trả lời...")])
            
            # Tạo prompt domain-specific
            prompt = self.create_domain_prompt(state["query"], state["context"], state["intent_info"])
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            state["answer"] = answer
            state["confidence_score"] = 0.8  # Có thể tính toán dựa trên context quality
            state["status"] = "answer_generated"
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi tạo câu trả lời: {str(e)}"
            state["status"] = "error"
            return state
    
    def post_process_node(self, state: RAGState) -> RAGState:
        """Node xử lý hậu kỳ response"""
        try:
            state["step"] = "Hoàn thiện"
            
            # Post-process response
            final_answer = self.post_process_response(state["answer"], state["intent_info"])
            state["answer"] = final_answer
            
            # Thêm AI message vào conversation
            state["messages"] = add_messages(state.get("messages", []), 
                                           [AIMessage(content=final_answer)])
            
            state["status"] = "completed"
            state["processing_time"] = 0.0  # Sẽ được tính ở workflow level
            
            return state
        except Exception as e:
            state["error"] = f"Lỗi xử lý hậu kỳ: {str(e)}"
            state["status"] = "error"
            return state
    
    def handle_error_node(self, state: RAGState) -> RAGState:
        """Node xử lý lỗi"""
        error_message = f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi: {state.get('error', 'Lỗi không xác định')}"
        
        state["answer"] = error_message
        state["messages"] = add_messages(state.get("messages", []), 
                                       [AIMessage(content=error_message)])
        state["status"] = "error_handled"
        
        return state
    
    def invoke(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Invoke synchronous processing
        """
        initial_state: RAGState = {
            "query": query,
            "user_context": user_context or {},
            "intent_info": {},
            "query_embedding": None,
            "retrieved_documents": [],
            "relevant_documents": [],
            "context": "",
            "answer": "",
            "sources": [],
            "confidence_score": 0.0,
            "messages": [],
            "step": "Completed",
            "processing_time": 0.0,
            "status": "completed",
            "error": None
        }
        
        try:
            start_time = datetime.now()
            final_state = self.compiled_workflow.invoke(initial_state)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": final_state.get("answer", ""),
                "sources": final_state.get("sources", []),
                "intent_info": final_state.get("intent_info", {}),
                "relevant_documents_count": len(final_state.get("relevant_documents", [])),
                "total_retrieved_count": len(final_state.get("retrieved_documents", [])),
                "confidence_score": final_state.get("confidence_score", 0.0),
                "processing_time": processing_time,
                "status": final_state.get("status", "unknown")
            }
        except Exception as e:
            return {
                "answer": f"Lỗi xử lý: {str(e)}",
                "sources": [],
                "intent_info": {"query_type": "error"},
                "relevant_documents_count": 0,
                "total_retrieved_count": 0,
                "confidence_score": 0.0,
                "processing_time": 0.0,
                "status": "error"
            }
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Phân tích intent của câu hỏi về mắt kính
        """
        intent_info = {
            "query_type": "general",
            "vision_condition": None,
            "product_interest": None,
            "style_preference": None,
            "technical_level": "basic"
        }
        
        query_lower = query.lower()
        
        # Detect vision conditions
        for condition in EYEWEAR_KEYWORDS["vision_conditions"]:
            if condition.lower() in query_lower:
                intent_info["vision_condition"] = condition
                intent_info["query_type"] = "medical_consultation"
                break
        
        # Detect product interest
        for product in EYEWEAR_KEYWORDS["lens_types"]:
            if product.lower() in query_lower:
                intent_info["product_interest"] = product
                intent_info["query_type"] = "product_recommendation"
                break
        
        # Detect style preference
        for style in EYEWEAR_KEYWORDS["frame_styles"]:
            if style.lower() in query_lower:
                intent_info["style_preference"] = style
                intent_info["query_type"] = "style_consultation"
                break
        
        # Detect technical questions
        technical_terms = ["coating", "lớp phủ", "chỉ số khúc xạ", "độ dày", "UV", "blue light"]
        if any(term in query_lower for term in technical_terms):
            intent_info["technical_level"] = "advanced"
        
        return intent_info
    
    def create_domain_prompt(self, query: str, context: str, intent_info: Dict) -> str:
        """
        Tạo prompt tối ưu cho domain mắt kính
        """
        base_role = """Bạn là chuyên gia tư vấn mắt kính chuyên nghiệp với nhiều năm kinh nghiệm trong lĩnh vực quang học. 
Bạn có kiến thức sâu rộng về:
- Các tật khúc xạ mắt (cận thị, viễn thị, loạn thị, lão thị)
- Các kiến thức sức khoẻ về mắt
- Các loại tròng kính và công nghệ lens
- Phong cách và thiết kế gọng kính
- Vật liệu và công nghệ sản xuất
- Xu hướng thời trang kính mắt"""

        if intent_info["query_type"] == "medical_consultation":
            role_specific = """
Hãy tập trung vào:
- Giải thích rõ ràng tình trạng thị lực
- Đề xuất loại tròng kính phù hợp
- Lưu ý về việc thăm khám mắt định kỳ
- Không thay thế ý kiến bác sĩ chuyên khoa"""

        elif intent_info["query_type"] == "style_consultation":
            role_specific = """
Hãy tập trung vào:
- Phân tích khuôn mặt và phong cách phù hợp
- Xu hướng thời trang mắt kính
- Cách phối hợp với trang phục
- Lời khuyên về màu sắc và chất liệu"""

        else:
            role_specific = """
Hãy cung cấp thông tin toàn diện và thực tế."""

        context_instruction = f"""
Dựa trên thông tin sau từ cơ sở dữ liệu về mắt kính:

{context}

Câu hỏi của khách hàng: {query}
"""

        response_guidelines = """
Hãy trả lời theo cấu trúc:
1. **Phân tích nhu cầu**: Hiểu rõ tình huống của khách hàng
2. **Đề xuất cụ thể**: Gợi ý sản phẩm/giải pháp phù hợp  
3. **Giải thích lý do**: Tại sao đây là lựa chọn tốt
4. **Lưu ý quan trọng**: Điều cần chú ý khi sử dụng
5. **Tư vấn thêm**: Gợi ý về chăm sóc hoặc lựa chọn khác

Lưu ý:
- Sử dụng ngôn ngữ thân thiện, dễ hiểu
- Đưa ra lời khuyên thực tế và có căn cứ
- Nếu cần thăm khám chuyên khoa, hãy khuyên khách hàng đi khám
- Tránh cam kết chữa bệnh hoặc kết quả chắc chắn
"""

        return f"{base_role}\n{role_specific}\n{context_instruction}\n{response_guidelines}"
    
    def enhance_context_with_keywords(self, context: str, intent_info: Dict) -> str:
        """
        Tăng cường context với keywords domain-specific
        """
        enhanced_context = context
        
        # Thêm keywords liên quan dựa trên intent
        if intent_info["vision_condition"]:
            related_keywords = [kw for kw in EYEWEAR_KEYWORDS["vision_conditions"] 
                              if kw != intent_info["vision_condition"]]
            enhanced_context += f"\n\nCác tình trạng liên quan: {', '.join(related_keywords)}"
        
        if intent_info["product_interest"]:
            related_products = [kw for kw in EYEWEAR_KEYWORDS["lens_types"] 
                              if kw != intent_info["product_interest"]]
            enhanced_context += f"\n\nCác loại sản phẩm liên quan: {', '.join(related_products[:3])}"
        
        return enhanced_context
    
    def post_process_response(self, response: str, intent_info: Dict) -> str:
        """
        Xử lý response để phù hợp với domain
        """
        # Thêm disclaimer cho medical advice
        if intent_info["query_type"] == "medical_consultation":
            disclaimer = "\n\n⚠️ **Lưu ý quan trọng**: Thông tin này chỉ mang tính tham khảo. Hãy thăm khám bác sĩ nhãn khoa để được chẩn đoán và tư vấn chính xác."
            if disclaimer not in response:
                response += disclaimer
        
        # Thêm call-to-action cho product recommendations
        if intent_info["query_type"] == "product_recommendation":
            cta = "\n\n💡 **Gợi ý**: Bạn có thể đến cửa hàng để thử trực tiếp và nhận tư vấn chi tiết từ nhân viên chuyên nghiệp."
            if "cửa hàng" not in response.lower():
                response += cta
        
        return response

    def grade_retrieved_documents(self, query: str, documents: List[Dict]) -> List[Dict]:
        """
        Bước 3.3: Đánh Giá và Lọc Kết Quả Truy Xuất
        Đánh giá độ liên quan của documents với câu hỏi
        """
        print("Đang đánh giá độ liên quan của documents...")
        
        relevant_docs = []
        
        for doc in documents:
            # Kiểm tra điểm similarity từ Qdrant
            if doc["score"] >= Config.SIMILARITY_THRESHOLD:
                # Thêm đánh giá LLM nếu cần (tùy chọn)
                grade_prompt = f"""
                Hãy đánh giá xem đoạn văn bản sau có liên quan đến câu hỏi không.
                
                Câu hỏi: {query}
                
                Đoạn văn bản: {doc["content"][:500]}...
                
                Trả lời chỉ "YES" nếu liên quan hoặc "NO" nếu không liên quan.
                """
                
                try:
                    messages = [HumanMessage(content=grade_prompt)]
                    response = self.llm.invoke(messages)
                    grade = response.content.strip().upper()
                    
                    if grade == "YES":
                        relevant_docs.append(doc)
                        print(f"✓ Document từ {doc['source']} - chunk {doc['chunk_id']} được chấp nhận (score: {doc['score']:.3f})")
                    else:
                        print(f"✗ Document từ {doc['source']} - chunk {doc['chunk_id']} bị loại bỏ (không liên quan)")
                        
                except Exception as e:
                    # Nếu lỗi LLM, chỉ dựa vào điểm similarity
                    relevant_docs.append(doc)
                    print(f"⚠ Lỗi đánh giá Gemini, giữ document dựa trên similarity score: {e}")
            else:
                print(f"✗ Document từ {doc['source']} - chunk {doc['chunk_id']} bị loại bỏ (score thấp: {doc['score']:.3f})")
        
        print(f"Đã lọc được {len(relevant_docs)}/{len(documents)} documents liên quan")
        return relevant_docs
    
    def aggregate_context(self, documents: List[Dict]) -> str:
        """
        Bước 3.4: Tổng Hợp Ngữ Cảnh (Context Aggregation)
        Kết hợp nội dung các documents thành context thống nhất
        """
        if not documents:
            return ""
        
        print("Đang tổng hợp ngữ cảnh từ documents...")
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source_info = f"[Nguồn: {doc['source']}, Phần {doc['chunk_id']}]"
            content = f"{source_info}\n{doc['content']}\n"
            context_parts.append(content)
        
        # Sửa formatting để context rõ ràng hơn
        context = "\n" + ("="*50 + "\n").join(context_parts)
        
        print(f"Đã tổng hợp context từ {len(documents)} documents")
        return context
    
    def generate_answer(self, query: str, context: str) -> str:
        """
        Bước 3.5: Tạo Câu Trả Lời với Gemini LLM (Answer Generation with LLM)
        Sử dụng Google Gemini để tạo câu trả lời dựa trên context
        """
        if not context.strip():
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi của bạn."
        
        print("Đang tạo câu trả lời với Google Gemini...")
        
        # Gemini works better with a single comprehensive prompt
        full_prompt = f"""
Bạn là một trợ lý AI thông minh, chuyên trả lời câu hỏi dựa trên nội dung tài liệu được cung cấp.

Hướng dẫn quan trọng:
1. Chỉ trả lời dựa trên thông tin có trong ngữ cảnh được cung cấp
2. Không tự suy diễn hoặc thêm thông tin không có trong tài liệu
3. Nếu không tìm thấy thông tin, hãy nói rõ điều đó
4. Trả lời bằng tiếng Việt một cách rõ ràng và dễ hiểu
5. Trích dẫn nguồn khi có thể (tên file, phần)
6. Nếu có nhiều nguồn thông tin, hãy tổng hợp một cách logic

Ngữ cảnh từ tài liệu:
{context}

Câu hỏi: {query}

Hãy trả lời câu hỏi dựa trên ngữ cảnh trên. Định dạng trả lời:
- Câu trả lời chính
- Nguồn tham khảo (nếu có)
"""
        
        try:
            messages = [HumanMessage(content=full_prompt)]
            response = self.llm.invoke(messages)
            answer = response.content.strip()
            
            print("✓ Đã tạo câu trả lời với Gemini thành công")
            return answer
            
        except Exception as e:
            error_msg = f"Lỗi khi tạo câu trả lời với Gemini: {str(e)}"
            print(f"✗ {error_msg}")
            return f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: {error_msg}"
    
    def process_query(self, query: str, retrieved_documents: List[Dict]) -> Dict:
        """
        Xử lý hoàn chỉnh một query: đánh giá docs -> tổng hợp context -> tạo answer
        """
        # Bước 3.3: Đánh giá và lọc documents
        relevant_docs = self.grade_retrieved_documents(query, retrieved_documents)
        
        # Bước 3.4: Tổng hợp context
        context = self.aggregate_context(relevant_docs)
        
        # Bước 3.5: Tạo câu trả lời
        answer = self.generate_answer(query, context)
        
        return {
            "query": query,
            "answer": answer,
            "relevant_documents_count": len(relevant_docs),
            "total_retrieved_count": len(retrieved_documents),
            "sources": list(set([doc["source"] for doc in relevant_docs])),
            "context": context
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái health của RAG agent
        """
        try:
            # Test simple query
            test_response = self.llm.invoke("Test connection")
            return {
                "status": "healthy",
                "model": Config.GEMINI_MODEL,
                "domain": Config.DOMAIN,
                "workflow_type": "LangGraph",
                "features": {
                    "intent_detection": True,
                    "domain_prompts": True,
                    "medical_disclaimer": True,
                    "langgraph_workflow": True,
                    "product_recommendations": getattr(Config, 'ENABLE_PRODUCT_RECOMMENDATIONS', True),
                    "technical_advice": getattr(Config, 'ENABLE_TECHNICAL_ADVICE', True)
                },
                "nodes": [
                    "detect_intent",
                    "retrieve_documents", 
                    "filter_documents",
                    "aggregate_context",
                    "generate_answer",
                    "post_process"
                ]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "workflow_type": "LangGraph"
            }

    def generate_response(self, query: str, context: str) -> Dict[str, Any]:
        """
        Tạo response với logic domain-specific cho mắt kính (legacy method for compatibility)
        """
        try:
            # Phân tích intent
            intent_info = self.detect_query_intent(query)
            
            # Tăng cường context
            enhanced_context = self.enhance_context_with_keywords(context, intent_info)
            
            # Tạo prompt tối ưu
            prompt = self.create_domain_prompt(query, enhanced_context, intent_info)
            
            # Gọi LLM
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Post-process
            final_answer = self.post_process_response(answer, intent_info)
            
            return {
                "answer": final_answer,
                "intent_info": intent_info,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "answer": f"Xin lỗi, tôi gặp khó khăn khi xử lý câu hỏi về mắt kính. Lỗi: {str(e)}",
                "intent_info": {"query_type": "error"},
                "status": "error",
                "error": str(e)
        } 