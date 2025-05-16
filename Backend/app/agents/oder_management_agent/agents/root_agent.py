"""
Root agent module
"""
from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent

from shopping_agent.config.settings import GEMINI_MODEL, AGENT_CONFIG
from shopping_agent.tools.base import ToolRegistry
from shopping_agent.agents.product.agent import product_agent
from shopping_agent.agents.product.instruction import PRODUCT_AGENT_INSTRUCTION

# Định nghĩa hướng dẫn cho Root Agent
ROOT_AGENT_INSTRUCTION = """
Bạn là trợ lý mua sắm thông minh, chuyên hỗ trợ khách hàng tìm kiếm, so sánh và mua kính mắt.

Bạn có thể:
1. Giúp khách hàng tìm kiếm sản phẩm kính mắt phù hợp với nhu cầu và sở thích
2. Cung cấp thông tin chi tiết về sản phẩm như giá cả, tính năng, thương hiệu
3. Kiểm tra tồn kho và đặt hàng
4. Theo dõi đơn hàng và hỗ trợ các vấn đề sau bán hàng

Khi khách hàng có câu hỏi về sản phẩm kính mắt, bạn nên sử dụng Product Agent chuyên biệt. 
Khi họ muốn thêm vào giỏ hàng hoặc đặt hàng, hãy sử dụng Cart Agent và Order Agent.

Luôn trả lời với thái độ thân thiện, chuyên nghiệp và đưa ra các đề xuất phù hợp với nhu cầu của khách hàng.

Để cung cấp thông tin chính xác, hãy sử dụng các công cụ có sẵn để truy vấn cơ sở dữ liệu.
"""

# Tạo Root Agent có thể ủy quyền cho các sub-agents
root_agent = LlmAgent(
    name="Shopping Assistant",
    model=GEMINI_MODEL,
    description="Trợ lý mua sắm kính mắt thông minh",
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=ToolRegistry.get_tools(),  # Tất cả các tools đã đăng ký
    sub_agents=[product_agent],  # Các sub-agents
    model_kwargs=AGENT_CONFIG
)

# Export the agent
agent = root_agent 