import logging
from typing import Any, Dict, List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError

from chatbot import PDFChatbot

logger = logging.getLogger(__name__)

class AdvisorAgentExecutor(AgentExecutor):
    """Advisor Agent Executor for handling A2A tasks and messages."""

    def __init__(self):
        """Initialize the AdvisorAgentExecutor."""
        self.chatbot = PDFChatbot()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the advisor agent task."""
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        try:
            # Get user input from context
            query = context.get_user_input()
            
            # Process the consultation request
            # The .invoke method returns a dictionary, we need the 'answer'
            response_dict = self.chatbot.invoke(query)
            response_text = response_dict.get("answer", "No answer found.")
            
            # Convert response to A2A parts
            parts = [Part(root=TextPart(text=response_text))]

            # Update task status and complete
            await updater.add_artifact(parts, name="consultation_result")
            await updater.complete()

        except Exception as e:
            logger.error(f"Error executing advisor task: {e}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        raise ServerError(error=UnsupportedOperationError()) 