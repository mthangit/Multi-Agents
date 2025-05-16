from google.adk.agents import Agent
from .instruction import INSTRUCTION_PRODUCT_AGENT
from ...tools.product_tools import product_tools

product_agent = Agent(
    name="Product Agent",
    description="A specialized agent for eyeglasses product information",
    instructions=INSTRUCTION_PRODUCT_AGENT,
    tools=product_tools,
)

