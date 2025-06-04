from typing import List, Dict, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from config import Config, EYEWEAR_KEYWORDS
import re

class RAGAgent:
    def __init__(self):
        """
        Khởi tạo RAG Agent với Google Gemini cho domain mắt kính
        """
        print(f"🤖 Đang khởi tạo RAG Agent cho domain: {Config.DOMAIN}")
        print(f"🤖 Đang khởi tạo Gemini model: {Config.GEMINI_MODEL}")
        
        self.llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            temperature=Config.GEMINI_TEMPERATURE,
            max_output_tokens=Config.GEMINI_MAX_OUTPUT_TOKENS,
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        print("✅ RAG Agent đã sẵn sàng!")
    
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

        elif intent_info["query_type"] == "product_recommendation":
            role_specific = """
Hãy tập trung vào:
- So sánh ưu nhược điểm các sản phẩm
- Đề xuất sản phẩm phù hợp với nhu cầu
- Thông tin về giá cả và chất lượng
- Hướng dẫn cách chọn mua"""

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
    
    def generate_response(self, query: str, context: str) -> Dict[str, Any]:
        """
        Tạo response với logic domain-specific cho mắt kính
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
                "features": {
                    "intent_detection": True,
                    "domain_prompts": True,
                    "medical_disclaimer": True,
                    "product_recommendations": Config.ENABLE_PRODUCT_RECOMMENDATIONS,
                    "technical_advice": Config.ENABLE_TECHNICAL_ADVICE
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

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
        
        context = "\n" + "="*50 + "\n".join(context_parts)
        
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