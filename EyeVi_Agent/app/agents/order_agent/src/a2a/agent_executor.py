import logging
import asyncio
from typing import Optional, Dict, Any

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

from src.chatbot.simplified_bot import simplified_chatbot_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderAgentExecutor(AgentExecutor):
    """Order Management AgentExecutor for A2A system."""

    def __init__(self):
        self.agent = simplified_chatbot_instance
        self._active_tasks: Dict[str, Task] = {}  # Store active tasks for cancellation

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent's logic for a given request context."""
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)
        
        # Store task for potential cancellation
        self._active_tasks[task.id] = task
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            logger.info(f"Starting agent execution for query: {query[:50]}...")
            
            # Set initial task state
            updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Đang xử lý yêu cầu của bạn...",
                    task.contextId,
                    task.id,
                ),
            )
            
            async def execute_with_timeout():
                async for item in self.agent.stream(query, task.contextId):
                    logger.debug(f"Received stream item: {item}")
                    is_task_complete = item['is_task_complete']
                    require_user_input = item['require_user_input']
                    content = item['content']

                    if not is_task_complete and not require_user_input:
                        # Update task status to working and send intermediate message
                        updater.update_status(
                            TaskState.working,
                            new_agent_text_message(
                                content,
                                task.contextId,
                                task.id,
                            ),
                        )
                    elif require_user_input:
                        # Task requires user input
                        updater.update_status(
                            TaskState.input_required,
                            new_agent_text_message(
                                content,
                                task.contextId,
                                task.id,
                            ),
                            final=True,
                        )
                        break
                    else:
                        # Task is complete
                        updater.add_artifact(
                            [Part(root=TextPart(text=content))],
                            name='order_result',
                        )
                        updater.complete()
                        break
            
            # Execute with 30 second timeout
            await asyncio.wait_for(execute_with_timeout(), timeout=300.0)
            logger.info("Agent execution completed successfully")

        except asyncio.TimeoutError:
            logger.error(f'Agent execution timed out after 300 seconds')
            updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    "Xin lỗi, xử lý yêu cầu quá lâu. Vui lòng thử lại.",
                    task.contextId,
                    task.id,
                ),
                final=True,
            )
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}', exc_info=True)
            updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn.",
                    task.contextId,
                    task.id,
                ),
                final=True,
            )
        finally:
            # Clean up task from active tasks
            self._active_tasks.pop(task.id, None)

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the incoming request context."""
        if not context.message:
            return True
        return False

    async def cancel(
        self, 
        context: RequestContext, 
        event_queue: EventQueue
    ) -> Optional[Task]:
        """Cancel an ongoing task."""
        task_id = context.task_id
        if task_id not in self._active_tasks:
            raise ServerError(error=InvalidParamsError("Task not found"))
        
        task = self._active_tasks[task_id]
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        # Update task status to canceled
        updater.update_status(
            TaskState.canceled,
            new_agent_text_message(
                "Yêu cầu đã bị hủy.",
                task.contextId,
                task.id,
            ),
            final=True,
        )
        
        # Clean up
        self._active_tasks.pop(task_id, None)
        return task