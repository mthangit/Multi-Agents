"""
Host Server - Core logic cho việc điều phối message tới các agent
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import json

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from prompt.root_prompt import ROOT_INSTRUCTION
from .a2a_client_manager import A2AClientManager
from .langchain_memory_adapter import EnhancedMemoryManager
from .mysql_message_history import MySQLMessageHistory
from db_connector import db_connector
logger = logging.getLogger(__name__)

class HostServer:
    def __init__(self):
        """Khởi tạo Host Server"""
        # Khởi tạo LangChain LLM
        self.llm = None
        self.orchestrator_chain = None
        
        # A2A Client Manager để quản lý các agent connections
        self.a2a_client_manager = A2AClientManager()
        
        # Enhanced Memory Manager với LangChain
        self.memory_manager = None
        
        # MySQL Message History cho real-time logging
        self.mysql_history = MySQLMessageHistory()
        
        # Database Connector để query thông tin sản phẩm  
        
        self.db_connector = db_connector

    async def initialize(self):
        """Khởi tạo các components cần thiết"""
        try:
            # Khởi tạo Google Generative AI
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.2
            )
            
            # Setup orchestrator chain
            await self._setup_orchestrator_chain()
            
            # Database Connector đã được khởi tạo với fresh connection pattern
            logger.info("✅ Database Connector (singleton) với fresh connections đã sẵn sàng")
            
            # Khởi tạo A2A Client Manager
            await self.a2a_client_manager.initialize()
            
            # Khởi tạo Enhanced Memory Manager
            self.memory_manager = EnhancedMemoryManager(
                redis_client=self.a2a_client_manager.redis_client,
                llm=self.llm
            )
            
            # Khởi tạo MySQL Message History
            try:
                await self.mysql_history.initialize()
                logger.info("✅ MySQL Message History initialized")
            except Exception as e:
                logger.warning(f"⚠️ MySQL Message History failed to initialize: {e}")
                logger.warning("📝 Messages will only be saved to Redis/LangChain memory")
            
            logger.info("✅ Host Server đã khởi tạo thành công!")
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi khởi tạo Host Server: {e}")
            raise

    async def _setup_orchestrator_chain(self):
        """Setup LangChain cho việc phân tích và điều phối"""
        
        
        # Tạo prompt template cho orchestrator thông thường
        prompt_template = PromptTemplate(
            input_variables=["user_message", "available_agents"],
            template=f"""
{ROOT_INSTRUCTION}

**Message từ User:**
{{user_message}}

**Nhiệm vụ của bạn:**
1. Phân tích và làm rõ message của user dựa vào context từ lịch sử hội thoại
2. **QUAN TRỌNG - Xử lý yêu cầu mua hàng:**
   - Nếu user muốn mua/đặt hàng sản phẩm nào đó, PHẢI tìm ID sản phẩm từ context
   - Tìm kiếm trong lịch sử các sản phẩm đã được search agent gợi ý (có chứa ID: xxx)
   - Xác định chính xác sản phẩm nào user muốn mua dựa vào mô tả/tên sản phẩm
   - Đính kèm product ID vào message gửi tới order agent
3. Viết lại message một cách rõ ràng hơn, thay thế các đại từ chỉ định bằng tên cụ thể
4. Xác định agent nào phù hợp nhất để xử lý yêu cầu đã được làm rõ
5. Trả về response theo format JSON:

{{{{
    "analysis": "Phân tích ngắn gọn về yêu cầu của user",
    "clarified_message": "Message đã được viết lại rõ ràng hơn, thay thế các đại từ bằng tên cụ thể",
    "selected_agent": "Tên agent được chọn (hoặc null nếu có thể trả lời trực tiếp)",
    "message_to_agent": "Message đã được làm rõ để gửi tới agent (nếu có) - PHẢI chứa product ID nếu là yêu cầu mua hàng",
    "extracted_product_ids": ["ID1", "ID2"] (nếu có - danh sách ID sản phẩm user muốn mua),
    "direct_response": "Response trực tiếp (nếu không cần agent nào khác)"
}}}}

**Hướng dẫn xử lý yêu cầu đặt hàng:**
- **Từ khóa tạo đơn hàng mới**: "mua", "đặt hàng", "order", "thêm vào giỏ", "tôi cần", "tôi muốn lấy" (khi chưa có đơn hàng)
- **Từ khóa chỉnh sửa đơn hàng**: "sửa đơn hàng", "thay đổi", "chỉnh sửa", "cập nhật đơn hàng", "thêm vào đơn hàng hiện tại", "bỏ sản phẩm", "đổi địa chỉ", "đổi số lượng"

