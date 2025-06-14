import logging
import os
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from src.chatbot.simplified_bot import simplified_chatbot_instance
from src.a2a.agent_executor import OrderAgentExecutor
from src.database import initialize_database_connections

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10000)
def main(host, port):
    """Starts the Order Agent server."""
    try:
        # Check API key first
        if not os.getenv('GEMINI_API_KEY'):
            raise MissingAPIKeyError(
                'GEMINI_API_KEY environment variable not set.'
            )
            
        # Try to initialize database connections (non-blocking)
        try:
            initialize_database_connections()
            logger.info("Database connections initialized successfully")
        except Exception as db_error:
            logger.warning(f"Database initialization failed (continuing anyway): {db_error}")
            # Continue without database - agent can still work for basic chat

        # Define agent capabilities and skills
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id='order_agent',
            name='Order Agent',
            description='Helps with order management tasks like finding products, managing cart, and creating orders',
            tags=['order management', 'shopping', 'e-commerce'],
            examples=[
                'Tìm sản phẩm iPhone',
                'Thêm 2 sản phẩm ID 123 vào giỏ hàng',
                'Xem giỏ hàng của tôi',
                'Tạo đơn hàng mới'
            ],
        )

        # Create agent card with supported content types from SimplifiedChatbot
        agent_card = AgentCard(
            name='Order Agent',
            description='A simplified order management agent that helps with product search, cart management, and order creation',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text/plain'],  # Simplified to just text input
            defaultOutputModes=['text/plain'],  # Simplified to just text output
            capabilities=capabilities,
            skills=[skill],
        )

        # Initialize HTTP client and components
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=OrderAgentExecutor(),  # Uses SimplifiedChatbot internally
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        # Create and run server
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )

        logger.info(f"Starting Order Agent server on {host}:{port}")
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()