# EyeVi Shop - Backend API

<div align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-FF0000?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Jaeger-66CFE3?style=for-the-badge&logo=jaeger&logoColor=white" alt="Jaeger" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white" alt="JWT" />
</div>

<div align="center">
  <h3>Backend API cho ứng dụng thương mại điện tử EyeVi Shop</h3>
</div>

## 📋 Mục lục

- [Tổng quan](#tổng-quan)
- [Tính năng](#tính-năng)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [API Endpoints](#api-endpoints)
- [Xác thực](#xác-thực)
- [Giám sát và Tracing](#giám-sát-và-tracing)
- [Giấy phép](#giấy-phép)

## 🚀 Tổng quan

EyeVi Shop Backend API là một RESTful API được xây dựng bằng FastAPI để phục vụ cho ứng dụng thương mại điện tử EyeVi Shop. API cung cấp các endpoint để quản lý người dùng, sản phẩm, giỏ hàng, danh sách yêu thích, đặt hàng và thanh toán.

## ✨ Tính năng

- 🔐 **Xác thực và phân quyền** - JWT token, bảo vệ API endpoints
- 📦 **Quản lý sản phẩm** - CRUD, tìm kiếm, lọc sản phẩm
- 🛒 **Giỏ hàng** - Thêm, xóa, cập nhật sản phẩm trong giỏ hàng
- ❤️ **Wishlist** - Quản lý danh sách sản phẩm yêu thích
- 📦 **Đặt hàng và thanh toán** - Xử lý đơn hàng, thanh toán
- 📍 **Quản lý địa chỉ** - Thêm, sửa, xóa địa chỉ giao hàng
- 📊 **Admin Dashboard** - Quản lý người dùng, sản phẩm, đơn hàng
- 📈 **Distributed Tracing** - Giám sát hiệu suất với Jaeger
- 📝 **API Documentation** - Swagger UI, ReDoc

## 🛠️ Công nghệ sử dụng

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework API hiện đại với hiệu suất cao
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM cho cơ sở dữ liệu
- **[MySQL](https://www.mysql.com/)** - Hệ quản trị cơ sở dữ liệu
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Kiểm tra dữ liệu và serialization
- **[JWT](https://jwt.io/)** - JSON Web Token cho xác thực
- **[Jaeger](https://www.jaegertracing.io/)** - Distributed tracing
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

## 📁 Cấu trúc dự án

```
app/
├── database/           # Kết nối và cấu hình database
├── models/             # SQLAlchemy models
├── routers/            # API routes
├── schemas/            # Pydantic schemas
├── services/           # Business logic
├── utils/              # Utility functions
├── middlewares/        # Middleware functions
├── config.py           # Cấu hình ứng dụng
└── main.py             # Entry point của ứng dụng
```

## 🚀 Cài đặt và chạy

### Yêu cầu

- Python 3.8+
- MySQL 5.7+

### Các bước cài đặt

1. Clone repository:
   ```bash
   git clone https://github.com/your-username/eyevi-shop.git
   cd eyevi-shop/Website/Backend
   ```

2. Tạo và kích hoạt môi trường ảo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Cài đặt dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Cấu hình biến môi trường:
   - Tạo file `.env` dựa trên `.env.example`
   - Cập nhật các biến môi trường cần thiết

5. Khởi động ứng dụng:
   ```bash
   python run.py
   ```

6. Truy cập API documentation:
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

## 🔌 API Endpoints

### Authentication
- `POST /api/signup` - Đăng ký người dùng mới
- `POST /api/login` - Đăng nhập người dùng

### Products
- `GET /api/products` - Lấy danh sách sản phẩm
- `GET /api/products/{product_id}` - Lấy thông tin chi tiết sản phẩm
- `GET /api/categories` - Lấy danh sách danh mục

### Cart
- `GET /api/user/cart/get` - Lấy giỏ hàng của người dùng
- `POST /api/user/cart/add` - Thêm sản phẩm vào giỏ hàng
- `POST /api/user/cart/update/{product_id}` - Cập nhật số lượng sản phẩm
- `DELETE /api/user/cart/remove/{product_id}` - Xóa sản phẩm khỏi giỏ hàng

### Wishlist
- `GET /api/user/wishlist/get` - Lấy danh sách yêu thích
- `POST /api/user/wishlist/add` - Thêm sản phẩm vào wishlist
- `DELETE /api/user/wishlist/remove/{product_id}` - Xóa sản phẩm khỏi wishlist

### Checkout
- `POST /api/user/checkout/place-order` - Đặt hàng
- `POST /api/user/checkout/process-payment` - Xử lý thanh toán
- `POST /api/user/checkout/cash-on-delivery` - Thanh toán khi nhận hàng

### Address
- `GET /api/user/address/get` - Lấy danh sách địa chỉ
- `POST /api/user/address` - Thêm địa chỉ mới
- `PUT /api/user/address/{address_id}` - Cập nhật địa chỉ
- `DELETE /api/user/address/{address_id}` - Xóa địa chỉ

### Admin
- `GET /api/admin/getUser` - Lấy danh sách người dùng
- `GET /api/admin/getInvoices` - Lấy danh sách đơn hàng
- `GET /api/admin/getInvoices/{invoice_id}` - Lấy chi tiết đơn hàng
- `POST /api/admin/addproduct` - Thêm sản phẩm mới
- `PUT /api/admin/products/{product_id}` - Cập nhật sản phẩm
- `DELETE /api/admin/products/{product_id}` - Xóa sản phẩm
- `PUT /api/admin/orders/{order_id}/status` - Cập nhật trạng thái đơn hàng

## 🔐 Xác thực

API sử dụng JWT (JSON Web Token) để xác thực người dùng:

1. Người dùng đăng nhập và nhận được JWT token
2. Token được gửi trong header `Authorization` của mỗi request
3. API kiểm tra tính hợp lệ của token và cấp quyền truy cập

## 📈 Giám sát và Tracing

API sử dụng Jaeger để giám sát và tracing:

1. Mỗi request được gắn một trace ID
2. Các span được tạo ra để theo dõi thời gian xử lý của từng bước
3. Dữ liệu tracing được gửi đến Jaeger server
4. Truy cập Jaeger UI để xem thông tin tracing: http://localhost:16686

## 📄 Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm thông tin.

---

<div align="center">
  <p>Developed with ❤️ by EyeVi Team</p>
</div> 