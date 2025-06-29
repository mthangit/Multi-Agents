import asyncio
import json
import uuid
from typing import Any, Dict, List
from datetime import datetime

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TextPart,
    UnsupportedOperationError
)
from a2a.utils.errors import ServerError
from a2a.utils import new_agent_text_message, new_task
import logging

from agents.rag_agent import RAGAgent
from utils.embedding_manager import EmbeddingManager
from utils.qdrant_manager import QdrantManager
from config import Config

logger = logging.getLogger(__name__)

class AdvisorAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor cho Eyewear Advisor Agent với LangGraph workflow
    Implements proper A2A AgentExecutor interface
    """
    
    def __init__(self):
        print("🚀 Khởi tạo Advisor Agent Executor với LangGraph...")
        
        # Khởi tạo các components
        self.embedding_manager = EmbeddingManager()
        self.qdrant_manager = QdrantManager()
        self.rag_agent = RAGAgent()
        
        # Inject managers vào RAG agent
        self.rag_agent.set_managers(self.embedding_manager, self.qdrant_manager)
        
        print("✅ Advisor Agent Executor đã sẵn sàng!")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute method theo A2A AgentExecutor interface
        Sử dụng LangGraph workflow với invoke
        """
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")


        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            # Get user input from context
            query = context.get_user_input()
            print(f"🔄 Processing query: {query}")
            
            # Process với LangGraph invoke (không streaming)
            start_time = datetime.now()
            result = self.rag_agent.invoke(query)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log processing info
            logger.info(f"✅ Processed query in {processing_time:.2f}s")
            logger.info(f"Intent: {result.get('intent_info', {}).get('query_type', 'unknown')}")
            logger.info(f"Retrieved {result.get('total_retrieved_count', 0)} documents")
            logger.info(f"Used {result.get('relevant_documents_count', 0)} relevant documents")
            
            final_answer = result.get("answer", "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này.")
            sources = result.get("sources", [])
            
            # Prepare metadata
            metadata = {
                "intent_info": result.get("intent_info", {}),
                "confidence_score": result.get("confidence_score", 0.0),
                "relevant_documents_count": result.get("relevant_documents_count", 0),
                "total_retrieved_count": result.get("total_retrieved_count", 0),
                "processing_time": processing_time,
                "sources": sources,
                "status": result.get("status", "completed")
            }
            
            # Convert response to A2A parts
            parts = [Part(root=TextPart(text=final_answer))]
            
            # Add artifact with metadata
            await updater.add_artifact(
                parts, 
                name="consultation_result",
                metadata=metadata
            )
            
            # Complete the task
            await event_queue.enqueue_event(task)
            
            await updater.complete()
            
            logger.info(f"✅ Successfully completed task {context.task_id}")

        except Exception as e:
            error_message = f"Error executing advisor task: {e}"
            logger.error(error_message)
            try:
                await updater.failed(str(e))
            except Exception as fail_error:
                logger.error(f"Error calling updater.fail: {fail_error}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        logger.info(f"Cancel requested for task {context.task_id}")
        raise ServerError(error=UnsupportedOperationError())
    
    async def execute_sync(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute synchronous cho testing/debugging
        """
        try:
            start_time = datetime.now()
            
            # Sử dụng invoke với LangGraph workflow
            result = self.rag_agent.invoke(user_message, context)
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "type": "message",
                "role": "agent", 
                "parts": [
                    {
                        "type": "text",
                        "text": result["answer"]
                    }
                ],
                "messageId": str(uuid.uuid4()),
                "metadata": {
                    "sources": result.get("sources", []),
                    "intent_info": result.get("intent_info", {}),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "relevant_documents_count": result.get("relevant_documents_count", 0),
                    "total_retrieved_count": result.get("total_retrieved_count", 0),
                    "processing_time": total_time,
                    "status": result.get("status", "completed")
                }
            }
            
        except Exception as e:
            return {
                "type": "error",
                "error": f"Lỗi xử lý: {str(e)}",
                "messageId": str(uuid.uuid4())
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Kiểm tra health status của agent
        """
        try:
            # Kiểm tra RAG agent health
            rag_health = self.rag_agent.get_health_status()
            
            # Kiểm tra Qdrant connection
            qdrant_info = self.qdrant_manager.get_collection_info()
            qdrant_healthy = "error" not in qdrant_info
            
            # Kiểm tra embedding manager
            embedding_healthy = self.embedding_manager is not None
            
            overall_status = "healthy" if (
                rag_health.get("status") == "healthy" and 
                qdrant_healthy and 
                embedding_healthy
            ) else "unhealthy"
            
            return {
                "status": overall_status,
                "agent_type": "eyewear_advisor",
                "framework": "A2A",
                "workflow": "LangGraph",
                "components": {
                    "rag_agent": rag_health,
                    "qdrant": {
                        "status": "healthy" if qdrant_healthy else "unhealthy",
                        "info": qdrant_info
                    },
                    "embedding_manager": {
                        "status": "healthy" if embedding_healthy else "unhealthy",
                        "model": getattr(self.embedding_manager, 'model_name', 'unknown') if embedding_healthy else None
                    }
                },
                "capabilities": {
                    "intent_detection": True,
                    "domain_specific": True,
                    "multi_language": True,
                    "document_retrieval": True,
                    "workflow_execution": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Trả về thông tin capabilities của agent
        """
        return {
            "agent_type": "eyewear_advisor", 
            "domain": "optical_eyewear",
            "language": "vietnamese",
            "features": [
                "intent_detection",
                "document_retrieval", 
                "medical_consultation",
                "product_recommendation",
                "style_consultation",
                "technical_advice"
            ],
            "workflow": {
                "type": "LangGraph",
                "streaming": True,
                "nodes": [
                    "detect_intent",
                    "retrieve_documents",
                    "filter_documents", 
                    "aggregate_context",
                    "generate_answer",
                    "post_process"
                ]
            },
            "models": {
                "llm": Config.GEMINI_MODEL,
                "embedding": getattr(Config, 'EMBEDDING_MODEL', 'unknown')
            }
        } 