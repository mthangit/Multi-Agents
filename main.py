import uvicorn
import os
import logging
from dotenv import load_dotenv

# Đường dẫn tới file .env
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

# Tải các biến môi trường
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"Cảnh báo: Không tìm thấy file .env tại {ENV_PATH}")
    print("Sử dụng các biến môi trường hệ thống")

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    # Tải ứng dụng từ module app.api
    uvicorn.run(
        "app.api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
        workers=1
    )
    print("Server started 🚀") 