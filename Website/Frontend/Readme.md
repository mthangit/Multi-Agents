# EyeVi Shop - Frontend

<div align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white" alt="Axios" />
  <img src="https://img.shields.io/badge/Context_API-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="Context API" />
</div>

<div align="center">
  <h3>Giao diện thương mại điện tử hiện đại, đẹp mắt và dễ sử dụng</h3>
</div>

## 📋 Mục lục

- [Tổng quan](#tổng-quan)
- [Tính năng](#tính-năng)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [API Endpoints](#api-endpoints)
- [State Management](#state-management)
- [Xác thực](#xác-thực)
- [Đóng góp](#đóng-góp)
- [Giấy phép](#giấy-phép)

## 🚀 Tổng quan

EyeVi Shop là một ứng dụng thương mại điện tử hiện đại được xây dựng bằng React. Frontend được thiết kế với trải nghiệm người dùng tuyệt vời, giao diện đẹp mắt và hiệu suất cao. Dự án sử dụng Context API của React để quản lý state, Axios để giao tiếp với backend, và JWT để xác thực người dùng.

![EyeVi Shop Screenshot](https://via.placeholder.com/800x400?text=EyeVi+Shop+Screenshot)

## ✨ Tính năng

- 🛍️ **Hiển thị sản phẩm** - Duyệt và tìm kiếm sản phẩm theo nhiều tiêu chí
- 🔍 **Lọc và tìm kiếm** - Lọc sản phẩm theo danh mục, giá, và các thuộc tính khác
- 🛒 **Giỏ hàng** - Thêm, xóa, cập nhật số lượng sản phẩm trong giỏ hàng
- ❤️ **Wishlist** - Lưu sản phẩm yêu thích để mua sau
- 👤 **Quản lý tài khoản** - Đăng ký, đăng nhập, quản lý thông tin cá nhân
- 📦 **Đặt hàng và thanh toán** - Quy trình thanh toán đơn giản với nhiều phương thức
- 📍 **Quản lý địa chỉ** - Thêm, sửa, xóa địa chỉ giao hàng
- 🔒 **Xác thực JWT** - Bảo mật với JSON Web Token
- 📱 **Responsive Design** - Trải nghiệm tuyệt vời trên mọi thiết bị

## 🛠️ Công nghệ sử dụng

- **[React](https://reactjs.org/)** - Thư viện JavaScript để xây dựng giao diện người dùng
- **[Context API](https://reactjs.org/docs/context.html)** - Quản lý state của ứng dụng
- **[Axios](https://axios-http.com/)** - Thư viện HTTP client để giao tiếp với API
- **[React Router](https://reactrouter.com/)** - Định tuyến trong ứng dụng React
- **[JWT](https://jwt.io/)** - JSON Web Token cho xác thực người dùng
- **[CSS3](https://developer.mozilla.org/en-US/docs/Web/CSS)** - Styling cho ứng dụng

## 📁 Cấu trúc dự án

```
src/
├── api/                 # API services và URL endpoints
├── assets/              # Tài nguyên tĩnh (hình ảnh, fonts)
├── components/          # React components tái sử dụng
├── contexts/            # Context API providers
│   ├── authContext/     # Xác thực người dùng
│   ├── cartContext/     # Quản lý giỏ hàng
│   ├── productsContext/ # Quản lý sản phẩm
│   ├── wishlistContext/ # Quản lý wishlist
│   └── checkoutContext/ # Quản lý thanh toán
├── hooks/               # Custom React hooks
├── pages/               # Các trang của ứng dụng
├── reducers/            # Reducers cho Context API
├── routes/              # Cấu hình routing
├── utils/               # Các hàm tiện ích
├── App.jsx              # Component gốc
├── index.js             # Entry point
└── server.js            # Server-side rendering (nếu có)
```

## 🚀 Cài đặt và chạy

### Yêu cầu

- Node.js (v14.0.0 trở lên)
- npm hoặc yarn

### Các bước cài đặt

1. Clone repository:
   ```bash
   git clone https://github.com/your-username/eyevi-shop.git
   cd eyevi-shop/Website/Frontend
   ```

2. Cài đặt dependencies:
   ```bash
   npm install
   # hoặc
   yarn install
   ```

3. Cấu hình biến môi trường:
   - Tạo file `.env` dựa trên `.env.example`
   - Cập nhật các biến môi trường cần thiết

4. Chạy ứng dụng ở môi trường development:
   ```bash
   npm start
   # hoặc
   yarn start
   ```

5. Build cho production:
   ```bash
   npm run build
   # hoặc
   yarn build
   ```

## 🔌 API Endpoints

Frontend giao tiếp với backend thông qua các API endpoints sau:

- **Authentication**
  - `POST /api/signup` - Đăng ký người dùng mới
  - `POST /api/login` - Đăng nhập người dùng

- **Products**
  - `GET /api/products` - Lấy danh sách sản phẩm
  - `GET /api/products/:id` - Lấy thông tin chi tiết sản phẩm

- **Categories**
  - `GET /api/categories` - Lấy danh sách danh mục

- **Cart**
  - `GET /api/user/cart/get` - Lấy giỏ hàng của người dùng
  - `POST /api/user/cart/add` - Thêm sản phẩm vào giỏ hàng
  - `POST /api/user/cart/update/:id` - Cập nhật số lượng sản phẩm
  - `DELETE /api/user/cart/remove/:id` - Xóa sản phẩm khỏi giỏ hàng

- **Wishlist**
  - `GET /api/user/wishlist/get` - Lấy danh sách yêu thích
  - `POST /api/user/wishlist/add` - Thêm sản phẩm vào wishlist
  - `DELETE /api/user/wishlist/remove/:id` - Xóa sản phẩm khỏi wishlist

- **Checkout**
  - `POST /api/user/checkout/place-order` - Đặt hàng
  - `POST /api/user/checkout/process-payment` - Xử lý thanh toán
  - `POST /api/user/checkout/cash-on-delivery` - Thanh toán khi nhận hàng

- **User Address**
  - `GET /api/user/address/get` - Lấy danh sách địa chỉ
  - `POST /api/user/address` - Thêm địa chỉ mới

## 📊 State Management

Dự án sử dụng Context API của React để quản lý state, được chia thành các context riêng biệt:

- **AuthContext** - Quản lý xác thực người dùng, JWT token
- **ProductsContext** - Quản lý danh sách sản phẩm, lọc, tìm kiếm
- **CartContext** - Quản lý giỏ hàng, thêm/xóa sản phẩm
- **WishlistContext** - Quản lý danh sách yêu thích
- **CheckoutContext** - Quản lý quy trình thanh toán và đặt hàng

## 🔐 Xác thực

Hệ thống xác thực sử dụng JWT (JSON Web Token):

1. Khi đăng nhập/đăng ký thành công, server trả về một JWT token
2. Token được lưu trong localStorage
3. Token được gửi trong header `authorization` của mỗi request yêu cầu xác thực
4. Khi đăng xuất, token được xóa khỏi localStorage

## 📄 Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm thông tin.

---

<div align="center">
  <p>Developed with ❤️ by EyeVi Team</p>
  <p>
    <a href="https://github.com/mthangit/Multi-Agents/tree/dev/Website/Frontend">GitHub</a> •
    <a href="http://eyevi.devsecopstech.click:3000/">Live Demo</a> •
    <a href="duongnguyen4823@gmail.com">Contact</a>
  </p>
</div>
