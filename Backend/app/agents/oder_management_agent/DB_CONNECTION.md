# Kết nối Database cho Shopping Agents

Tài liệu này mô tả cách kết nối cơ sở dữ liệu MySQL cho dự án Shopping Agents.

## Cấu trúc

- `database.py`: Module chính để kết nối và quản lý session database
- `utils/db_tool_wrapper.py`: Các wrapper để cung cấp session DB tự động cho các tool
- Các tool và service đã được cập nhật để sử dụng SQLAlchemy ORM

## Cấu hình

Cấu hình kết nối database được đặt trong `config/settings.py`. Cấu hình mặc định:

```python
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "shopping_db"),
    "port": int(os.getenv("DB_PORT", "3306"))
}
```

## Biến môi trường

Tạo file `.env` tại thư mục gốc của dự án với nội dung:

```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=shopping_db
DB_PORT=3306
GEMINI_API_KEY=your_api_key
```

## Cách sử dụng

### Kết nối database

Kết nối database được tự động khởi tạo khi import `database.py`. Để tạo session mới:

```python
from shopping_agent.database import get_db_session

# Tạo session
session = get_db_session()
try:
    # Sử dụng session
    result = session.query(Model).all()
finally:
    # Đảm bảo đóng session
    session.close()
```

### Tạo tool với database

1. Sử dụng decorator `with_db_session` để tự động xử lý session:

```python
from shopping_agent.utils.db_tool_wrapper import with_db_session

@with_db_session
def my_tool_function(db, param1, param2):
    # db là session SQL Alchemy được tự động truyền vào
    return db.query(Model).filter(Model.field == param1).all()
```

2. Tạo tool object cho agent:

```python
from shopping_agent.utils.db_tool_wrapper import create_db_tool

my_tool = create_db_tool(
    name="my_tool_name",
    description="Tool description",
    func=my_tool_function
)
```

### Ví dụ đầy đủ

```python
from shopping_agent.utils.db_tool_wrapper import with_db_session, create_db_tool
from shopping_agent.models.product import Product

@with_db_session
def search_products(db, query=None):
    products = db.query(Product)
    
    if query:
        products = products.filter(Product.name.ilike(f"%{query}%"))
    
    return [product.to_dict() for product in products.all()]

# Tạo tool
search_products_tool = create_db_tool(
    name="search_products",
    description="Search for products by name",
    func=search_products
)

# Sử dụng tool trong agent
from google.adk.agents import Agent

agent = Agent(
    name="My Agent",
    description="Product search agent",
    instructions="Help users find products",
    tools=[search_products_tool]
) 