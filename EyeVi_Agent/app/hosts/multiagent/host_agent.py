import base64
import json
import uuid

from common.client import A2ACardResolver
from common.types import (
    AgentCard,
    DataPart,
    Message,
    Part,
    Task,
    TaskSendParams,
    TaskState,
    TextPart,
)
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .remote_agent_connection import RemoteAgentConnections, TaskUpdateCallback


class HostAgent:
    """The host agent.

    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        for address in remote_agent_addresses:
            card_resolver = A2ACardResolver(address)
            card = card_resolver.get_agent_card()
            remote_connection = RemoteAgentConnections(card)
            self.remote_agent_connections[card.name] = remote_connection
            self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = '\n'.join(agent_info)

    def register_agent_card(self, card: AgentCard):
        remote_connection = RemoteAgentConnections(card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = '\n'.join(agent_info)

    def create_agent(self) -> Agent:
        return Agent(
            model='gemini-2.0-flash-001',
            name='host_agent',
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                'This agent orchestrates the decomposition of the user request into'
                ' tasks that can be performed by the child agents.'
            ),
            tools=[
                self.list_remote_agents,
                self.send_task,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_state(context)
        return f"""You are a smart Orchestrator Agent for an eyewear recommendation chatbot system. Your role is to analyze user input (text, images, or both) and coordinate tasks with remote agents to provide accurate and helpful responses. Always respond to the user in Vietnamese, ensuring a friendly and professional tone.

                Analysis:
                1. Determine the user's intent from their input:
                - Search: Requests related to finding eyewear products (e.g., "Find glasses for a round face" or uploading an image).
                - Order: Requests related to purchasing or managing orders (e.g., "Buy rectangular glasses").
                - FAQ: General questions or inquiries (e.g., "What is your return policy?").
                2. If the user provides an image:
                - Check if the image contains a human face.
                - If a face is detected:
                    - Identify the skin tone (light, medium, dark).
                    - Identify the face shape (round, oval, square, heart, diamond, long).
                    - Suggest 2–3 suitable eyeglass frame shapes (e.g., rectangle, square, cat-eye, round).
                    - If the person is wearing glasses, describe:
                    - Frame shape (e.g., square, round).
                    - Color (e.g., blue, black).
                    - Style (e.g., minimalist, bold, fashion, sporty).
                - Generate an analysis result in the following JSON format:
                    {
                    "face_detected": <true|false>,
                    "glasses_detected": <true|false>,
                    "skin_tone": "<light|medium|dark>",
                    "face_shape": "<round|oval|square|heart|diamond|long>",
                    "recommended_frame_shapes": ["<shape1>", "<shape2>", "<shape3>"],
                    "glasses_observed": {
                        "frame_shape": "<shape>",
                        "color": "<color>",
                        "style": "<minimalist|bold|fashion|sporty>"
                    },
                    "summary": "<A concise summary of the analysis, including face shape, skin tone, and frame recommendations>"
                    }

                Discovery:
                - Use `list_remote_agents` to identify available remote agents (e.g., search_agent, order_management_agent, faq_agent) for task delegation.

                Execution:
                - Based on the user's intent and analysis:
                - For search intent, delegate to search_agent with relevant details (e.g., "Find rectangle and square glasses for an oval face" or the JSON analysis result).
                - For order intent, delegate to order_management_agent (e.g., "Create an order for rectangular glasses").
                - For FAQ intent, delegate to faq_agent (e.g., "Answer a question about return policy").
                - Use `send_task` to assign tasks to the appropriate remote agent, including necessary information such as text descriptions or JSON analysis results.
                - Monitor task states using `check_pending_task_states` to track progress and handle responses.

                Guidelines:
                - If the user's intent is unclear, politely ask for clarification in Vietnamese (e.g., "Bạn muốn tìm kính, đặt hàng, hay hỏi thông tin khác?").
                - Rely on tools and remote agents for accurate responses; do not fabricate information.
                - Focus on the most recent user input to ensure relevance.
                - If an active agent is handling a task, send updates to that agent using the appropriate tool.
                - Summarize and present results to the user in a natural, user-friendly manner in Vietnamese.

                Available Agents:
                {self.agents}

                Current Active Agent:
                {current_agent['active_agent']}
                """

    def check_state(self, context: ReadonlyContext):
        state = context.state
        if (
            'session_id' in state
            and 'session_active' in state
            and state['session_active']
            and 'agent' in state
        ):
            return {'active_agent': f'{state["agent"]}'}
        return {'active_agent': 'None'}

    def before_model_callback(
        self, callback_context: CallbackContext, llm_request
    ):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

        # Lưu kết quả phân tích ảnh (nếu có) từ lần gọi trước
        if 'analysis_result' in callback_context.input_data:
            state['last_analysis_result'] = callback_context.input_data['analysis_result']

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

    async def send_task(
        self,
        agent_name: str,
        message: str,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[dict] = None,
        tool_context: ToolContext = None,
    ):
        """Sends a task either streaming (if supported) or non-streaming to a remote agent.

        Args:
            agent_name: The name of the agent to send the task to.
            message: The message to send to the agent for the task.
            image_data: Optional image bytes to send (if the agent needs to process the image).
            analysis_result: Optional JSON result from image analysis (if already processed by Orchestrator).
            tool_context: The tool context this method runs in.

        Returns:
            A list of processed response parts, formatted for user-friendly output in Vietnamese.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        state = tool_context.state
        state['agent'] = agent_name
        client = self.remote_agent_connections[agent_name]
        taskId = state.get('task_id', str(uuid.uuid4()))
        sessionId = state['session_id']

        # Prepare message parts
        parts = [TextPart(text=message)]
        if image_data:
            parts.append(
                FilePart(
                    file=types.File(
                        name="user_image.jpg",
                        mimeType="image/jpeg",
                        bytes=base64.b64encode(image_data).decode('utf-8')
                    )
                )
            )
        if analysis_result:
            parts.append(DataPart(data=analysis_result))

        # Create task request
        metadata = {'conversation_id': sessionId, 'message_id': str(uuid.uuid4())}
        request = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=Message(
                role='user',
                parts=parts,
                metadata=metadata,
            ),
            acceptedOutputModes=['text', 'text/plain', 'image/png', 'application/json'],
            metadata={'conversation_id': sessionId},
        )

        # Send task and handle streaming
        task = await client.send_task(request, self.task_callback)
        state['session_active'] = task.status.state not in [
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.FAILED,
            TaskState.UNKNOWN,
        ]

        # Handle task status
        if task.status.state == TaskState.INPUT_REQUIRED:
            tool_context.actions.skip_summarization = True
            tool_context.actions.escalate = True
            return ["Vui lòng cung cấp thêm thông tin để tiếp tục."]
        elif task.status.state == TaskState.CANCELED:
            raise ValueError(f'Nhiệm vụ của agent {agent_name} đã bị hủy.')
        elif task.status.state == TaskState.FAILED:
            raise ValueError(f'Nhiệm vụ của agent {agent_name} thất bại.')

        # Process response
        response = []
        if task.status.message:
            response.extend(convert_parts(task.status.message.parts, tool_context))
        if task.artifacts:
            for artifact in task.artifacts:
                response.extend(convert_parts(artifact.parts, tool_context))

        # Format response in Vietnamese
        formatted_response = self._format_response(response, agent_name, analysis_result)
        return formatted_response

    def _format_response(self, response: list, agent_name: str, analysis_result: Optional[dict]) -> list:
        """Formats the response in Vietnamese based on the agent and analysis result."""
        formatted = []
        for item in response:
            if isinstance(item, dict) and agent_name == "search_agent":
                # Handle search_agent response (e.g., product list)
                summary = item.get('summary', '')
                formatted.append(f"Dựa trên yêu cầu của bạn, đây là gợi ý: {summary}")
            elif isinstance(item, dict) and agent_name == "order_management_agent":
                # Handle order_management_agent response
                formatted.append(f"Đơn hàng của bạn đã được xử lý: {item.get('order_details', '')}")
            elif isinstance(item, dict) and agent_name == "faq_agent":
                # Handle faq_agent response
                formatted.append(f"Câu trả lời cho câu hỏi của bạn: {item.get('answer', '')}")
            elif isinstance(item, str):
                # Handle text response
                formatted.append(item)
            else:
                formatted.append("Kết quả không rõ, vui lòng thử lại.")
        
        # If there's an analysis result, prepend it
        if analysis_result:
            summary = analysis_result.get('summary', '')
            formatted.insert(0, f"Kết quả phân tích ảnh: {summary}")
        
        return formatted


def convert_parts(parts: list[Part], tool_context: ToolContext):
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval


def convert_part(part: Part, tool_context: ToolContext):
    if part.type == 'text':
        return part.text
    if part.type == 'data':
        return part.data
    if part.type == 'file':
        # Repackage A2A FilePart to google.genai Blob
        # Currently not considering plain text as files
        file_id = part.file.name
        file_bytes = base64.b64decode(part.file.bytes)
        file_part = types.Part(
            inline_data=types.Blob(
                mime_type=part.file.mimeType, data=file_bytes
            )
        )
        tool_context.save_artifact(file_id, file_part)
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        return DataPart(data={'artifact-file-id': file_id})

    return f'Unknown type: {part.type}'
