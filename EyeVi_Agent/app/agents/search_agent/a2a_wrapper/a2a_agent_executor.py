import logging
import asyncio
import base64
import json
from typing import Optional, Dict, Any, List

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
    UnsupportedOperationError,
    Message,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
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
            # Get user input from context
            query = context.get_user_input()
            
            # Process the search request
            result = await self.agent.search(
                query=query,
                image_data=None,  # Handle image data if needed
                analysis_result=None  # Handle analysis result if needed
            )

            # Convert result to A2A parts
            parts = [Part(root=TextPart(text=str(result)))]

            # Update task status and complete
            await updater.add_artifact(parts, name="search_result")
            await event_queue.enqueue_event(new_agent_text_message(
                text=result,
                context_id=context.context_id,
                task_id=context.task_id,
            ))
            
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