**Khi phát hiện yêu cầu tạo đơn hàng mới:**
  1. Quét lại context để tìm các sản phẩm có ID (định dạng: "ID: xxx" hoặc "id: xxx")
  2. So khớp mô tả sản phẩm với yêu cầu của user
  3. Trích xuất chính xác product ID và đính kèm vào message_to_agent
  4. Format: "Tạo đơn hàng mới với [tên sản phẩm] ID: [ID]"

**Khi phát hiện yêu cầu chỉnh sửa đơn hàng:**
  1. Xác định đơn hàng nào cần chỉnh sửa từ context
  2. Trích xuất product ID nếu có sản phẩm mới cần thêm
  3. Format: "Yêu cầu chỉnh sửa đơn hàng [mô tả thay đổi cụ thể]"

**Hướng dẫn làm rõ message:**
- Nếu user nói "sản phẩm đó", "cái này", "nó" → thay bằng tên cụ thể từ context
- Nếu user nói "tôi muốn mua nó" → thay bằng "tôi muốn mua [tên sản phẩm cụ thể] với ID: [ID]"
- Nếu user nói "làm như vậy" → thay bằng hành động cụ thể đã đề cập trước đó
- Nếu user nói "địa chỉ đó" → thay bằng địa chỉ cụ thể từ context
- Luôn đảm bảo clarified_message có thể hiểu được mà không cần context bổ sung

**Lưu ý:**
- Chỉ chọn agent khi thực sự cần thiết
- Nếu có thể trả lời trực tiếp, đặt selected_agent = null
- Message_to_agent phải sử dụng clarified_message và chứa đủ context
- **ĐẶC BIỆT QUAN TRỌNG**: Nếu là yêu cầu mua hàng, message_to_agent PHẢI chứa product ID
- **TUYỆT ĐỐI KHÔNG nhắc đến tên agent** trong direct_response hoặc khi tham khảo thông tin từ context
- **KHÔNG bao giờ nói**: "Search Agent đã tìm", "theo Advisor Agent", "như đã trả lời trước đó bởi..."
- **CHỈ trả lời trực tiếp** nội dung thông tin mà không mention nguồn agent
- Direct_response chỉ dùng khi không cần agent khác
"""
        )
        
        # Tạo prompt template cho clarification khi có files (không cần chọn agent)
        file_clarification_template = PromptTemplate(
            input_variables=["user_message"],
            template=f"""
{ROOT_INSTRUCTION}

**Message từ User (có kèm files):**
{{user_message}}

**Nhiệm vụ của bạn:**
1. **Phân tích context**: Đọc và hiểu toàn bộ context từ lịch sử hội thoại
2. **Tóm tắt context**: Tạo summary ngắn gọn mà vẫn phải đầy đủ về thông tin quan trọng từ context (sản phẩm đã tìm, thông tin user, etc.)
3. **Làm rõ message**: Viết lại message của user rõ ràng hơn, thay thế các đại từ chỉ định bằng tên cụ thể
4. **Tạo message hoàn chỉnh**: Kết hợp message đã clarify với context summary để tạo message tự đủ gửi tới agent
5. **QUAN TRỌNG - Xử lý yêu cầu mua hàng:**
   - Nếu user muốn mua/đặt hàng sản phẩm nào đó, PHẢI tìm ID sản phẩm từ context
   - Tìm kiếm trong lịch sử các sản phẩm đã được gợi ý (có chứa ID: xxx)
   - Xác định chính xác sản phẩm nào user muốn mua dựa vào mô tả/tên sản phẩm
   - Đính kèm product ID vào message

**Trả về response theo format JSON:**

{{{{
    "analysis": "Phân tích ngắn gọn về yêu cầu của user và context",
    "context_summary": "Tóm tắt thông tin quan trọng từ context (sản phẩm, giá cả, thông tin user, etc.)",
    "clarified_message": "Message đã được viết lại rõ ràng hơn, thay thế các đại từ bằng tên cụ thể",
    "message_to_agent": "Message hoàn chỉnh tự đủ = clarified_message + context_summary tích hợp - PHẢI chứa product ID nếu là yêu cầu mua hàng",
    "extracted_product_ids": ["ID1", "ID2"] (nếu có - danh sách ID sản phẩm user muốn mua)
}}}}

**Hướng dẫn tạo message_to_agent hoàn chỉnh:**
- Bắt đầu bằng clarified_message
- Tích hợp context_summary một cách tự nhiên vào message
- Đảm bảo agent có thể hiểu hoàn toàn request mà không cần đọc thêm context gì khác
- Format ví dụ: "Tôi muốn mua sản phẩm ABC với ID: 123. Trước đó tôi đã tìm hiểu về sản phẩm này với giá 500k và đã xem các thông tin chi tiết..."

