# Hướng dẫn Docker cho Backend API

Tài liệu này hướng dẫn cách triển khai và chạy backend API sử dụng Docker và Docker Compose.

## Yêu cầu

- Docker và Docker Compose đã được cài đặt
- Google Gemini API key (nếu sử dụng các tính năng liên quan đến AI)

## Cấu trúc

- `Dockerfile`: Cấu hình môi trường Docker cho backend API
- `docker-compose.yml`: Cấu hình để chạy backend API cùng với Qdrant và các dịch vụ khác

## Khởi động

### 1. Thiết lập biến môi trường

Tạo file `.env` trong thư mục gốc (`Backend/`) với nội dung:

```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 2. Chạy môi trường phát triển

```bash
# Khởi động tất cả dịch vụ
docker-compose up

# Hoặc chạy ở chế độ nền
docker-compose up -d
```

Dịch vụ sẽ khả dụng tại:
- API: http://localhost:8000
- Qdrant UI: http://localhost:6334

### 3. Theo dõi logs

```bash
# Xem logs của tất cả dịch vụ
docker-compose logs -f

# Chỉ xem logs của API
docker-compose logs -f api
```

### 4. Dừng dịch vụ

```bash
docker-compose down
```

## Các lệnh hữu ích

```bash
# Xem trạng thái các dịch vụ
docker-compose ps

# Xây dựng lại image
docker-compose build

# Chạy một lệnh trong container
docker-compose exec api python -c "print('Hello World')"

# Truy cập shell trong container
docker-compose exec api bash
```

## Quản lý dữ liệu

Dữ liệu của Qdrant được lưu trữ trong volume Docker `qdrant_data`. Để xóa dữ liệu và bắt đầu lại:

```bash
docker-compose down -v  # Xóa cả volumes
```

## Triển khai production

Đối với môi trường production, bạn nên:

1. Xóa cờ `--reload` trong `command` của dịch vụ `api` trong file `docker-compose.yml` 
2. Thay đổi các cài đặt mạng để hạn chế quyền truy cập trực tiếp vào Qdrant
3. Thiết lập xác thực cho Qdrant
4. Cân nhắc sử dụng proxy như Nginx ở phía trước API

## Xử lý sự cố

### API không thể kết nối với Qdrant
Kiểm tra logs của Qdrant để xem nó đã khởi động thành công chưa:
```bash
docker-compose logs qdrant
```

### Vấn đề khi cài đặt thư viện CLIP
CLIP yêu cầu PyTorch, có thể gặp vấn đề khi cài đặt. Xem logs build để biết chi tiết:
```bash
docker-compose build --no-cache
``` 