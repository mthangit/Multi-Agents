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
        
        
        # Tạo prompt template
        prompt_template = PromptTemplate(
            input_variables=["user_message", "available_agents"],
            template=f"""
{ROOT_INSTRUCTION}

**Message từ User:**
{{user_message}}

**Nhiệm vụ của bạn:**
1. Phân tích và làm rõ message của user dựa vào context từ lịch sử hội thoại
2. Viết lại message một cách rõ ràng hơn, thay thế các đại từ chỉ định (đó, này, nó, sản phẩm đó, dịch vụ này, etc.) bằng tên cụ thể
3. Xác định agent nào phù hợp nhất để xử lý yêu cầu đã được làm rõ
4. Trả về response theo format JSON:

{{{{
    "analysis": "Phân tích ngắn gọn về yêu cầu của user",
    "clarified_message": "Message đã được viết lại rõ ràng hơn, thay thế các đại từ bằng tên cụ thể",
    "selected_agent": "Tên agent được chọn (hoặc null nếu có thể trả lời trực tiếp)",
    "message_to_agent": "Message đã được làm rõ để gửi tới agent (nếu có)",
    "direct_response": "Response trực tiếp (nếu không cần agent nào khác)"
}}}}

**Hướng dẫn làm rõ message:**
- Nếu user nói "sản phẩm đó", "cái này", "nó" → thay bằng tên cụ thể từ context
- Nếu user nói "tôi muốn mua nó" → thay bằng "tôi muốn mua [tên sản phẩm cụ thể]"
- Nếu user nói "làm như vậy" → thay bằng hành động cụ thể đã đề cập trước đó
- Nếu user nói "địa chỉ đó" → thay bằng địa chỉ cụ thể từ context
- Luôn đảm bảo clarified_message có thể hiểu được mà không cần context bổ sung

**Lưu ý:**
- Chỉ chọn agent khi thực sự cần thiết
- Nếu có thể trả lời trực tiếp, đặt selected_agent = null
- Message_to_agent phải sử dụng clarified_message và chứa đủ context
- Direct_response chỉ dùng khi không cần agent khác

"""
        )
        
        # Tạo chain
        self.orchestrator_chain = prompt_template | self.llm | StrOutputParser()

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
                
                agent_response_data = self.parse_agent_response(agent_response)
                
                print(f"Agent response: {agent_response}")
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=agent_response_data["text"], 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=clarified_message,
                    agent_name=decision["selected_agent"],
                    response_data=agent_response_data.get("data"),
                    analysis=decision.get("analysis")
                )

                return {    
                    "response": agent_response_data["text"],
                    "agent_used": decision["selected_agent"],
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id,
                    "data": agent_response_data["data"] if agent_response_data["has_data"] else None
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
                    analysis=decision.get("analysis")
                )
                                
                return {
                    "response": direct_response,
                    "agent_used": None,
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id
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
        Xử lý message từ user có kèm files và điều phối tới agent phù hợp
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
            
            # Thêm thông tin về files nếu có
            files_info = ""
            if files:
                file_descriptions = []
                for file_info in files:
                    file_descriptions.append(f"- {file_info.name} ({file_info.mime_type})")
                files_info = f"\nFiles đính kèm:\n" + "\n".join(file_descriptions)
            
            # Gọi orchestrator chain để phân tích
            full_message = message + context_info + files_info
            orchestrator_response = await self.orchestrator_chain.ainvoke({
                "user_message": full_message,
                "available_agents": ", ".join(available_agents)
            })
            
            logger.info(f"🤖 Orchestrator response (with files): {orchestrator_response}")
            
            # Parse response từ orchestrator
            decision = await self._parse_orchestrator_response(orchestrator_response)
            
            # Xử lý theo decision
            clarified_message = decision.get("clarified_message", message)
            
            if decision.get("selected_agent") and decision["selected_agent"] != "null":
                # Gửi message đã được làm rõ tới agent được chọn qua A2A với files
                agent_response = await self.a2a_client_manager.send_message_to_agent(
                    agent_name=decision["selected_agent"],
                    message=decision.get("message_to_agent", clarified_message),
                    user_id=user_id,
                    session_id=session_id,
                    files=files
                )
                
                # Parse agent response để lấy data
                agent_response_data = self.parse_agent_response(agent_response)
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=agent_response_data["text"], 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=clarified_message,
                    agent_name=decision["selected_agent"],
                    files=files,
                    response_data=agent_response_data.get("data"),
                    analysis=decision.get("analysis")
                )
                
                return {
                    "response": agent_response_data["text"],
                    "agent_used": decision["selected_agent"],
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id,
                    "files_processed": len(files) if files else 0,
                    "data": agent_response_data["data"] if agent_response_data["has_data"] else None
                }
            else:
                # Trả lời trực tiếp và lưu vào chat history
                direct_response = decision.get("direct_response", "Xin lỗi, tôi chưa hiểu yêu cầu của bạn.")
                
                # Lưu tin nhắn vào LangChain memory và MySQL
                await self._save_messages_to_memory_with_agent(
                    user_message=message,
                    ai_response=direct_response, 
                    user_id=user_id, 
                    session_id=session_id, 
                    clarified_message=clarified_message,
                    agent_name="Host Agent",
                    files=files,
                    analysis=decision.get("analysis")
                )
                
                return {
                    "response": direct_response,
                    "agent_used": None,
                    "analysis": decision.get("analysis", ""),
                    "clarified_message": clarified_message,
                    "session_id": session_id,
                    "files_processed": len(files) if files else 0
                }
                
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
        analysis: Optional[str] = None
    ):
        """Enhanced method để lưu messages với agent information"""
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
        
        # Save to MySQL với agent information
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
                
                # Save AI response với agent information
                await self.mysql_history.save_agent_message(
                    session_id=session_id,
                    message_content=ai_response,
                    agent_name=agent_name,
                    user_id=mysql_user_id,
                    response_data=response_data,
                    analysis=analysis
                )
                
                logger.debug(f"💾 Đã lưu messages vào MySQL cho session {session_id} (agent: {agent_name})")
                
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

    async def get_chat_history(self, user_id: str, session_id: str):
        """Lấy chat history cho session (ưu tiên LangChain memory)"""
        if self.memory_manager:
            try:
                memory = await self.memory_manager.get_memory(session_id, user_id)
                return memory.chat_memory.messages
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi lấy history từ LangChain memory: {e}")
        
        # Fallback to old method
        return await self.a2a_client_manager.get_chat_history(user_id, session_id)
    
    def get_chat_history_fallback(self, session_id: str):
        """Lấy chat history từ memory (cho backward compatibility)"""
        return self.a2a_client_manager.get_chat_history_fallback(session_id)

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
            
            logger.info("✅ Host Server cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")