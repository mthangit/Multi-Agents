# EyeVi UI - Chatbot hỗ trợ mua sắm mắt kính

UI cho hệ thống chatbot hỗ trợ mua sắm mắt kính trực tuyến sử dụng mô hình ngôn ngữ lớn và kỹ thuật tăng cường truy xuất.

## Các tính năng

- Giao diện chat trực quan, thân thiện với người dùng
- Khả năng gửi tin nhắn văn bản
- Đính kèm tệp, hình ảnh
- Chụp ảnh từ camera
- Ghi âm giọng nói
- Lưu trữ lịch sử trò chuyện
- Giao diện tối/sáng

## Công nghệ sử dụng

- [Next.js](https://nextjs.org/)
- [React](https://reactjs.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)

## Cài đặt và chạy

1. Cài đặt các package:

```bash
npm install
```

2. Chạy môi trường phát triển:

```bash
npm run dev
```

3. Mở [http://localhost:3000](http://localhost:3000) để xem kết quả.

## Cấu trúc dự án

```
eyevi_ui/
├── public/              # Tài nguyên tĩnh
├── src/
│   ├── app/             # Các trang Next.js
│   ├── components/      # Components React 
│   │   ├── ui/          # UI components
│   │   └── ...          # Các components khác
│   ├── lib/             # Thư viện và tiện ích
│   └── ...
├── tailwind.config.js   # Cấu hình Tailwind CSS
├── tsconfig.json        # Cấu hình TypeScript
└── ...
```

## Môi trường

- Node.js 18+ và npm 


# Phân tích triển khai và hướng phát triển tiếp theo cho EyeVi UI

## Tóm tắt hiện trạng

Hiện tại, EyeVi UI đã có các thành phần cơ bản của một ứng dụng chat:
- Giao diện chat với tin nhắn từ người dùng và bot
- Khả năng gửi tin nhắn văn bản
- Hỗ trợ đính kèm tệp tin và hình ảnh
- Giao diện đã được cải thiện để tin nhắn người dùng căn phải, tin nhắn bot căn trái

## Hướng phát triển tiếp theo và các file liên quan

### 1. Hoàn thiện chức năng đính kèm tệp tin
- **File cần xem**: `eyevi_ui/src/components/chat-input.tsx`
- **File cần xem**: `eyevi_ui/src/app/page.tsx` (để xử lý logic gửi tệp đính kèm)

### 2. Tích hợp API Backend
- **File cần xem**: `eyevi_ui/src/app/page.tsx` (cần cập nhật URL API)
- **Tạo file mới**: `eyevi_ui/src/api/chatService.ts` (để tách riêng logic gọi API)

### 3. Cải thiện giao diện Sidebar
- **File cần xem**: `eyevi_ui/src/components/sidebar.tsx`
- **Cần triển khai**: Chức năng tạo cuộc trò chuyện mới, lưu lịch sử chat

### 4. Quản lý trạng thái toàn cục
- **Tạo file mới**: `eyevi_ui/src/lib/store.ts` (sử dụng Zustand hoặc Context API)
- **Cần triển khai**: Quản lý trạng thái người dùng, danh sách cuộc trò chuyện, v.v.

### 5. Cải thiện chức năng chat
- **File cần xem**: `eyevi_ui/src/components/chat-messages.tsx` (để thêm hiệu ứng loading)
- **Bổ sung**: Hiển thị trạng thái đang nhập, đang gửi tin nhắn

### 6. Triển khai xác thực người dùng
- **Tạo file mới**: `eyevi_ui/src/app/login/page.tsx` (trang đăng nhập)
- **Tạo file mới**: `eyevi_ui/src/lib/auth.ts` (logic xác thực)

### 7. Cài đặt người dùng
- **Tạo file mới**: `eyevi_ui/src/app/settings/page.tsx`
- **Cần triển khai**: Thay đổi cài đặt, cập nhật thông tin người dùng

### 8. Tối ưu hiệu suất ứng dụng
- **File cần xem**: `eyevi_ui/src/app/layout.tsx` (để cấu hình metadata và hiệu suất trang)
- **Cân nhắc**: Sử dụng React.memo, useCallback và useMemo cho các component lớn

### 9. Chức năng ghi âm
- **File cần xem**: `eyevi_ui/src/components/chat-input.tsx`
- **Cần triển khai**: Hoàn thiện nút ghi âm với MediaRecorder API

### 10. Thêm tính năng trích xuất văn bản từ hình ảnh (OCR)
- **Tạo file mới**: `eyevi_ui/src/lib/ocr.ts` (tích hợp với API OCR)
- **File cần xem**: `eyevi_ui/src/components/chat-input.tsx` (để bổ sung vào quy trình xử lý tệp đính kèm)

## Các tương tác cần cải thiện

1. **Hiển thị trạng thái bot đang trả lời**
   - Thêm hiệu ứng "đang nhập" khi chờ phản hồi từ API

2. **Tạo tính năng cuộc trò chuyện theo chủ đề**
   - Thực hiện phân loại/gắn thẻ cho mỗi cuộc trò chuyện

3. **Tùy chỉnh giao diện theo chế độ sáng/tối**
   - Triển khai chuyển đổi theme với Tailwind CSS

4. **Đồng bộ hóa dữ liệu chat**
   - Lưu trữ tin nhắn trên cơ sở dữ liệu và đồng bộ hóa giữa các thiết bị

5. **Cải thiện trải nghiệm người dùng trên thiết bị di động**
   - Thêm responsive design cho giao diện

## Kết luận

EyeVi UI đã có nền tảng vững chắc để phát triển tiếp. Nên ưu tiên các tính năng theo thứ tự: hoàn thiện tích hợp API backend, quản lý trạng thái toàn cục, sau đó mới đến các tính năng khác như xác thực người dùng và cài đặt cá nhân hóa.
