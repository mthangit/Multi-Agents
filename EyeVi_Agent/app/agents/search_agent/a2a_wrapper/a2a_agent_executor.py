import logging
import asyncio
import base64
import json
from typing import Optional, Dict, Any, List, Tuple

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TaskState,
    TextPart,
    FilePart,
    DataPart,
    Message,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
    new_data_artifact
)
from a2a.utils.errors import ServerError

from agent.agent import SearchAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgentExecutor(AgentExecutor):
    """Search Agent Executor for handling A2A tasks and messages."""

    def __init__(self):
        """Initialize the SearchAgentExecutor."""
        self.agent = SearchAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the search agent task."""
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
            # Trích xuất dữ liệu từ message
            query, image_data, analysis_result = self._extract_message_parts(context.message)
            
            # Process the search request
            result = await self.agent.search(
                query=query,
                image_data=image_data,
                analysis_result=analysis_result
            )

            # Format the response as text
            formatted_result = self._format_search_result(result)
            
            data_part = DataPart(data=result)
            text_part = TextPart(text=formatted_result)
            # Create parts for the task artifact (full result)
            parts = [Part(root=data_part), Part(root=text_part)]

            # Update task status and complete
            await updater.add_artifact(parts, name="search_result")
            
            # Send formatted text response to the user
            # await event_queue.enqueue_event(new_agent_text_message(
            #     text=formatted_result,
            #     context_id=context.context_id,
            #     task_id=context.task_id,
            # ))
            
            await event_queue.enqueue_event(
                task
            )
            
            await updater.complete()

        except Exception as e:
            logger.error(f"Error executing search task: {e}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        raise ServerError(error=UnsupportedOperationError())

    def _parse_search_query(self, query: str) -> Dict[str, Any]:
        """Parse search query to extract search parameters."""
        search_params = {
            "query": query,
            "image_data": None,
            "analysis_result": None
        }
        
        # Try to detect if query contains base64 encoded image
        try:
            # Look for patterns that might indicate image data
            if "base64," in query:
                # Extract base64 image data
                base64_start = query.find("base64,") + 7
                base64_data = query[base64_start:].strip()
                
                # Try to decode the base64 data
                image_data = base64.b64decode(base64_data)
                search_params["image_data"] = image_data
                
                # Remove image data from text query
                search_params["query"] = query[:query.find("base64,")].strip()
                
                logger.info("Detected image data in query")
                
        except Exception as e:
            logger.debug(f"No valid image data found in query: {e}")
        
        # Try to detect analysis result in query (JSON format)
        try:
            if "{" in query and "}" in query:
                # Try to extract JSON from query
                json_start = query.find("{")
                json_end = query.rfind("}") + 1
                json_str = query[json_start:json_end]
                
                analysis_result = json.loads(json_str)
                search_params["analysis_result"] = analysis_result
                
                # Remove JSON from text query
                search_params["query"] = (query[:json_start] + query[json_end:]).strip()
                
                logger.info("Detected analysis result in query")
                
        except Exception as e:
            logger.debug(f"No valid analysis result found in query: {e}")
        
        return search_params

    async def _process_search_async(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process search using the search agent asynchronously."""
        try:
            # Run the search method in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.agent.search_sync(
                    query=search_params.get("query"),
                    image_data=search_params.get("image_data"),
                    analysis_result=search_params.get("analysis_result")
                )
            )
            return result
        except Exception as e:
            logger.error(f"Error in async search processing: {e}")
            return {
                "error": str(e),
                "products": [],
                "count": 0,
                "summary": "Xin lỗi, tôi gặp lỗi khi tìm kiếm sản phẩm."
            }

    def _format_search_result(self, result: Dict[str, Any]) -> str:
        """Format search results for display."""
        try:
            if result.get("error"):
                return f"❌ Lỗi tìm kiếm: {result['error']}"
            
            # Ưu tiên sử dụng câu trả lời từ LLM nếu có
            if result.get("llm_response"):
                return result["llm_response"]
            
            # Nếu không có câu trả lời từ LLM, sử dụng định dạng cũ
            products = result.get("products", [])
            count = result.get("count", len(products))
            summary = result.get("summary", "")
            
            if not products:
                return "🔍 Không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn."
            
            # Format the response
            response_parts = []
            
            if summary:
                response_parts.append(f"📋 **Tóm tắt tìm kiếm:**\n{summary}")
            
            response_parts.append(f"\n🎯 **Tìm thấy {count} sản phẩm phù hợp:**")
            
            for i, product in enumerate(products[:5], 1):  # Show top 5 products
                product_info = f"\n**{i}. {product.get('name', 'Sản phẩm không tên')}**"
                
                if product.get('brand'):
                    product_info += f"\n   🏷️ Thương hiệu: {product['brand']}"
                
                if product.get('price'):
                    product_info += f"\n   💰 Giá: {product['price']}"
                
                if product.get('description'):
                    desc = product['description'][:100] + "..." if len(product['description']) > 100 else product['description']
                    product_info += f"\n   📝 Mô tả: {desc}"
                
                if product.get('score'):
                    product_info += f"\n   ⭐ Độ phù hợp: {product['score']:.2f}"
                
                if product.get('category'):
                    product_info += f"\n   📂 Danh mục: {product['category']}"
                
                response_parts.append(product_info)
            
            if count > 5:
                response_parts.append(f"\n📌 Và {count - 5} sản phẩm khác...")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting search result: {e}")
            return f"✅ Tìm thấy {len(result.get('products', []))} sản phẩm nhưng gặp lỗi khi định dạng kết quả."

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the incoming request context."""
        if not context.message:
            return True
        return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the search agent."""
        try:
            health_info = {
                "agent_type": "search_clip",
                "status": "healthy",
                "search_agent_available": self.agent is not None,
                "active_tasks": 0
            }
            
            if self.agent:
                try:
                    # Test basic functionality
                    test_result = self.agent.search_sync(query="test")
                    health_info["search_functionality"] = "working" if not test_result.get("error") else "error"
                    health_info["qdrant_status"] = "connected"
                    health_info["clip_model_status"] = "loaded"
                except Exception as e:
                    health_info["search_functionality"] = "error"
                    health_info["error_details"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "agent_type": "search_clip",
                "status": "error",
                "error": str(e),
                "search_agent_available": False,
                "active_tasks": 0
            }

    def _extract_message_parts(self, message: Message) -> Tuple[Optional[str], Optional[bytes], Optional[Dict]]:
        """Trích xuất query text, image data và analysis result từ message parts.
        
        Args:
            message: Message từ client
            
        Returns:
            Tuple chứa (query_text, image_data, analysis_result)
        """
        query_text = None
        image_data = None
        analysis_result = None
        
        for part in message.parts:
            if hasattr(part, 'root'):
                part_root = part.root
                
                # TextPart - Xử lý phần văn bản
                if isinstance(part_root, TextPart):
                    query_text = part_root.text
                    logger.info(f"Extracted text query: {query_text[:50]}...")
                
                # FilePart - Xử lý phần file (ảnh)
                elif isinstance(part_root, FilePart) and part_root.file.mimeType.startswith("image/"):
                    try:
                        # Decode base64 image data
                        if part_root.file.bytes:
                            image_data = base64.b64decode(part_root.file.bytes)
                            logger.info(f"Extracted image data: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Error decoding image data: {str(e)}")
                
                # DataPart - Xử lý phần dữ liệu cấu trúc
                elif isinstance(part_root, DataPart):
                    analysis_result = part_root.data
                    logger.info(f"Extracted analysis result: {analysis_result}")
        
        return query_text, image_data, analysis_result 