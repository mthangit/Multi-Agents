import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .remote_agent_connection import RemoteAgentConnections

load_dotenv()
nest_asyncio.apply()


class OrchestratorAgent:
    """The Orchestrator agent for eyewear consultation and shopping system."""

    def __init__(
        self,
    ):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self._agent = self.create_agent()
        self._user_id = "orchestrator_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _async_init_components(self, remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    print(f"Initialized connection for {card.name}")
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(f"ERROR: Failed to get agent card from {address}: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to initialize connection for {address}: {e}")

        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("agent_info:", agent_info)
        self.agents = "\n".join(agent_info) if agent_info else "Không tìm thấy agent nào"

    @classmethod
    async def create(
        cls,
        remote_agent_addresses: List[str],
    ):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash-preview-04-17",
            name="Orchestrator_Agent",
            instruction=self.root_instruction,
            description="Orchestrator Agent điều phối hệ thống tư vấn và mua sắm mắt kính thông minh, kết nối với Advisor Agent, Search Agent và Order Agent để cung cấp trải nghiệm toàn diện cho khách hàng.",
            tools=[
                self.send_message,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
        **Vai trò:** Bạn là Orchestrator Agent - trợ lý thông minh điều phối hệ thống tư vấn và mua sắm mắt kính. Bạn có khả năng kết nối với 3 agent chuyên biệt để hỗ trợ khách hàng một cách toàn diện.

        **Các Agent Có Sẵn:**
        {self.agents}

        **Chức Năng Chính:**

        **1. 🎯 Phân Tích Yêu Cầu:**
        - Hiểu rõ nhu cầu của khách hàng (tư vấn, tìm kiếm, đặt hàng)
        - Xác định agent phù hợp để xử lý yêu cầu
        - Điều phối luồng công việc giữa các agent

        **2. 🔍 Tìm Kiếm Sản Phẩm (Search Agent):**
        - Sử dụng `send_message` để gọi Search Agent khi khách hàng cần:
          * Tìm kiếm sản phẩm bằng văn bản
          * Tìm kiếm bằng hình ảnh
          * Tìm kiếm đa phương thức (text + image)
          * Tìm kiếm cá nhân hóa dựa trên phân tích khuôn mặt
        - Ví dụ: "Tìm kính cận thị cho nam", "Tìm kính tương tự như trong ảnh"

        **3. 💡 Tư Vấn Chuyên Sâu (Advisor Agent):**
        - Sử dụng `send_message` để gọi Advisor Agent khi khách hàng cần:
          * Tư vấn về loại tròng kính phù hợp
          * Gợi ý sản phẩm dựa trên nhu cầu cụ thể
          * Tư vấn kỹ thuật về quang học
          * Tư vấn phong cách và kiểu dáng
        - Ví dụ: "Tôi bị cận 2.5 độ nên chọn tròng kính nào?", "Kính chống ánh sáng xanh có hiệu quả không?"

        **4. 🛍️ Quản Lý Đơn Hàng (Order Agent):**
        - Sử dụng `send_message` để gọi Order Agent khi khách hàng cần:
          * Tìm thông tin sản phẩm theo ID hoặc tên
          * Xem thông tin cá nhân và lịch sử đơn hàng
          * Tạo đơn hàng mới
        - Ví dụ: "Tìm sản phẩm ID 123", "Tạo đơn hàng với 2 sản phẩm ID 1 và 3 sản phẩm ID 5"

        **5. 🔄 Điều Phối Thông Minh:**
        - **Luồng Tư Vấn → Tìm Kiếm → Đặt Hàng:**
          1. Tư vấn chuyên sâu về nhu cầu (Advisor Agent)
          2. Tìm kiếm sản phẩm phù hợp (Search Agent)
          3. Hỗ trợ đặt hàng (Order Agent)
        
        - **Luồng Tìm Kiếm → Tư Vấn → Đặt Hàng:**
          1. Tìm kiếm sản phẩm ban đầu (Search Agent)
          2. Tư vấn chi tiết về sản phẩm (Advisor Agent)
          3. Hỗ trợ đặt hàng (Order Agent)

        **6. 📋 Hướng Dẫn Sử Dụng Tools:**
        - Sử dụng `send_message` với format: `send_message(agent_name, task)`
        - Agent names chính xác:
          * "Advisor Agent"
          * "Search Agent"
          * "Order Agent"

        **7. 🎯 Chiến Lược Điều Phối:**
        - **Yêu cầu tư vấn chung:** → Advisor Agent
        - **Yêu cầu tìm kiếm cụ thể:** → Search Agent
        - **Yêu cầu thông tin sản phẩm/đơn hàng:** → Order Agent
        - **Yêu cầu phức tạp:** Kết hợp nhiều agent theo thứ tự logic

        **8. 💬 Giao Tiếp Thân Thiện:**
        - Luôn trả lời bằng tiếng Việt
        - Giải thích rõ ràng quá trình xử lý
        - Tóm tắt kết quả từ các agent một cách dễ hiểu
        - Đề xuất bước tiếp theo phù hợp

        **9. 🔧 Xử Lý Lỗi:**
        - Nếu agent không phản hồi, thông báo rõ ràng cho khách hàng
        - Đề xuất giải pháp thay thế
        - Ghi log lỗi để debug

        **Ngày Hiện Tại:** {datetime.now().strftime("%Y-%m-%d")}

        **Lưu Ý Quan Trọng:**
        - Đảm bảo tên agent chính xác khi gọi `send_message`
        - Tối ưu hóa trải nghiệm khách hàng bằng cách điều phối thông minh
        - Duy trì context và lịch sử tương tác để tư vấn hiệu quả hơn
        """

    async def stream(
        self, query: str, session_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        """
        Streams the agent's response to a given query.
        """
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "The host agent is thinking...",
                }

    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        """Gửi yêu cầu đến agent chuyên biệt (Advisor, Search, hoặc Order Agent)."""
        print(f"Sending message to {agent_name}")
        print(f"Remote agent connections: {self.remote_agent_connections.keys()}")
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f"Client not available for {agent_name}")

        # Simplified task and context ID management
        state = tool_context.state
        task_id = state.get("task_id", str(uuid.uuid4()))
        context_id = state.get("context_id", str(uuid.uuid4()))
        message_id = str(uuid.uuid4())

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            },
        }

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        send_response: SendMessageResponse = await client.send_message(message_request)

        # if not isinstance(
        #     send_response.root, SendMessageSuccessResponse
        # ) or not isinstance(send_response.root.result, Task):
        #     print("Received a non-success or non-task response. Cannot proceed.")
        #     return

        response_content = send_response.model_dump(mode='json', exclude_none=True)
        print("response_content", response_content)

        resp = []
        if response_content.get("result", {}).get("artifacts"):
            for artifact in response_content["result"]["artifacts"]:
                if artifact.get("parts"):
                    resp.extend(artifact["parts"])
        return resp


def _get_initialized_orchestrator_agent_sync():
    """Synchronously creates and initializes the OrchestratorAgent."""

    async def _async_main():
        # URLs của các agent chuyên biệt trong hệ thống mắt kính
        eyewear_agent_urls = [
            "http://localhost:10000",  # Order Agent
            "http://localhost:10001",  # Advisor Agent
            "http://localhost:10002",  # Search Agent
        ]

        print("initializing orchestrator agent")
        orchestrator_agent_instance = await OrchestratorAgent.create(
            remote_agent_addresses=eyewear_agent_urls
        )
        print("OrchestratorAgent initialized")
        return orchestrator_agent_instance.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Warning: Could not initialize OrchestratorAgent with asyncio.run(): {e}. "
                "This can happen if an event loop is already running (e.g., in Jupyter). "
                "Consider initializing OrchestratorAgent within an async function in your application."
            )
        else:
            raise


root_agent = _get_initialized_orchestrator_agent_sync()