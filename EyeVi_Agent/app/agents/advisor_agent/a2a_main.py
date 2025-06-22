#!/usr/bin/env python3
"""
A2A Main Server cho Advisor Agent (RAG-based Eyewear Consultation)
"""

import logging
import os
import sys
from pathlib import Path

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

from a2a_wrapper.a2a_agent_executor import AdvisorAgentExecutor

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


class MissingDataError(Exception):
    """Exception for missing data/database."""


def check_prerequisites():
    """Check if all prerequisites are met for the advisor agent."""
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError(
            'GOOGLE_API_KEY environment variable not set. Please set your Google Gemini API key.'
        )
    
    # Check data directory exists
    data_folder = Path("data")
    if not data_folder.exists():
        raise MissingDataError(
            'Data directory not found. Please run data ingestion first: python ingest_data.py'
        )
    
    # Check for PDF files
    import glob
    pdf_files = glob.glob("data/**/*.pdf", recursive=True)
    if not pdf_files:
        raise MissingDataError(
            'No PDF files found in data directory. Please add PDF files and run: python ingest_data.py'
        )
    
    logger.info(f"✅ Prerequisites met: {len(pdf_files)} PDF files found")


@click.command()
@click.option('--host', 'host', default='localhost', help='Host to bind to')
@click.option('--port', 'port', default=10001, help='Port to bind to')
@click.option('--skip-checks', is_flag=True, help='Skip prerequisite checks')
def main(host, port, skip_checks):
    """Starts the Advisor Agent A2A server."""
    try:
        # Check prerequisites unless skipped
        if not skip_checks:
            try:
                check_prerequisites()
            except (MissingAPIKeyError, MissingDataError) as e:
                logger.warning(f"Prerequisite check failed: {e}")
                logger.info("Starting server anyway, but functionality may be limited")
        
        # Define agent capabilities and skills for eyewear consultation
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        # Define advisor agent skills
        advisor_skills = [
            AgentSkill(
                id='eyewear_consultation',
                name='Tư vấn mắt kính',
                description='Tư vấn chuyên sâu về mắt kính dựa trên cơ sở dữ liệu kiến thức chuyên ngành',
                tags=['eyewear', 'consultation', 'optics', 'vision'],
                examples=[
                    'Tôi bị cận thị 2.5 độ, nên chọn loại tròng kính nào?',
                    'Kính chống ánh sáng xanh có thực sự hiệu quả không?',
                    'Khuôn mặt tròn phù hợp với kiểu gọng nào?',
                    'So sánh tròng kính đa tròng và đơn tròng?'
                ],
            ),
            AgentSkill(
                id='product_recommendation',
                name='Gợi ý sản phẩm',
                description='Đưa ra gợi ý sản phẩm mắt kính phù hợp với nhu cầu và điều kiện cụ thể',
                tags=['product', 'recommendation', 'personalized'],
                examples=[
                    'Tôi làm việc nhiều với máy tính, cần loại kính nào?',
                    'Gọng titan có ưu điểm gì so với gọng nhựa?',
                    'Kính photochromic có phù hợp với tôi không?'
                ],
            ),
            AgentSkill(
                id='technical_advice',
                name='Tư vấn kỹ thuật',
                description='Giải thích các khía cạnh kỹ thuật của mắt kính và quang học',
                tags=['technical', 'optics', 'education'],
                examples=[
                    'Chỉ số khúc xạ của tròng kính ảnh hưởng như thế nào?',
                    'Lớp phủ chống phản xạ hoạt động ra sao?',
                    'Tại sao tròng kính mỏng lại đắt hơn?'
                ],
            ),
            AgentSkill(
                id='style_consultation',
                name='Tư vấn phong cách',
                description='Tư vấn về kiểu dáng và phong cách mắt kính phù hợp với khuôn mặt',
                tags=['style', 'fashion', 'design'],
                examples=[
                    'Khuôn mặt vuông nên chọn gọng như thế nào?',
                    'Xu hướng kính mắt năm 2024 là gì?',
                    'Làm sao để phối kính với trang phục?'
                ],
            )
        ]

        # Create agent card with specialized eyewear consultation info
        agent_card = AgentCard(
            name='Advisor Agent',
            description='Agent tư vấn chuyên sâu về mắt kính, sử dụng cơ sở dữ liệu kiến thức chuyên ngành để đưa ra lời khuyên chính xác và hữu ích về các vấn đề liên quan đến mắt kính, quang học và thị lực',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text/plain'],
            defaultOutputModes=['text/plain'],
            capabilities=capabilities,
            skills=advisor_skills,
        )

        # Initialize HTTP client and components
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=AdvisorAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        # Create and run server
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )

        logger.info(f"🚀 Starting Advisor Agent A2A server on {host}:{port}")
        logger.info(f"📋 Agent Card: http://{host}:{port}/.well-known/agent.json")
        logger.info(f"🔗 A2A Endpoint: http://{host}:{port}/")
        logger.info(f"💬 Ready for eyewear consultation queries!")
        
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f'❌ API Key Error: {e}')
        logger.info('💡 Please set GOOGLE_API_KEY in your .env file')
        sys.exit(1)
    except MissingDataError as e:
        logger.error(f'❌ Data Error: {e}')
        logger.info('💡 Please run: python ingest_data.py')
        sys.exit(1)
    except Exception as e:
        logger.error(f'❌ Server startup error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()