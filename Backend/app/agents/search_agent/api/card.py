from common.types import (
    AgentCard,
    AgentCapabilities,
    AgentProvider,
    AgentSkill,
)

def get_agent_card() -> AgentCard:
    return AgentCard(
        name="search_agent",
        description="Agent tìm kiếm sản phẩm kính mắt dựa trên văn bản và ảnh",
        url="http://localhost:8001",  # Thay đổi theo deployment
        provider=AgentProvider(
            organization="KhoaLuan",
            url="https://example.com"
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True,  # Hỗ trợ streaming
            pushNotifications=False,
            stateTransitionHistory=True
        ),
        defaultInputModes=["text", "image/jpeg", "image/png", "application/json"],
        defaultOutputModes=["text", "application/json"],
        skills=[
            AgentSkill(
                id="product_search",
                name="Tìm kiếm sản phẩm",
                description="Tìm kiếm sản phẩm kính mắt phù hợp dựa trên văn bản mô tả hoặc hình ảnh",
                inputModes=["text", "image/jpeg", "image/png", "application/json"],
                outputModes=["text", "application/json"],
                examples=[
                    "Tìm kính mát phù hợp với khuôn mặt tròn",
                    "Tìm kính gọng vuông màu đen"
                ]
            )
        ]
    )
