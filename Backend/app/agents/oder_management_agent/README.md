# Shopping Agent using Google ADK

Đây là hệ thống agent trợ lý mua sắm kính mắt, sử dụng Google Agent Development Kit (ADK) kết nối với cơ sở dữ liệu MySQL.

## Kiến trúc

![Architecture](https://i.imgur.com/W8a8F3V.png)

### Cấu trúc thư mục
```
order_management_agent/
├── __init__.py
├── app.py                    # Entry point, setup ADK runner
├── config/
│   └── settings.py          # Cấu hình chung, DB, API keys
├── core/
│   ├── __init__.py
│   ├── database.py          # Kết nối DB chính
│   └── session.py           # Session management
├── models/                  # SQLAlchemy models
├── services/                # Business logic
├── tools/                   # ADK tools
│   ├── __init__.py
│   ├── base.py              # Tool base classes
│   ├── product_tools.py
│   ├── order_tools.py
│   └── cart_tools.py
├── agents/                  # ADK agents
│   ├── __init__.py
│   ├── root_agent.py        # Main agent coordinator
│   ├── product/
│   ├── order/
│   └── cart/
└── utils/
    └── tool_decorators.py   # DB session decorators
```

### Database Flow

1. Kết nối DB được quản lý bởi `core/database.py` sử dụng SQLAlchemy
2. Models được định nghĩa trong thư mục `models/`
3. Services xử lý business logic trong `services/`
4. Tools sử dụng decorator `with_db_session` để tự động kết nối và xử lý session

### Agent Architecture

- **Root Agent**: Agent chính điều phối các yêu cầu và phân công cho các sub-agents
- **Product Agent**: Xử lý các yêu cầu liên quan đến sản phẩm
- **Cart Agent**: Xử lý giỏ hàng
- **Order Agent**: Xử lý đơn hàng và thanh toán

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Tạo file `.env` trong thư mục gốc:
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=shopping_db
DB_PORT=3306
GEMINI_API_KEY=your_api_key
```

3. Khởi tạo database:
```bash
# Chạy script SQL để tạo bảng và dữ liệu mẫu
mysql -u your_username -p < db.sql
```

## Chạy ứng dụng

### Web UI (Recommended)

```bash
cd /path/to/project
adk web
```

Mở trình duyệt và truy cập http://localhost:8000

### Programmatic Usage

```python
from shopping_agent.app import setup_application, run_agent

# Initialize application
setup_application()

# Run the agent
responses = run_agent("Tìm kính mắt thương hiệu Ray-Ban")
print(responses)
```

## Hướng dẫn tạo tool mới

1. Tạo function tool trong thư mục tools/ với decorator phù hợp:

```python
from shopping_agent.utils.tool_decorators import with_db_session
from shopping_agent.tools.base import create_db_tool, ToolRegistry

@with_db_session
def my_tool_function(db, param1: str) -> dict:
    # db là session SQLAlchemy
    return {"status": "success", "data": {...}}

# Tạo tool
my_tool = create_db_tool(
    name="my_tool_name",
    description="My tool description",
    func=my_tool_function
)

# Đăng ký tool
ToolRegistry.register_tools("category_name", [my_tool])
```

2. Tools sẽ tự động được đăng ký và có thể sử dụng bởi agents.

## Customizing Agents

1. Tạo instruction mới trong `agents/{agent_type}/instruction.py`
2. Tạo agent mới trong `agents/{agent_type}/agent.py`
3. Đăng ký agent mới trong `agents/root_agent.py`

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

## Giấy phép

MIT 