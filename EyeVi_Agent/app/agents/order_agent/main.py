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

from src.a2a_wrapper.agent_executor import OrderAgentExecutor
from src.database import initialize_database_connections

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10000)
@click.option('--agent-type', 'agent_type',
              type=click.Choice(['simplified', 'simple', 'streaming']), 
              default='simplified',
              help='Loại agent sử dụng: simplified (mới), simple (cũ), streaming (bot)')
def main(host, port, agent_type):
    """Starts the Order Agent server với simplified agent."""
    try:
        # Check API key first
        if not os.getenv('GOOGLE_API_KEY'):
            raise MissingAPIKeyError(
                'GOOGLE_API_KEY environment variable not set.'
            )
            
        # Try to initialize database connections (non-blocking)
        try:
            initialize_database_connections()
            logger.info("✅ Database connections initialized successfully")
        except Exception as db_error:
            logger.warning(f"⚠️  Database initialization failed (continuing anyway): {db_error}")
            # Continue without database - agent can still work for basic chat

        # Define agent capabilities - hỗ trợ streaming và push notifications
        capabilities = AgentCapabilities(streaming=False, pushNotifications=True)
        
        # Agent skills - 6 chức năng chính từ SimplifiedOrderAgent
        agent_skills = [
            AgentSkill(
                id='find_product_by_id',
                name='Tìm sản phẩm theo ID',
                description='Tìm kiếm thông tin chi tiết sản phẩm bằng ID. Hiển thị tên, giá, mô tả và số lượng tồn kho.',
                tags=['search', 'product', 'id', 'lookup'],
                examples=[
                    'Tìm sản phẩm ID 123',
                    'Cho tôi xem sản phẩm có ID 456', 
                    'Thông tin chi tiết sản phẩm số 789',
                    'Sản phẩm 15 có gì không?'
                ],
            ),
            AgentSkill(
                id='find_product_by_name',
                name='Tìm sản phẩm theo tên',
                description='Tìm kiếm sản phẩm theo tên hoặc từ khóa. Hỗ trợ tìm kiếm mờ và hiển thị tối đa 5 kết quả.',
                tags=['search', 'product', 'name', 'keyword', 'fuzzy'],
                examples=[
                    'Tìm sản phẩm iPhone',
                    'Có kính mắt nào không?',
                    'Sản phẩm Samsung',
                    'Tìm laptop Dell'
                ],
            ),
            AgentSkill(
                id='get_user_info',
                name='Xem thông tin khách hàng',
                description='Lấy thông tin chi tiết khách hàng bao gồm tên, email, số điện thoại và địa chỉ.',
                tags=['user', 'profile', 'customer', 'info'],
                examples=[
                    'Thông tin của tôi',
                    'Xem profile tôi',
                    'Tài khoản của tôi như thế nào?',
                    'Thông tin user 5'
                ],
            ),
            AgentSkill(
                id='get_user_orders', 
                name='Xem lịch sử đơn hàng',
                description='Xem lịch sử đơn hàng của khách hàng với thông tin tổng tiền, số sản phẩm và trạng thái.',
                tags=['order', 'history', 'purchase', 'tracking'],
                examples=[
                    'Đơn hàng của tôi',
                    'Lịch sử mua hàng',
                    '5 đơn hàng gần nhất',
                    'Xem đơn hàng user 10'
                ],
            ),
            AgentSkill(
                id='collect_order_info',
                name='Thu thập thông tin đặt hàng',
                description='Thu thập và xác nhận thông tin sản phẩm, yêu cầu cung cấp địa chỉ giao hàng, số điện thoại và hình thức thanh toán (COD/Banking).',
                tags=['order', 'info', 'collect', 'prepare', 'confirm'],
                examples=[
                    'Đặt 2 sản phẩm ID 1',
                    'Mua iPhone 2 cái',
                    'Tôi muốn đặt hàng',
                    'Đặt 3 sản phẩm ID 5'
                ],
            ),
            AgentSkill(
                id='create_order_directly',
                name='Tạo đơn hàng với thông tin đầy đủ',
                description='Tạo đơn hàng cuối cùng với thông tin đầy đủ đã được thu thập (địa chỉ, SĐT, payment). Chỉ hỗ trợ COD và Banking.',
                tags=['order', 'finalize', 'complete', 'create', 'confirm'],
                examples=[
                    'Xác nhận đặt hàng với địa chỉ và SĐT',
                    'Hoàn tất đơn hàng thanh toán COD',
                    'Tạo đơn với thông tin giao hàng',
                    'Xử lý đơn hàng cuối cùng'
                ],
            )
        ]

        # Create agent card với thông tin chi tiết
        agent_description = {
            'simplified': 'Trợ lý quản lý đơn hàng thông minh với LangGraph và Gemini AI. Hỗ trợ tìm kiếm sản phẩm, quản lý thông tin khách hàng, xem lịch sử đơn hàng và tạo đơn hàng mới với thu thập thông tin đầy đủ (địa chỉ, SĐT, thanh toán COD/Banking).',
            'simple': 'Trợ lý đơn hàng với Simple LangGraph Agent',
            'streaming': 'Trợ lý đơn hàng với Streaming Bot'
        }
        
        agent_card = AgentCard(
            name='Order Agent',
            description=agent_description[agent_type],
            url=f'http://{host}:{port}/',
            version='2.1.0',  # Version cập nhật mới
            defaultInputModes=['text/plain'],
            defaultOutputModes=['text/plain', 'application/json'],
            capabilities=capabilities,
            skills=agent_skills,
        )

        # Initialize HTTP client and components
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=OrderAgentExecutor(agent_type=agent_type),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        # Create and run server
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )

        logger.info(f"🚀 Starting EyeVi Order Management Agent server")
        logger.info(f"   🌐 Host: {host}:{port}")
        logger.info(f"   🤖 Agent Type: {agent_type.upper()}")
        logger.info(f"   📋 Agent Card: http://{host}:{port}/.well-known/agent.json")
        logger.info(f"   🔗 A2A Endpoint: http://{host}:{port}/")
        logger.info(f"   ⚡ Capabilities: 6 skills, database integration")
        logger.info(f"   🧠 AI Model: Gemini 2.0 Flash")
        logger.info(f"💬 EyeVi Order Agent is ready!")
        
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f'❌ API Key Error: {e}')
        logger.info('💡 Please set GOOGLE_API_KEY in your .env file')
        sys.exit(1)
    except Exception as e:
        logger.error(f'❌ Server startup error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()