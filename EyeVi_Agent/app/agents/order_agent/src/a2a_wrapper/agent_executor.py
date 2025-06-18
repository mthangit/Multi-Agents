import asyncio
import logging
from typing import Dict

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
)
from a2a.utils.errors import ServerError
from src.chatbot.simplified_bot import simplified_chatbot_instance

logger = logging.getLogger(__name__)


class OrderAgentExecutor(AgentExecutor):
    """Order Agent Executor for handling A2A tasks and messages."""

    def __init__(self):
        """Initialize the OrderAgentExecutor."""
        self.agent = simplified_chatbot_instance

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the order agent task, handling streaming responses."""
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        query = context.get_user_input()

        try:
            async def execute_streaming_task():
                async for item in self.agent.stream(query, context.context_id):
                    is_task_complete = item.get("is_task_complete", False)
                    require_user_input = item.get("require_user_input", False)
                    content = item.get("content", "Processing...")
                    parts = [Part(root=TextPart(text=content))]

                    if is_task_complete:
                        await updater.add_artifact(parts, name="order_result")
                        await updater.complete()
                        break
                    elif require_user_input:
                        await updater.update_status(
                            TaskState.input_required,
                            message=updater.new_agent_message(parts),
                        )
                        break
                    else:
                        await updater.update_status(
                            TaskState.working,
                            message=updater.new_agent_message(parts),
                        )
            
            # Execute with a timeout to prevent indefinite hanging
            await asyncio.wait_for(execute_streaming_task(), timeout=300.0)

        except asyncio.TimeoutError:
            logger.error(f"Order agent task timed out for query: {query}")
            await updater.fail(message="The request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error executing order task: {e}", exc_info=True)
            await updater.fail(message=f"An internal error occurred: {e}")

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        raise ServerError(error=UnsupportedOperationError())