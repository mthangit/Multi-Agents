from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn
from app.routers import auth, product, cart, wishlist, checkout, address, admin
from app.database.database import engine, Base
# from app.utils.tracing import init_tracer
from app.config import settings

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Khởi tạo Jaeger tracer
# tracer = init_tracer()

# Tạo các bảng trong database
Base.metadata.create_all(bind=engine)

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="EyeVi Shop API",
    description="API for EyeVi Shop e-commerce platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, hãy chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware để đo thời gian xử lý request
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Đăng ký các router
app.include_router(auth.router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(wishlist.router, prefix="/api")
app.include_router(checkout.router, prefix="/api")
app.include_router(address.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Kiểm tra trạng thái hoạt động của API
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 