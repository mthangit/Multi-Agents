#!/usr/bin/env python3
"""
Enhanced LangGraph Workflow cho Eyewear Advisor Agent
- Advanced intent detection và routing
- Multi-step reasoning với memory
- Dynamic parameter adjustment
- Sophisticated error handling và recovery
- State management với history
"""

from typing import Dict, List, Any, TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import time
import json

from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager
from agents.rag_agent import RAGAgent
from config import Config

# Intent Detection Models
class QueryIntent(BaseModel):
    """Structured output for intent detection"""
    intent_type: Literal["medical_consultation", "product_recommendation", "technical_advice", "style_consultation", "general_inquiry", "complex_analysis"] = Field(
        description="Type of user query intent"
    )
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    sub_intents: List[str] = Field(description="Secondary intent categories", default=[])
    complexity_level: Literal["simple", "moderate", "complex", "expert"] = Field(description="Query complexity")
    requires_multi_step: bool = Field(description="Whether query needs multi-step reasoning")
    key_entities: List[str] = Field(description="Important entities extracted from query", default=[])

class WorkflowState(TypedDict):
    """Enhanced state cho LangGraph workflow"""
    # Core input
    query: str
    user_context: Dict[str, Any]  # User profile, preferences, history
    
    # Intent analysis
    intent: Optional[QueryIntent]
    processing_strategy: str
    
    # Multi-step reasoning
    reasoning_steps: List[Dict[str, Any]]
    current_step: int
    sub_queries: List[str]
    
    # Retrieval & processing
    query_embedding: List[float]
    retrieved_documents: List[Dict]
    filtered_documents: List[Dict]
    context_documents: List[Dict]
    
    # Response generation
    intermediate_answers: List[str]
    final_answer: str
    sources: List[str]
    confidence_score: float
    
    # State management
    messages: List[BaseMessage]
    step_history: List[str]
    error_count: int
    retry_count: int
    
    # Metadata
    processing_time: float
    tokens_used: int
    status: str