**Hướng dẫn xử lý yêu cầu đặt hàng:**
- **Từ khóa tạo đơn hàng mới**: "mua", "đặt hàng", "order", "thêm vào giỏ", "tôi cần", "tôi muốn lấy" (khi user chưa có đơn hàng hiện tại)
- **Từ khóa chỉnh sửa đơn hàng**: "sửa đơn hàng", "thay đổi đơn hàng", "chỉnh sửa", "cập nhật đơn hàng", "thêm vào đơn hàng hiện tại", "bỏ sản phẩm", "đổi địa chỉ", "đổi số lượng"

**Khi phát hiện yêu cầu tạo đơn hàng mới:**
  1. Quét lại context để tìm các sản phẩm có ID (định dạng: "ID: xxx" hoặc "id: xxx")
  2. So khớp mô tả sản phẩm với yêu cầu của user
  3. Trích xuất chính xác product ID và đính kèm vào message_to_agent
  4. Format: "Tạo đơn hàng mới với [tên sản phẩm] ID: [ID] + context về sản phẩm này"

**Khi phát hiện yêu cầu chỉnh sửa đơn hàng:**
  1. Xác định đơn hàng nào cần chỉnh sửa từ context hoặc lịch sử
  2. Trích xuất product ID nếu có sản phẩm mới cần thêm
  3. Format: "Yêu cầu chỉnh sửa đơn hàng [mô tả chi tiết thay đổi] + context về đơn hàng hiện tại"

**Hướng dẫn làm rõ message:**
- Nếu user nói "sản phẩm đó", "cái này", "nó" → thay bằng tên cụ thể từ context
- Nếu user nói "tôi muốn mua nó" → thay bằng "tôi muốn mua [tên sản phẩm cụ thể] với ID: [ID]"
- Nếu user nói "làm như vậy" → thay bằng hành động cụ thể đã đề cập trước đó
- Nếu user nói "địa chỉ đó" → thay bằng địa chỉ cụ thể từ context
- Luôn đảm bảo clarified_message có thể hiểu được mà không cần context bổ sung

**Lưu ý quan trọng:**
- **message_to_agent phải là message hoàn chỉnh tự đủ**, agent không cần đọc thêm context nào khác
- **ĐẶC BIỆT QUAN TRỌNG**: 
  + Nếu là yêu cầu **tạo đơn hàng mới**, message_to_agent phải bắt đầu bằng "Tạo đơn hàng mới..." và PHẢI chứa product ID
  + Nếu là yêu cầu **chỉnh sửa đơn hàng**, message_to_agent phải bắt đầu bằng "Yêu cầu chỉnh sửa đơn hàng..." và mô tả rõ thay đổi
- Context summary phải ngắn gọn nhưng đầy đủ thông tin cần thiết
- Tích hợp context một cách tự nhiên, không làm message trở nên rườm rà

