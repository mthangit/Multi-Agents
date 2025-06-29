import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
    DataPart,
)
from a2a.utils.errors import ServerError
from a2a.utils import new_agent_text_message, new_task
# Import simplified agent mới
from src.chatbot.simplified_order_agent import SimplifiedOrderAgent
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OrderAgentExecutor(AgentExecutor):
    """Executor cho Order Agent với support cho các loại agent khác nhau"""
    
    def __init__(self, agent_type: str = "simplified"):
        """
        Khởi tạo executor
        
        Args:
            agent_type: Loại agent sử dụng
                - "simplified": Simplified Order Agent (mới, đơn giản)
                - "simple": Simple LangGraph Agent (cũ)
                - "streaming": Simplified Bot (streaming)
        """
        self.agent_type = agent_type
        
        if agent_type == "simplified":
            logger.info("🚀 Sử dụng Simplified Order Agent (LangGraph đơn giản)")
            self.agent = SimplifiedOrderAgent()
        
        logger.info(f"✅ Order Agent Executor đã sẵn sàng với agent type: {agent_type}")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the order agent task, handling different agent types."""
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        query = context.get_user_input()
        logger.info(f"🔍 Xử lý query: {query}")

        try:
            # Sử dụng Simplified Order Agent mới
            async def execute_simplified_task():
                logger.info("💬 Gọi simplified order agent...")
                response = self.agent.chat(query, user_id=1)
                
                text_part = TextPart(text=response.get("llm_response", ""))
                data_part = DataPart(data=response)
                parts = [Part(root=text_part), Part(root=data_part)]
                
                await updater.add_artifact(parts, name="order_result")
                
                # Send formatted text response to the user
                # await event_queue.enqueue_event(new_agent_text_message(
                #     text=response,
                #     context_id=context.context_id,
                #     task_id=context.task_id,
                # ))
                
                await event_queue.enqueue_event(task)
                
                await updater.complete()
                logger.info("✅ Hoàn thành task với simplified agent")
            
            await asyncio.wait_for(execute_simplified_task(), timeout=300.0)
                                
            logger.info(f"✅ Successfully completed task {context.task_id}")

        except asyncio.TimeoutError:
            logger.error(f"❌ Order agent task timed out for query: {query}")
            try:
                await updater.fail(message="⏰ Yêu cầu bị timeout. Vui lòng thử lại.")
            except Exception as fail_error:
                logger.error(f"Error calling updater.fail: {fail_error}")
            raise ServerError(error=InternalError()) from Exception("Task timeout")
        except Exception as e:
            logger.error(f"❌ Error executing order task: {e}", exc_info=True)
            try:
                await updater.fail(message=f"❌ Có lỗi xảy ra: {str(e)}")
            except Exception as fail_error:
                logger.error(f"Error calling updater.fail: {fail_error}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        logger.info(f"Cancel requested for task {context.task_id}")
        raise ServerError(error=UnsupportedOperationError())

    def get_health_status(self) -> Dict[str, Any]:
        """Lấy trạng thái health của agent"""
        try:
            health_info = {
                "agent_type": self.agent_type,
                "status": "healthy",
                "agent_available": self.agent is not None,
                "active_tasks": 0,
                "framework": "A2A",
                "domain": "order_management",
                "timestamp": datetime.now().isoformat()
            }
            
            # Test agent functionality
            if self.agent and self.agent_type == "simplified":
                try:
                    test_response = self.agent.chat("test", user_id=1)
                    health_info["test_functionality"] = "working" if test_response else "error"
                    health_info["gemini_connection"] = "connected"
                except Exception as e:
                    health_info["test_functionality"] = "error"
                    health_info["error_details"] = str(e)
                    health_info["status"] = "unhealthy"
            
            return health_info
            
        except Exception as e:
            return {
                "agent_type": self.agent_type,
                "status": "error", 
                "error": str(e),
                "agent_available": False,
                "active_tasks": 0,
                "timestamp": datetime.now().isoformat()
            }

