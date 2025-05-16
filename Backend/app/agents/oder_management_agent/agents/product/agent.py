"""
Product agent module
"""
from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent

from shopping_agent.config.settings import GEMINI_MODEL, AGENT_CONFIG
from shopping_agent.tools.base import ToolRegistry
from .instruction import PRODUCT_AGENT_INSTRUCTION

# Tạo Product Agent với các tools liên quan đến sản phẩm
product_agent = LlmAgent(
    name="Product Agent",
    model=GEMINI_MODEL,
    description="Agent chuyên về thông tin sản phẩm kính mắt",
    instruction=PRODUCT_AGENT_INSTRUCTION,
    tools=ToolRegistry.get_tools("product"),  # Chỉ sử dụng product tools
    model_kwargs=AGENT_CONFIG
) 