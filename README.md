<p align="center">
  <a href="https://www.uit.edu.vn/" title="Trường Đại học Công nghệ Thông tin" style="border: none;">
    <img src="https://i.imgur.com/WmMnSRt.png" alt="Trường Đại học Công nghệ Thông tin | University of Information Technology">
  </a>
</p>



## KHÓA LUẬN TỐT NGHIỆP

-    **Đề tài:** XÂY DỰNG HỆ THỐNG CHATBOT HỖ TRỢ MUA SẮM MẮT KÍNH TRỰC
TUYẾN SỬ DỤNG MÔ HÌNH NGÔN NGỮ LỚN VÀ KỸ THUẬT TĂNG
CƯỜNG TRUY XUẤT
-    **Tên tiếng anh:** BUILDING A CHATBOT SYSTEM TO SUPPORT ONLINE EYEWEAR
SHOPPING USING LARGE LANGUAGE MODELS AND RETRIEVAL
AUGMENTED GENERATION

## THÀNH VIÊN NHÓM

| STT | MSSV     | Họ và Tên            | GitHub                            | Email                  |
| :-- | :------- | :------------------- | :-------------------------------- | :--------------------- |
| 1   | 21521990 | Nguyễn Dương         | https://github.com/duonguwu       | 21521990@gm.uit.edu.vn |
| 2   | 21521936 | Hoàng Mạnh Thắng       | https://github.com/mthangit       | 21521428@gm.uit.edu.vn |

## TỔNG QUAN HỆ THỐNG

EyeVi là hệ thống chatbot hỗ trợ mua sắm mắt kính trực tuyến sử dụng mô hình ngôn ngữ lớn (LLM) kết hợp với kỹ thuật Retrieval Augmented Generation (RAG) và mô hình CLIP để tìm kiếm sản phẩm đa phương thức. Hệ thống được thiết kế theo kiến trúc multi-agent, với mỗi agent đảm nhận một vai trò chuyên biệt trong quy trình mua sắm.

### Kiến trúc hệ thống

<p align="center">
  <img src="Architect System.png" alt="Kiến trúc hệ thống EyeVi">
</p>

Hệ thống EyeVi bao gồm các thành phần chính:
- **Orchestrator Agent**: Điều phối luồng làm việc giữa các agent
- **Search Agent**: Tìm kiếm sản phẩm mắt kính bằng văn bản hoặc hình ảnh
- **Advisor Agent**: Tư vấn lựa chọn mắt kính phù hợp với người dùng
- **Order Agent**: Xử lý và theo dõi đơn hàng
- **Vector Database**: Lưu trữ và tìm kiếm embeddings của sản phẩm
- **MySQL Database**: Lưu trữ thông tin sản phẩm, đơn hàng và người dùng

## CẤU TRÚC DỰ ÁN

Dự án được tổ chức thành các thư mục chính:

### EyeVi_Agent

Thư mục chứa mã nguồn cho hệ thống multi-agent, bao gồm các agent chuyên biệt để tìm kiếm, tư vấn và xử lý đơn hàng mắt kính.

- **[README.md](EyeVi_Agent/README.md)**: Hướng dẫn chi tiết về hệ thống agent
- **[DOCKER.md](EyeVi_Agent/DOCKER.md)**: Hướng dẫn triển khai với Docker

### eyevi_ui

Thư mục chứa mã nguồn giao diện người dùng (UI) của hệ thống, được phát triển với Next.js và Tailwind CSS.

- **[README.md](eyevi_ui/README.md)**: Hướng dẫn về giao diện người dùng
- **[src/](eyevi_ui/src/)**: Mã nguồn chính của giao diện

## HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG

### Yêu cầu hệ thống

- Python 3.9+
- Node.js 18+
- Docker và Docker Compose (cho triển khai container)
- Google API key cho LLM

### Cài đặt và khởi chạy EyeVi_Agent

1. Di chuyển vào thư mục EyeVi_Agent:
   ```bash
   cd EyeVi_Agent
   ```

2. Sao chép file môi trường:
   ```bash
   cp .env.example .env
   ```

3. Cập nhật các biến môi trường trong file `.env`

4. Khởi chạy với Docker:
   ```bash
   ./run_docker.sh
   ```

### Cài đặt và khởi chạy eyevi_ui

1. Di chuyển vào thư mục eyevi_ui:
   ```bash
   cd eyevi_ui
   ```

2. Cài đặt các thư viện phụ thuộc:
   ```bash
   npm install
   ```

3. Khởi chạy ứng dụng:
   ```bash
   npm run dev
   ```

## LIÊN KẾT

- [Mã nguồn trên GitHub](https://github.com/mthangit/Multi-Agents)
- [Báo cáo khóa luận](https://github.com/mthangit/Multi-Agents/wiki/Report)