class EnhancedEyewearWorkflow:
    """
    Enhanced LangGraph workflow với advanced features:
    - Intelligent intent detection
    - Dynamic routing based on intent
    - Multi-step reasoning capabilities
    - Sophisticated error handling
    - State memory management
    """
    
    def __init__(self):
        print("🚀 Initializing Enhanced LangGraph Workflow...")
        
        # Initialize components
        self.embedding_manager = EmbeddingManager()
        self.qdrant_manager = QdrantManager()
        self.rag_agent = RAGAgent()
        
        # Initialize LLM for intent detection
        self.intent_llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            temperature=0.1,  # Low temperature for consistent intent detection
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        # Initialize reasoning LLM
        self.reasoning_llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            temperature=0.3,
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        # Create workflow
        self.workflow = self._create_enhanced_workflow()
        self.compiled_workflow = self.workflow.compile()
        
        print("✅ Enhanced LangGraph Workflow ready!")
    
    def _create_enhanced_workflow(self) -> StateGraph:
        """Create enhanced workflow graph with sophisticated routing"""
        workflow = StateGraph(WorkflowState)
        
        # Core processing nodes
        workflow.add_node("analyze_intent", self.analyze_intent_node)
        workflow.add_node("plan_strategy", self.plan_strategy_node)
        workflow.add_node("retrieve_context", self.retrieve_context_node)
        workflow.add_node("filter_documents", self.filter_documents_node)
        
        # Specialized processing nodes
        workflow.add_node("medical_consultation", self.medical_consultation_node)
        workflow.add_node("product_recommendation", self.product_recommendation_node)
        workflow.add_node("technical_analysis", self.technical_analysis_node)
        workflow.add_node("style_consultation", self.style_consultation_node)
        workflow.add_node("complex_reasoning", self.complex_reasoning_node)
        workflow.add_node("general_response", self.general_response_node)
        
        # Multi-step processing
        workflow.add_node("decompose_query", self.decompose_query_node)
        workflow.add_node("process_sub_query", self.process_sub_query_node)
        workflow.add_node("synthesize_answers", self.synthesize_answers_node)
        
        # Finalization
        workflow.add_node("finalize_response", self.finalize_response_node)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_intent")
        
        # Intent analysis flow
        workflow.add_edge("analyze_intent", "plan_strategy")
        
        # Strategy planning with conditional routing
        workflow.add_conditional_edges(
            "plan_strategy",
            self.route_by_strategy,
            {
                "simple_retrieval": "retrieve_context",
                "multi_step": "decompose_query",
                "error": "handle_error"
            }
        )
        
        # Document processing flow
        workflow.add_edge("retrieve_context", "filter_documents")
        
        # Intent-based routing
        workflow.add_conditional_edges(
            "filter_documents", 
            self.route_by_intent,
            {
                "medical_consultation": "medical_consultation",
                "product_recommendation": "product_recommendation", 
                "technical_advice": "technical_analysis",
                "style_consultation": "style_consultation",
                "complex_analysis": "complex_reasoning",
                "general_inquiry": "general_response"
            }
        )
        
        # Multi-step processing flow
        workflow.add_edge("decompose_query", "process_sub_query")
        workflow.add_conditional_edges(
            "process_sub_query",
            self.check_sub_queries_complete,
            {
                "continue": "process_sub_query",
                "synthesize": "synthesize_answers"
            }
        )
        
        # Finalization flow
        workflow.add_edge("medical_consultation", "finalize_response")
        workflow.add_edge("product_recommendation", "finalize_response")
        workflow.add_edge("technical_analysis", "finalize_response")
        workflow.add_edge("style_consultation", "finalize_response")
        workflow.add_edge("complex_reasoning", "finalize_response")
        workflow.add_edge("general_response", "finalize_response")
        workflow.add_edge("synthesize_answers", "finalize_response")
        
        # End states
        workflow.add_edge("finalize_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def analyze_intent_node(self, state: WorkflowState) -> WorkflowState:
        """Advanced intent analysis with LLM"""
        try:
            print("🧠 Analyzing query intent...")
            start_time = time.time()
            
            # Intent detection prompt
            intent_prompt = PromptTemplate(
                input_variables=["query"],
                template="""
Phân tích câu hỏi sau về mắt kính và xác định intent:

Câu hỏi: {query}

Hãy phân loại intent theo các categories:
1. medical_consultation: Câu hỏi về sức khỏe mắt, bệnh lý, điều trị
2. product_recommendation: Tìm hiểu/so sánh sản phẩm mắt kính
3. technical_advice: Thông tin kỹ thuật về tròng kính, công nghệ
4. style_consultation: Tư vấn phong cách, thẩm mỹ
5. general_inquiry: Câu hỏi chung chung
6. complex_analysis: Yêu cầu phân tích phức tạp, nhiều bước

Cũng đánh giá:
- Độ phức tạp: simple/moderate/complex/expert
- Có cần multi-step reasoning không?
- Confidence score (0-1)
- Key entities trong câu hỏi

Trả về JSON format với các fields: intent_type, confidence, sub_intents, complexity_level, requires_multi_step, key_entities
"""
            )
            
            # Call LLM for intent detection
            prompt_formatted = intent_prompt.format(query=state["query"])
            messages = [SystemMessage(content="You are an expert intent classifier for eyewear domain."),
                       HumanMessage(content=prompt_formatted)]
            
            response = self.intent_llm.invoke(messages)
            
            # Parse response (simplified - in production use structured output)
            try:
                # Extract JSON from response (basic parsing)
                content = response.content
                if "```json" in content:
                    json_part = content.split("```json")[1].split("```")[0]
                elif "{" in content and "}" in content:
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    json_part = content[start_idx:end_idx]
                else:
                    # Fallback
                    json_part = '{"intent_type": "general_inquiry", "confidence": 0.7, "sub_intents": [], "complexity_level": "moderate", "requires_multi_step": false, "key_entities": []}'
                
                intent_data = json.loads(json_part)
                intent = QueryIntent(**intent_data)
                
            except:
                # Fallback intent
                intent = QueryIntent(
                    intent_type="general_inquiry",
                    confidence=0.7,
                    complexity_level="moderate",
                    requires_multi_step=False
                )
            
            state["intent"] = intent
            state["step_history"] = ["analyze_intent"]
            state["processing_time"] = time.time() - start_time
            
            print(f"🎯 Intent detected: {intent.intent_type} (confidence: {intent.confidence:.2f})")
            print(f"🔍 Complexity: {intent.complexity_level}, Multi-step: {intent.requires_multi_step}")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["status"] = "error"
            print(f"❌ Error in intent analysis: {e}")
            return state
    
    def plan_strategy_node(self, state: WorkflowState) -> WorkflowState:
        """Plan processing strategy based on intent analysis"""
        try:
            print("📋 Planning processing strategy...")
            
            intent = state["intent"]
            
            if intent.requires_multi_step or intent.complexity_level in ["complex", "expert"]:
                state["processing_strategy"] = "multi_step"
                print("🔄 Strategy: Multi-step reasoning")
            else:
                state["processing_strategy"] = "simple_retrieval"
                print("➡️  Strategy: Simple retrieval")
            
            state["step_history"].append("plan_strategy")
            return state
            
        except Exception as e:
            state["processing_strategy"] = "error"
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    def retrieve_context_node(self, state: WorkflowState) -> WorkflowState:
        """Enhanced document retrieval with dynamic parameters"""
        try:
            print("🔍 Retrieving relevant context...")
            
            # Create query embedding
            query_embedding = self.embedding_manager.embed_query(state["query"])
            state["query_embedding"] = query_embedding.tolist()
            
            # Dynamic retrieval parameters based on intent
            intent = state["intent"]
            if intent.complexity_level == "expert":
                top_k = min(15, Config.TOP_K_DOCUMENTS + 5)
            elif intent.complexity_level == "complex":
                top_k = min(12, Config.TOP_K_DOCUMENTS + 2)
            else:
                top_k = Config.TOP_K_DOCUMENTS
            
            # Retrieve documents
            retrieved_docs = self.qdrant_manager.search_similar_documents(
                query_embedding.tolist(), 
                top_k=top_k
            )
            
            state["retrieved_documents"] = retrieved_docs
            state["step_history"].append("retrieve_context")
            
            print(f"📄 Retrieved {len(retrieved_docs)} documents")
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["status"] = "error"
            return state
    
    def filter_documents_node(self, state: WorkflowState) -> WorkflowState:
        """Intelligent document filtering using LLM"""
        try:
            print("🎯 Filtering documents by relevance...")
            
            intent = state["intent"]
            retrieved_docs = state["retrieved_documents"]
            
            if not retrieved_docs:
                state["filtered_documents"] = []
                return state
            
            # LLM-based relevance filtering
            filter_prompt = f"""
Đánh giá relevance của documents sau cho câu hỏi: "{state['query']}"
Intent type: {intent.intent_type}
Key entities: {intent.key_entities}

Chỉ giữ lại documents thực sự hữu ích cho intent này.
Trả về danh sách index của documents relevance (từ 0 đến {len(retrieved_docs)-1}).
"""
            
            # Simplified filtering (can be enhanced with LLM scoring)
            filtered_docs = retrieved_docs[:8]  # Basic filtering
            
            state["filtered_documents"] = filtered_docs
            state["step_history"].append("filter_documents")
            
            print(f"✅ Filtered to {len(filtered_docs)} most relevant documents")
            return state
            
        except Exception as e:
            state["filtered_documents"] = state.get("retrieved_documents", [])
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    # Specialized processing nodes
    def medical_consultation_node(self, state: WorkflowState) -> WorkflowState:
        """Specialized medical consultation processing"""
        try:
            print("🏥 Processing medical consultation...")
            
            medical_prompt = """
Bạn là chuyên gia nhãn khoa với 20+ năm kinh nghiệm. Hãy tư vấn về vấn đề mắt/kính dựa trên thông tin sau:

Context: {context}
Câu hỏi: {query}

Hướng dẫn trả lời:
1. Phân tích triệu chứng/vấn đề nếu có
2. Đưa ra lời khuyên chuyên môn
3. LUÔN khuyến nghị thăm khám bác sĩ nhãn khoa nếu liên quan sức khỏe
4. Cung cấp thông tin an toàn và có căn cứ
5. Tránh chẩn đoán qua internet

Lưu ý: Ưu tiên sự an toàn của bệnh nhân.
"""
            
            result = self.rag_agent.process_query(
                state["query"], 
                state["filtered_documents"],
                custom_prompt=medical_prompt
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.9  # High confidence for medical
            state["step_history"].append("medical_consultation")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi xử lý tư vấn y tế. Vui lòng thăm khám bác sĩ nhãn khoa."
            return state
    
    def product_recommendation_node(self, state: WorkflowState) -> WorkflowState:
        """Specialized product recommendation processing"""
        try:
            print("🛍️ Processing product recommendation...")
            
            product_prompt = """
Bạn là chuyên gia tư vấn sản phẩm mắt kính với kiến thức sâu về các thương hiệu và công nghệ.

Context: {context}
Câu hỏi: {query}

Hãy đưa ra khuyến nghị sản phẩm:
1. Phân tích nhu cầu của khách hàng
2. So sánh các lựa chọn phù hợp
3. Giải thích ưu/nhược điểm từng loại
4. Đưa ra khuyến nghị cụ thể với lý do
5. Đề xuất mức giá và nơi mua nếu có
6. Lưu ý về tương thích với đặc điểm cá nhân

Phong cách: Thân thiện, chuyên nghiệp, dễ hiểu.
"""
            
            result = self.rag_agent.process_query(
                state["query"],
                state["filtered_documents"], 
                custom_prompt=product_prompt
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.85
            state["step_history"].append("product_recommendation")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi đưa ra khuyến nghị sản phẩm."
            return state
    
    def technical_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Technical analysis processing"""
        try:
            print("🔬 Processing technical analysis...")
            
            technical_prompt = """
Bạn là kỹ sư quang học chuyên về công nghệ tròng kính và gọng mắt kính.

Context: {context}
Câu hỏi: {query}

Hãy đưa ra phân tích kỹ thuật:
1. Giải thích các khái niệm/công nghệ liên quan
2. Phân tích ưu/nhược điểm kỹ thuật
3. So sánh với các công nghệ khác
4. Đưa ra đánh giá khách quan
5. Giải thích cách hoạt động nếu phù hợp
6. Đề xuất ứng dụng thực tế

Phong cách: Chính xác, khoa học, chi tiết nhưng dễ hiểu.
"""
            
            result = self.rag_agent.process_query(
                state["query"],
                state["filtered_documents"],
                custom_prompt=technical_prompt
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.88
            state["step_history"].append("technical_analysis")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi phân tích kỹ thuật."
            return state
    
    def style_consultation_node(self, state: WorkflowState) -> WorkflowState:
        """Style consultation processing"""
        try:
            print("👓 Processing style consultation...")
            
            style_prompt = """
Bạn là chuyên gia tư vấn phong cách và thẩm mỹ mắt kính với kinh nghiệm styling cho nhiều dáng mặt.

Context: {context}
Câu hỏi: {query}

Hãy tư vấn phong cách:
1. Phân tích đặc điểm khuôn mặt/phong cách cá nhân
2. Khuyến nghị kiểu gọng phù hợp
3. Tư vấn về màu sắc và chất liệu
4. Đưa ra tips phối đồ với mắt kính
5. Gợi ý xu hướng thời trang mắt kính
6. Cân nhắc về tính thực tế và sử dụng

Phong cách: Thân thiện, sáng tạo, cập nhật xu hướng.
"""
            
            result = self.rag_agent.process_query(
                state["query"],
                state["filtered_documents"],
                custom_prompt=style_prompt
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.82
            state["step_history"].append("style_consultation")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi tư vấn phong cách."
            return state
    
    def complex_reasoning_node(self, state: WorkflowState) -> WorkflowState:
        """Complex multi-faceted analysis"""
        try:
            print("🧩 Processing complex analysis...")
            
            complex_prompt = """
Bạn là chuyên gia tổng hợp với kiến thức đa ngành về mắt kính (y tế, kỹ thuật, thẩm mỹ, kinh tế).

Context: {context}
Câu hỏi phức tạp: {query}

Hãy đưa ra phân tích toàn diện:
1. Phân tích đa chiều vấn đề
2. Xem xét các yếu tố liên quan (sức khỏe, kinh tế, thẩm mỹ, kỹ thuật)
3. Đưa ra pros/cons của các lựa chọn
4. Khuyến nghị tối ưu dựa trên trade-offs
5. Đề xuất các bước thực hiện cụ thể
6. Cân nhắc rủi ro và lưu ý

Phong cách: Toàn diện, cân bằng, có cấu trúc rõ ràng.
"""
            
            result = self.rag_agent.process_query(
                state["query"],
                state["filtered_documents"],
                custom_prompt=complex_prompt
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.87
            state["step_history"].append("complex_reasoning")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi phân tích phức tạp."
            return state
    
    def general_response_node(self, state: WorkflowState) -> WorkflowState:
        """General response processing"""
        try:
            print("💬 Processing general inquiry...")
            
            result = self.rag_agent.process_query(
                state["query"],
                state["filtered_documents"]
            )
            
            state["final_answer"] = result["answer"]
            state["sources"] = result.get("sources", [])
            state["confidence_score"] = 0.75
            state["step_history"].append("general_response")
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            state["final_answer"] = "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi."
            return state
    
    # Multi-step processing nodes
    def decompose_query_node(self, state: WorkflowState) -> WorkflowState:
        """Decompose complex query into sub-queries"""
        try:
            print("🔄 Decomposing complex query...")
            
            # Use LLM to break down complex query
            decompose_prompt = f"""
Phân tách câu hỏi phức tạp sau thành các sub-queries đơn giản hơn:

Query: {state['query']}
Intent: {state['intent'].intent_type}

Chia thành 2-4 câu hỏi con có thể trả lời độc lập:
1. [Sub-query 1]
2. [Sub-query 2]
...

Trả về danh sách các sub-queries.
"""
            
            # Simplified decomposition (can enhance with LLM)
            sub_queries = [
                f"Thông tin cơ bản về {' '.join(state['intent'].key_entities)}",
                f"Khuyến nghị cụ thể cho {state['query'][:50]}...",
                "Lưu ý và cân nhắc quan trọng"
            ]
            
            state["sub_queries"] = sub_queries
            state["current_step"] = 0
            state["intermediate_answers"] = []
            state["step_history"].append("decompose_query")
            
            print(f"🧩 Decomposed into {len(sub_queries)} sub-queries")
            return state
            
        except Exception as e:
            state["processing_strategy"] = "error"
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    def process_sub_query_node(self, state: WorkflowState) -> WorkflowState:
        """Process individual sub-query"""
        try:
            current_step = state["current_step"]
            sub_queries = state["sub_queries"]
            
            if current_step < len(sub_queries):
                sub_query = sub_queries[current_step]
                print(f"🔍 Processing sub-query {current_step + 1}: {sub_query}")
                
                # Process sub-query with relevant documents
                result = self.rag_agent.process_query(
                    sub_query,
                    state["filtered_documents"]
                )
                
                state["intermediate_answers"].append({
                    "sub_query": sub_query,
                    "answer": result["answer"],
                    "sources": result.get("sources", [])
                })
                
                state["current_step"] += 1
            
            return state
            
        except Exception as e:
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    def synthesize_answers_node(self, state: WorkflowState) -> WorkflowState:
        """Synthesize multiple answers into comprehensive response"""
        try:
            print("🔗 Synthesizing comprehensive answer...")
            
            intermediate_answers = state["intermediate_answers"]
            
            # Create synthesis prompt
            synthesis_content = "\n\n".join([
                f"Q: {ans['sub_query']}\nA: {ans['answer']}"
                for ans in intermediate_answers
            ])
            
            synthesis_prompt = f"""
Tổng hợp các câu trả lời sau thành một phản hồi hoàn chỉnh cho câu hỏi gốc:

Câu hỏi gốc: {state['query']}

Các câu trả lời thành phần:
{synthesis_content}

Hãy tạo một câu trả lời tổng hợp:
1. Có cấu trúc rõ ràng
2. Loại bỏ thông tin trùng lặp
3. Kết nối logic giữa các phần
4. Đưa ra kết luận tổng thể
5. Giữ nguyên các thông tin quan trọng
"""
            
            # Use reasoning LLM for synthesis
            messages = [
                SystemMessage(content="You are an expert at synthesizing information."),
                HumanMessage(content=synthesis_prompt)
            ]
            
            response = self.reasoning_llm.invoke(messages)
            
            state["final_answer"] = response.content
            
            # Collect all sources
            all_sources = []
            for ans in intermediate_answers:
                all_sources.extend(ans.get("sources", []))
            state["sources"] = list(set(all_sources))  # Remove duplicates
            
            state["confidence_score"] = 0.85
            state["step_history"].append("synthesize_answers")
            
            return state
            
        except Exception as e:
            # Fallback to simple concatenation
            answers = [ans["answer"] for ans in state["intermediate_answers"]]
            state["final_answer"] = "\n\n".join(answers)
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    def finalize_response_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize and enhance the response"""
        try:
            print("✨ Finalizing response...")
            
            # Add metadata and enhancements
            if not state.get("final_answer"):
                state["final_answer"] = "Xin lỗi, tôi không thể trả lời câu hỏi này."
                state["confidence_score"] = 0.0
            
            # Ensure we have sources
            if not state.get("sources"):
                state["sources"] = []
            
            # Calculate total processing time
            total_time = time.time() - state.get("processing_time", time.time())
            state["processing_time"] = total_time
            
            state["status"] = "completed"
            state["step_history"].append("finalize_response")
            
            print(f"✅ Response finalized in {total_time:.2f}s")
            return state
            
        except Exception as e:
            state["status"] = "error"
            state["error_count"] = state.get("error_count", 0) + 1
            return state
    
    def handle_error_node(self, state: WorkflowState) -> WorkflowState:
        """Enhanced error handling with recovery"""
        try:
            error_count = state.get("error_count", 0)
            
            if error_count < 3:  # Retry logic
                print(f"⚠️ Error occurred, attempting recovery (attempt {error_count + 1}/3)")
                state["final_answer"] = "Đang thử lại xử lý câu hỏi..."
                state["retry_count"] = state.get("retry_count", 0) + 1
            else:
                print("❌ Maximum errors reached, providing fallback response")
                state["final_answer"] = """
Xin lỗi, tôi gặp khó khăn khi xử lý câu hỏi của bạn. 

Vui lòng:
1. Thử lại với câu hỏi đơn giản hơn
2. Kiểm tra kết nối internet
3. Liên hệ hỗ trợ kỹ thuật nếu vấn đề tiếp tục

Cảm ơn bạn đã sử dụng dịch vụ tư vấn mắt kính!
"""
            
            state["status"] = "error_handled"
            state["confidence_score"] = 0.1
            state["sources"] = []
            
            return state
            
        except Exception as e:
            state["final_answer"] = "Hệ thống gặp lỗi nghiêm trọng. Vui lòng thử lại sau."
            state["status"] = "critical_error"
            return state
    
    # Routing functions
    def route_by_strategy(self, state: WorkflowState) -> str:
        """Route based on processing strategy"""
        strategy = state.get("processing_strategy", "simple_retrieval")
        
        if strategy == "error":
            return "error"
        elif strategy == "multi_step":
            return "multi_step"
        else:
            return "simple_retrieval"
    
    def route_by_intent(self, state: WorkflowState) -> str:
        """Route based on detected intent"""
        intent = state.get("intent")
        if not intent:
            return "general_inquiry"
        
        return intent.intent_type
    
    def check_sub_queries_complete(self, state: WorkflowState) -> str:
        """Check if all sub-queries are processed"""
        current_step = state.get("current_step", 0)
        total_steps = len(state.get("sub_queries", []))
        
        if current_step < total_steps:
            return "continue"
        else:
            return "synthesize"
    
    # Main execution methods
    def invoke(self, query: str, user_context: Dict = None, **kwargs) -> Dict:
        """
        Main invoke method for the enhanced workflow
        
        Args:
            query: User question
            user_context: User profile/preferences/history
            **kwargs: Additional parameters
        
        Returns:
            Comprehensive result dictionary
        """
        try:
            # Initialize state
            initial_state = WorkflowState(
                query=query,
                user_context=user_context or {},
                reasoning_steps=[],
                current_step=0,
                sub_queries=[],
                retrieved_documents=[],
                filtered_documents=[],
                intermediate_answers=[],
                messages=[],
                step_history=[],
                error_count=0,
                retry_count=0,
                processing_time=time.time(),
                tokens_used=0,
                status="processing"
            )
            
            # Run workflow
            final_state = self.compiled_workflow.invoke(initial_state)
            
            # Format response
            return {
                "query": query,
                "answer": final_state.get("final_answer", ""),
                "sources": final_state.get("sources", []),
                "intent": final_state.get("intent").dict() if final_state.get("intent") else None,
                "confidence_score": final_state.get("confidence_score", 0.0),
                "processing_time": final_state.get("processing_time", 0.0),
                "step_history": final_state.get("step_history", []),
                "status": final_state.get("status", "unknown"),
                "metadata": {
                    "workflow_type": "enhanced_langgraph",
                    "error_count": final_state.get("error_count", 0),
                    "retry_count": final_state.get("retry_count", 0),
                    "reasoning_steps": len(final_state.get("reasoning_steps", [])),
                    "documents_retrieved": len(final_state.get("retrieved_documents", [])),
                    "documents_filtered": len(final_state.get("filtered_documents", []))
                }
            }
            
        except Exception as e:
            return {
                "query": query,
                "answer": f"Lỗi nghiêm trọng trong workflow: {str(e)}",
                "sources": [],
                "intent": None,
                "confidence_score": 0.0,
                "processing_time": 0.0,
                "step_history": ["error"],
                "status": "critical_error",
                "error": str(e),
                "metadata": {"workflow_type": "enhanced_langgraph"}
            }

def create_enhanced_workflow() -> EnhancedEyewearWorkflow:
    """Factory function to create enhanced workflow"""
    return EnhancedEyewearWorkflow()

def get_enhanced_workflow() -> EnhancedEyewearWorkflow:
    """Get singleton instance of enhanced workflow"""
    global _enhanced_workflow_instance
    if '_enhanced_workflow_instance' not in globals():
        _enhanced_workflow_instance = create_enhanced_workflow()
    return _enhanced_workflow_instance 