"""
        )
        
        # Tạo các chains
        self.orchestrator_chain = prompt_template | self.llm | StrOutputParser()
        self.file_clarification_chain = file_clarification_template | self.llm | StrOutputParser()

    async def process_message(self, message: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Xử lý message từ user và điều phối tới agent phù hợp
        """
        try:
            # Chuẩn bị thông tin cho orchestrator
            available_agents = await self.a2a_client_manager.get_available_agents()

            # Lấy context từ LangChain memory nếu có session_id
            context_info = ""
            if session_id and self.memory_manager:
                try:
                    context = await self.memory_manager.get_conversation_context(session_id, user_id, max_messages=5)
                    if context:
                        context_info = f"\nContext từ cuộc hội thoại trước:\n{context}"
                except Exception as e:
                    logger.warning(f"⚠️ Lỗi khi lấy context từ memory: {e}")
                    # Fallback to old method
                    if user_id:
                        chat_history = await self.a2a_client_manager.get_chat_history(user_id, session_id)
                    else:
                        chat_history = self.a2a_client_manager.get_chat_history_fallback(session_id)
                    if chat_history:
                        context_info = f"\nContext từ cuộc hội thoại trước:\n{chat_history.get_context_string()}"
            
            # Gọi orchestrator chain để phân tích
            orchestrator_response = await self.orchestrator_chain.ainvoke({
                "user_message": message + context_info,
                "available_agents": ", ".join(available_agents)
            })
            
            logger.info(f"🤖 Orchestrator response: {orchestrator_response}")
            
            # Parse response từ orchestrator
            decision = await self._parse_orchestrator_response(orchestrator_response)
            
            # Xử lý theo decision
            clarified_message = decision.get("clarified_message", message)
            
            if decision.get("selected_agent") and decision["selected_agent"] != "null":
                # Gửi message đã được làm rõ tới agent được chọn qua A2A
                agent_response = await self.a2a_client_manager.send_message_to_agent(
                    agent_name=decision["selected_agent"],
                    message=decision.get("message_to_agent", clarified_message),
                    user_id=user_id,
                    session_id=session_id
                )
                
                # agent_response_data = self.parse_agent_response(agent_response)
                agent_response_data = agent_response
 
                print(f"Agent response: {agent_response}")
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=agent_response_data.get("text", ""), 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=clarified_message,
                    agent_name=decision["selected_agent"],
                    response_data=agent_response_data.get("data", []),
                    analysis=decision.get("analysis", ""),
                    orders=agent_response_data.get("orders", []),
                    user_info=agent_response_data.get("user_info", {}),
                    products=agent_response_data.get("data", []),
                    extracted_product_ids=decision.get("extracted_product_ids", [])
                )

                return {    
                    "response": agent_response_data.get("text", ""),
                    "agent_used": decision["selected_agent"],
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id,
                    "data": agent_response_data.get("data", []),
                    "user_info": agent_response_data.get("user_info", {}),
                    "orders": agent_response_data.get("orders", []),
                    "extracted_product_ids": decision.get("extracted_product_ids", [])
                }
            else:
                # Trả lời trực tiếp và lưu vào memory
                direct_response = decision.get("direct_response", "Xin lỗi, tôi chưa hiểu yêu cầu của bạn.")
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=direct_response, 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=clarified_message,
                    agent_name="Host Agent",
                    analysis=decision.get("analysis", ""),
                    orders=[],
                    user_info={},
                    products=[],
                    extracted_product_ids=decision.get("extracted_product_ids", [])
                )
                                
                return {
                    "response": direct_response,
                    "agent_used": None,
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id,
                    "extracted_product_ids": decision.get("extracted_product_ids", [])
                }
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý message: {e}")
            return {
                "response": f"Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn: {str(e)}",
                "agent_used": None,
                "analysis": "Error occurred",
                "session_id": session_id
            }

    async def process_message_with_files(
        self, 
        message: str, 
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None,
        files: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Xử lý message từ user có kèm files - lấy context và clarify message, nhưng gửi thẳng qua Search Agent
        """
        try:
            # Nếu có files, vẫn lấy context và clarify message nhưng gửi thẳng qua Search Agent
            if files and len(files) > 0:
                # logger.info(f"📁 Phát hiện {len(files)} files, lấy context và clarify message trước khi gửi qua Search Agent")
                            
                # # Lấy context từ LangChain memory nếu có session_id
                # context_info = ""
                # if session_id and self.memory_manager:
                #     try:
                #         context = await self.memory_manager.get_conversation_context(session_id, user_id, max_messages=5)
                #         if context:
                #             context_info = f"\nContext từ cuộc hội thoại trước:\n{context}"
                #     except Exception as e:
                #         logger.warning(f"⚠️ Lỗi khi lấy context từ memory: {e}")
                #         # Fallback to old method
                #         if user_id:
                #             chat_history = await self.a2a_client_manager.get_chat_history(user_id, session_id)
                #         else:
                #             chat_history = self.a2a_client_manager.get_chat_history_fallback(session_id)
                #         if chat_history:
                #             context_info = f"\nContext từ cuộc hội thoại trước:\n{chat_history.get_context_string()}"
                
                # # Thêm thông tin về files nếu có
                # files_info = ""
                # if files:
                #     file_descriptions = []
                #     for file_info in files:
                #         file_descriptions.append(f"- {file_info.name} ({file_info.mime_type})")
                #     files_info = f"\nFiles đính kèm:\n" + "\n".join(file_descriptions)
                
                # # Gọi file clarification chain để phân tích và clarify message (không cần chọn agent)
                # full_message = message + context_info + files_info
                # clarification_response = await self.file_clarification_chain.ainvoke({
                #     "user_message": full_message
                # })
                
                # logger.info(f"🤖 File clarification response: {clarification_response}")
                
                # # Parse response để lấy clarified message và context summary
                # decision = await self._parse_orchestrator_response(clarification_response)
                # clarified_message = decision.get("clarified_message", message)
                # context_summary = decision.get("context_summary", "")
                # message_to_agent = decision.get("message_to_agent", clarified_message)
                
                # # Bỏ qua agent selection, gửi thẳng qua Search Agent
                # logger.info(f"📁 Gửi message hoàn chỉnh qua Search Agent: {message_to_agent}")
                
                agent_response = await self.a2a_client_manager.send_message_to_agent(
                    agent_name="Search Agent",
                    message=message,
                    user_id=user_id,
                    session_id=session_id,
                    files=files
                )
                
                agent_response_data = agent_response
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=agent_response_data["text"], 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=None,
                    agent_name="Search Agent",
                    files=files,
                    response_data=agent_response_data.get("data", []),
                    analysis=None,
                    orders=agent_response_data.get("orders", []),
                    user_info=agent_response_data.get("user_info", {}),
                    products=agent_response_data.get("data", []),
                    extracted_product_ids=None
                )
                
                return {
                    "response": agent_response_data["text"],
                    "agent_used": "Search Agent",
                    "analysis": None,
                    "clarified_message": None,
                    "context_summary": None,
                    "message_to_agent": None,
                    "session_id": session_id,
                    "files_processed": len(files),
                    "data": agent_response_data.get("data", []),
                    "user_info": agent_response_data.get("user_info", {}),
                    "orders": agent_response_data.get("orders", []),
                    "extracted_product_ids": None
                }
            else:
                # Nếu không có files, fallback về process_message thông thường
                logger.info("📝 Không có files, chuyển sang xử lý message thông thường")
                return await self.process_message(message, user_id, session_id)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý message với files: {e}")
            return {
                "response": f"Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn: {str(e)}",
                "agent_used": None,
                "analysis": "Error occurred",
                "session_id": session_id,
                "files_processed": 0
            }

    def parse_agent_response(self, response: str) -> dict:
        """
        Parse agent response để tách text và data
        Args:
            response: Response từ agent
        Returns:
            Dict chứa text và data
        """
        # Tìm data marker
        data_pattern = r'\[DATA_MARKER\](.*?)\[/DATA_MARKER\]'
        data_match = re.search(data_pattern, response, re.DOTALL)
        
        if data_match:
            # Tách text và data
            text_content = response.replace(data_match.group(0), '').strip()
            try:
                data_content = json.loads(data_match.group(1))
            except json.JSONDecodeError:
                data_content = None
            
            return {
                "text": text_content,
                "data": data_content,
                "has_data": True
            }
        else:
            return {
                "text": response,
                "data": None,
                "has_data": False
            }

    async def _save_messages_to_memory(
        self, 
        user_message: str, 
        ai_response: str, 
        user_id: Optional[str], 
        session_id: str, 
        clarified_message: Optional[str] = None,
        files: Optional[List[Any]] = None
    ):
        """Helper method để lưu messages vào LangChain memory và MySQL"""
        # Convert user_id to int for MySQL (safe conversion)
        mysql_user_id = None
        if user_id:
            try:
                mysql_user_id = int(user_id)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Invalid user_id format: {user_id}, treating as None")
        
        # Save to LangChain Memory (existing logic)
        if session_id and self.memory_manager:
            try:
                # Tạo user message content bao gồm thông tin về files
                user_message_content = user_message
                if files:
                    file_names = [f.name for f in files]
                    user_message_content += f" [Đính kèm: {', '.join(file_names)}]"
                
                # Lưu user message (sử dụng clarified message nếu có)
                message_to_save = clarified_message if clarified_message else user_message_content
                await self.memory_manager.add_user_message(session_id, message_to_save, user_id)
                
                # Lưu AI response
                await self.memory_manager.add_ai_message(session_id, ai_response, user_id)
                
                logger.debug(f"💾 Đã lưu messages vào LangChain memory cho session {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi lưu messages vào LangChain memory: {e}")
                # Fallback to old method
                await self._save_user_message_to_history_fallback(user_message, clarified_message or user_message, user_id, session_id, files)
        
        # Save to MySQL (new real-time logging)
        if self.mysql_history and session_id:
            try:
                # Prepare file names for metadata
                file_names = [f.name for f in files] if files else None
                
                # Save user message
                await self.mysql_history.save_user_message(
                    session_id=session_id,
                    message_content=user_message,
                    user_id=mysql_user_id,
                    clarified_content=clarified_message,
                    files=file_names
                )
                
                # Save AI response (determine agent name from context)
                # Default to Host Agent if no specific agent was used
                agent_name = "Host Agent"  # Will be updated below if agent was used
                
                await self.mysql_history.save_agent_message(
                    session_id=session_id,
                    message_content=ai_response,
                    agent_name=agent_name,
                    user_id=mysql_user_id
                )
                
                logger.debug(f"💾 Đã lưu messages vào MySQL cho session {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi lưu messages vào MySQL: {e}")
                # MySQL failure không block user experience

    def _convert_decimal_to_serializable(self, obj: Any) -> Any:
        """
        Convert Decimal objects to float/int để tránh JSON serialization errors
        
        Args:
            obj: Object cần convert (có thể là dict, list, hoặc primitive)
            
        Returns:
            Object đã được convert với Decimal → float/int
        """
        from decimal import Decimal
        
        if isinstance(obj, Decimal):
            # Convert Decimal to float, hoặc int nếu là số nguyên
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        elif isinstance(obj, dict):
            # Recursively convert dict
            return {key: self._convert_decimal_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            # Recursively convert list
            return [self._convert_decimal_to_serializable(item) for item in obj]
        else:
            # Return as-is for other types
            return obj

    async def _enrich_products_with_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich products với thông tin đầy đủ từ database (images, prices, descriptions, etc.)
        
        Args:
            products: Danh sách products từ agent response
            
        Returns:
            Danh sách products đã được enriched với thông tin đầy đủ từ database
        """
        if not products or len(products) == 0:
            return products
            
        try:
            # Extract product IDs từ products list
            product_ids = []
            for product in products:
                if isinstance(product, dict):
                    # Thử các field có thể chứa ID
                    product_id = product.get('product_id') or product.get('id') or product.get('ID')
                    if product_id:
                        product_ids.append(str(product_id))
            
            if not product_ids:
                logger.debug("⚠️ Không tìm thấy product IDs trong products list")
                return products
            
            logger.debug(f"🔍 Đang enrich {len(product_ids)} products với thông tin đầy đủ từ database")
            
            # Query database để lấy thông tin đầy đủ
            db_products = self.db_connector.get_products_by_ids(product_ids)
            
            # Tạo mapping từ product ID tới thông tin database
            db_data_mapping = {}
            for db_product in db_products:
                if db_product and db_product.get('id'):
                    product_id = str(db_product['id'])
                    db_data_mapping[product_id] = db_product
            
            logger.debug(f"💾 Đã lấy được thông tin database cho {len(db_data_mapping)} products")
            
            # Enrich products với thông tin đầy đủ từ database
            enriched_products = []
            for product in products:
                if isinstance(product, dict):
                    enriched_product = product.copy()
                    
                    # Lấy product ID
                    product_id = product.get('product_id') or product.get('id') or product.get('ID')
                    if product_id:
                        product_id_str = str(product_id)
                        
                        # Merge thông tin từ database nếu có
                        if product_id_str in db_data_mapping:
                            db_data = db_data_mapping[product_id_str]
                            
                            # Chuẩn hóa product_id field
                            enriched_product['product_id'] = product_id_str
                            
                            # Merge các field từ database (chỉ thêm nếu chưa có hoặc empty)
                            db_fields_mapping = {
                                'price': db_data.get('price'),
                                'newPrice': db_data.get('newPrice'), 
                                'image_url': db_data.get('image_url'),
                                'images': db_data.get('images'),
                                'description': db_data.get('description'),
                                'brand': db_data.get('brand'),
                                'category': db_data.get('category'),
                                'color': db_data.get('color'),
                                'gender': db_data.get('gender'),
                                'frameMaterial': db_data.get('frameMaterial'),
                                'frameShape': db_data.get('frameShape'),
                                'rating': db_data.get('rating'),
                                'stock': db_data.get('stock'),
                                'availability': db_data.get('availability'),
                                'weight': db_data.get('weight'),
                                'quantity': db_data.get('quantity'),
                                'trending': db_data.get('trending'),
                                'lensMaterial': db_data.get('lensMaterial'),
                                'lensFeatures': db_data.get('lensFeatures'),
                                'lensWidth': db_data.get('lensWidth'),
                                'bridgeWidth': db_data.get('bridgeWidth'),
                                'templeLength': db_data.get('templeLength')
                            }
                            
                            # Merge fields - ưu tiên data từ agent, fallback sang database
                            for field, db_value in db_fields_mapping.items():
                                if db_value is not None:
                                    # Convert Decimal to serializable types
                                    db_value = self._convert_decimal_to_serializable(db_value)
                                    
                                    # Nếu field chưa có hoặc empty trong product data từ agent
                                    if (field not in enriched_product or 
                                        enriched_product.get(field) is None or 
                                        enriched_product.get(field) == ""):
                                        enriched_product[field] = db_value
                            
                            logger.debug(f"✅ Enriched product {product_id_str} với thông tin từ database")
                        else:
                            logger.debug(f"⚠️ Không tìm thấy thông tin database cho product {product_id_str}")
                    
                    enriched_products.append(enriched_product)
                else:
                    # Nếu không phải dict, giữ nguyên
                    enriched_products.append(product)
            
            logger.debug(f"🎯 Đã enrich xong {len(enriched_products)} products với thông tin đầy đủ")
            return enriched_products
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi enrich products với thông tin database: {e}")
            # Return original products nếu có lỗi
            return products

    async def _save_messages_to_memory_with_agent(
        self, 
        user_message: str, 
        ai_response: str, 
        user_id: Optional[str], 
        session_id: str, 
        agent_name: str,
        clarified_message: Optional[str] = None,
        files: Optional[List[Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        analysis: Optional[str] = None,
        orders: Optional[List[Dict[str, Any]]] = None,
        user_info: Optional[Dict[str, Any]] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        extracted_product_ids: Optional[List[str]] = None
    ):
        """Enhanced method để lưu messages với agent information và đầy đủ thông tin list"""
        # Convert user_id to int for MySQL (safe conversion)
        mysql_user_id = None
        if user_id:
            try:
                mysql_user_id = int(user_id)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Invalid user_id format: {user_id}, treating as None")
        
        # Save to LangChain Memory (existing logic)
        if session_id and self.memory_manager:
            try:
                # Tạo user message content bao gồm thông tin về files
                user_message_content = user_message
                if files:
                    file_names = [f.name for f in files]
                    user_message_content += f" [Đính kèm: {', '.join(file_names)}]"
                
                # Lưu user message (sử dụng clarified message nếu có)
                message_to_save = clarified_message if clarified_message else user_message_content
                await self.memory_manager.add_user_message(session_id, message_to_save, user_id)
                
                # Lưu AI response với agent information
                ai_message_content = ai_response
                if agent_name and agent_name != "Host Agent":
                    ai_message_content = f"[{agent_name}] {ai_response}"
                
                await self.memory_manager.add_ai_message(session_id, ai_message_content, user_id)
                
                logger.debug(f"💾 Đã lưu messages vào LangChain memory cho session {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi lưu messages vào LangChain memory: {e}")
                # Fallback to old method
                await self._save_user_message_to_history_fallback(user_message, clarified_message or user_message, user_id, session_id, files)
        
        # Save to MySQL với đầy đủ thông tin về orders, products, user_info
        if self.mysql_history and session_id:
            try:
                # Prepare file names for metadata
                file_names = [f.name for f in files] if files else None
                
                # ✅ Enrich products với thông tin đầy đủ từ database trước khi lưu
                enriched_products = products
                if products and len(products) > 0:
                    enriched_products = await self._enrich_products_with_images(products)
                    # Convert any remaining Decimal types để đảm bảo JSON serializable
                    enriched_products = self._convert_decimal_to_serializable(enriched_products)
                    logger.debug(f"🎯 Đã enrich {len(enriched_products)} products với thông tin đầy đủ từ database")
                
                # ✅ Convert Decimal types trong tất cả metadata để tránh JSON serialization errors
                safe_orders = self._convert_decimal_to_serializable(orders) if orders else orders
                safe_user_info = self._convert_decimal_to_serializable(user_info) if user_info else user_info
                safe_response_data = self._convert_decimal_to_serializable(response_data) if response_data else response_data
                
                # Save user message
                await self.mysql_history.save_user_message(
                    session_id=session_id,
                    message_content=user_message,
                    user_id=mysql_user_id,
                    clarified_content=clarified_message,
                    files=file_names
                )
                
                # Save AI response với đầy đủ thông tin list (sử dụng enriched_products)
                await self.mysql_history.save_agent_message(
                    session_id=session_id,
                    message_content=ai_response,
                    agent_name=agent_name,
                    user_id=mysql_user_id,
                    response_data=safe_response_data,
                    analysis=analysis,
                    orders=safe_orders,
                    user_info=safe_user_info,
                    products=enriched_products,  # ✅ Sử dụng enriched products với image URLs
                    extracted_product_ids=extracted_product_ids
                )
                
                logger.debug(f"💾 Đã lưu messages vào MySQL cho session {session_id} (agent: {agent_name}) với thông tin đầy đủ")
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi lưu messages vào MySQL: {e}")
                # MySQL failure không block user experience

    async def _save_user_message_to_history_fallback(self, original_message: str, clarified_message: str, user_id: Optional[str], session_id: str, files: Optional[List[Any]] = None):
        """Fallback method để lưu tin nhắn gốc và clarified message vào chat history cũ"""
        if not session_id:
            return
            
        if user_id:
            chat_history = await self.a2a_client_manager._ensure_chat_history_with_redis(user_id, session_id)
        else:
            self.a2a_client_manager._ensure_chat_history(session_id)
            chat_history = self.a2a_client_manager.get_chat_history_fallback(session_id)
        
        # Tạo original message content bao gồm thông tin về files
        original_message_content = original_message
        if files:
            file_names = [f.name for f in files]
            original_message_content += f" [Đính kèm: {', '.join(file_names)}]"
        
        # Lưu tin nhắn gốc trước
        chat_history.add_message(
            role="user", 
            content=original_message_content, 
            clarified_content=clarified_message, 
            agent_used=None, 
            user_id=user_id
        )
        
        # Lưu vào Redis nếu có user_id
        if user_id:
            await self.a2a_client_manager._save_chat_history_to_redis(user_id, session_id, chat_history)
        
        return chat_history

    async def _parse_orchestrator_response(self, response: str) -> Dict[str, Any]:
        """Parse response từ orchestrator để extract decision"""
        try:
            import json
            import re
            
            # Tìm JSON trong response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    "analysis": "Unable to parse orchestrator response",
                    "selected_agent": None,
                    "direct_response": response
                }
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi parse orchestrator response: {e}")
            return {
                "analysis": "Parse error",
                "selected_agent": None,
                "direct_response": response
            }

    async def send_message_to_agent(self, agent_name: str, message: str, user_id: Optional[str] = None, session_id: Optional[str] = None, files: Optional[List[Any]] = None) -> str:
        """
        Gửi message tới agent cụ thể qua A2A (wrapper method)
        """
        return await self.a2a_client_manager.send_message_to_agent(agent_name, message, user_id, session_id, files)

    async def check_agents_health(self) -> Dict[str, bool]:
        """Kiểm tra health của tất cả agents"""
        health_status = await self.a2a_client_manager.health_check_all()
        return {name: status["healthy"] for name, status in health_status.items()}

    async def get_all_agents_status(self) -> Dict[str, Any]:
        """Lấy status chi tiết của tất cả agents"""
        return await self.a2a_client_manager.health_check_all()

    def _normalize_chat_history(self, messages_data: Any) -> List[Dict[str, Any]]:
        """Chuẩn hóa chat history thành format chuẩn"""
        normalized_messages = []
        
        try:
            # Nếu là list of LangChain BaseMessage objects
            if isinstance(messages_data, list) and len(messages_data) > 0:
                from langchain.schema import HumanMessage, AIMessage
                import re
                
                for msg in messages_data:
                    if isinstance(msg, HumanMessage):
                        normalized_messages.append({
                            "role": "user",
                            "content": msg.content,
                            "timestamp": datetime.now().isoformat(),
                            "agent_used": None,
                            "user_id": None
                        })
                    elif isinstance(msg, AIMessage):
                        # Extract agent name từ content nếu có format [Agent Name]
                        content = msg.content
                        agent_used = None
                        
                        # Tìm pattern [Agent Name] ở đầu message
                        agent_match = re.match(r'^\[([^\]]+)\]\s*(.*)$', content, re.DOTALL)
                        if agent_match:
                            agent_used = agent_match.group(1)
                            content = agent_match.group(2)
                        
                        normalized_messages.append({
                            "role": "assistant", 
                            "content": content,
                            "timestamp": datetime.now().isoformat(),
                            "agent_used": agent_used,
                            "user_id": None
                        })
                        
            # Nếu là ChatHistory object
            elif hasattr(messages_data, 'messages'):
                normalized_messages = messages_data.messages
                
            # Nếu đã là list of dict (format chuẩn)
            elif isinstance(messages_data, list):
                normalized_messages = messages_data
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi chuẩn hóa chat history: {e}")
            normalized_messages = []
            
        return normalized_messages

    async def get_chat_history(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Lấy chat history cho session (ưu tiên LangChain memory) - format chuẩn"""
        try:
            if self.memory_manager:
                try:
                    memory = await self.memory_manager.get_memory(session_id, user_id)
                    messages = memory.chat_memory.messages
                    return self._normalize_chat_history(messages)
                except Exception as e:
                    logger.warning(f"⚠️ Lỗi khi lấy history từ LangChain memory: {e}")
            
            # Fallback to old method
            chat_history = await self.a2a_client_manager.get_chat_history(user_id, session_id)
            return self._normalize_chat_history(chat_history)
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy chat history: {e}")
            return []
    
    def get_chat_history_fallback(self, session_id: str) -> List[Dict[str, Any]]:
        """Lấy chat history từ memory (cho backward compatibility) - format chuẩn"""
        try:
            chat_history = self.a2a_client_manager.get_chat_history_fallback(session_id)
            return self._normalize_chat_history(chat_history)
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy chat history fallback: {e}")
            return []

    async def clear_chat_history(self, user_id: str, session_id: str):
        """Xóa chat history cho session (ưu tiên LangChain memory)"""
        if self.memory_manager:
            try:
                await self.memory_manager.clear_memory(session_id, user_id)
                logger.info(f"🗑️ Đã xóa LangChain memory cho session {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi xóa LangChain memory: {e}")
        
        # Also clear old method for cleanup
        await self.a2a_client_manager.clear_chat_history(user_id, session_id)
    
    def clear_chat_history_fallback(self, session_id: str):
        """Xóa chat history từ memory (cho backward compatibility)"""
        self.a2a_client_manager.clear_chat_history_fallback(session_id)
    
    async def get_user_sessions(self, user_id: str):
        """Lấy danh sách tất cả sessions của user (ưu tiên LangChain memory)"""
        if self.memory_manager:
            try:
                sessions = await self.memory_manager.get_all_user_sessions(user_id)
                if sessions:
                    return sessions
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi lấy sessions từ LangChain memory: {e}")
        
        # Fallback to old method
        return await self.a2a_client_manager.get_user_sessions(user_id)

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.a2a_client_manager.cleanup()
            
            # Cleanup MySQL connections
            if self.mysql_history:
                await self.mysql_history.cleanup()
            
            # Database Connector (singleton) sẽ được cleanup bởi main.py
            # Không close connection ở đây để tránh ảnh hưởng đến các component khác
            logger.info("✅ Database Connector (singleton) will be cleaned up by main.py")
            
            logger.info("✅ Host Server cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
