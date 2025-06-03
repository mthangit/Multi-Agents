from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.endpoints import chatbot
from src.api.endpoints import a2a
from src.config import settings
from src.database import initialize_database_connections
from src.a2a.agent_adapter import ChatbotA2AAdapter
from src.chatbot.langgraph_bot import ChatbotGraph
import logging
import asyncio

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("app")

# Khởi tạo FastAPI app
app = FastAPI(
    title="Order Management A2A Server",
    description="API cho hệ thống quản lý đơn hàng, chatbot và Agent-to-Agent communication",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Có thể thay đổi thành domain cụ thể trong production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bao gồm các routers
app.include_router(chatbot.router)
app.include_router(a2a.router)

# Global variables cho A2A
chatbot_instance = None
a2a_adapter = None

@app.get("/")
async def root():
    return {
        "message": "Welcome to Order Management A2A Server",
        "features": [
            "Chatbot API",
            "Agent-to-Agent Communication",
            "Agent Registry",
            "Message Broker",
            "Agent Discovery"
        ],
        "endpoints": {
            "chatbot": "/chatbot",
            "a2a": "/a2a",
            "docs": "/docs"
        }
    }

# Sự kiện startup để khởi tạo kết nối database và A2A
@app.on_event("startup")
async def startup_event():
    global chatbot_instance, a2a_adapter
    
    logger.info("Application starting up...")
    try:
        # Khởi tạo tất cả kết nối database khi ứng dụng bắt đầu
        initialize_database_connections()
        logger.info("Database connections initialized successfully")
        
        # Khởi tạo chatbot
        chatbot_instance = ChatbotGraph()
        logger.info("Chatbot initialized successfully")
        
        # Khởi tạo A2A adapter với delay để tránh connection issues
        async def init_a2a():
            try:
                await asyncio.sleep(2)  # Delay một chút để Redis kết nối ổn định
                
                global a2a_adapter
                a2a_adapter = ChatbotA2AAdapter(
                    chatbot=chatbot_instance,
                    server_host=getattr(settings, 'API_HOST', 'localhost'),
                    server_port=getattr(settings, 'API_PORT', 8000)
                )
                
                # Đăng ký agent vào hệ thống A2A
                success = await a2a_adapter.register_agent()
                if success:
                    logger.info("A2A Agent registered successfully")
                else:
                    logger.warning("Failed to register A2A Agent - continuing without A2A")
                    
            except Exception as e:
                logger.error(f"Failed to initialize A2A adapter: {str(e)}")
                logger.warning("Continuing without A2A functionality")
        
        # Chạy A2A initialization trong background
        asyncio.create_task(init_a2a())
        
    except Exception as e:
        logger.error(f"Failed to initialize: {str(e)}")
        # Vẫn cho phép ứng dụng chạy ngay cả khi có lỗi

# Sự kiện shutdown để đóng kết nối database và A2A
@app.on_event("shutdown")
async def shutdown_event():
    global a2a_adapter
    
    logger.info("Application shutting down...")
    try:
        # Hủy đăng ký A2A agent
        if a2a_adapter and a2a_adapter.registered:
            await a2a_adapter.unregister_agent()
            logger.info("A2A Agent unregistered successfully")
        
        # Đóng kết nối database khi ứng dụng kết thúc
        from src.database import DatabaseConnection, MongoDBConnection
        
        # Đóng kết nối MySQL
        try:
            DatabaseConnection.get_instance().close()
        except:
            pass
        
        # Đóng kết nối MongoDB
        try:
            MongoDBConnection.get_instance().close()
        except:
            pass
        
        # Đóng kết nối A2A services
        try:
            from src.a2a.registry import get_agent_registry
            from src.a2a.message_broker import get_message_broker
            
            registry = await get_agent_registry()
            await registry.disconnect()
            
            broker = await get_message_broker()
            await broker.disconnect()
            
        except:
            pass
        
        logger.info("All connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Endpoint để kiểm tra trạng thái A2A
@app.get("/a2a-status")
async def get_a2a_status():
    """
    Kiểm tra trạng thái A2A agent
    """
    global a2a_adapter
    
    if a2a_adapter:
        return {
            "a2a_enabled": True,
            "agent_registered": a2a_adapter.registered,
            "agent_id": a2a_adapter.agent_id,
            "heartbeat_running": a2a_adapter.heartbeat_task is not None and not a2a_adapter.heartbeat_task.done(),
            "message_listener_running": a2a_adapter.message_listener_task is not None and not a2a_adapter.message_listener_task.done()
        }
    else:
        return {
            "a2a_enabled": False,
            "agent_registered": False,
            "message": "A2A adapter not initialized"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT) 