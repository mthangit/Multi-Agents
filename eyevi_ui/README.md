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