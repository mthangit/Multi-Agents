import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { Link } from "react-router-dom";
import bannerHero from "../assets/bannerHero.jpg";
import { Logo } from "../components";
import { useAuthContext } from "../contexts";
import api from "../utils/axios-config"; // Import tệp axios-config.js đã cấu hình
import axios from "axios";
import { notify } from "../utils/utils";

const Login = () => {
  const { loginHandler, token, loggingIn, userInfo } = useAuthContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [loginCredentials, setLoginCredentials] = useState({
    email: "",
    password: "",
  });
  useEffect(() => {
    let id;
    if (token) {
      id = setTimeout(() => {
        navigate(location?.state?.from?.pathname ?? "/");
      }, 1000);
    }

    return () => {
      clearInterval(id);
    };
  }, [token]);

  // Đánh dấu hàm là async để sử dụng await
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // 1. Gọi API login để lấy thông tin người dùng
      const userResponse = await api.post(
        "http://34.87.90.190:8000/api/login",
        loginCredentials
      );
      
      if (userResponse.status !== 200) {
        notify("error", "Đăng nhập thất bại!");
        return;
      }
      
      const userData = userResponse.data;
      
      // 2. Gọi API token để lấy token xác thực
      // API token yêu cầu dữ liệu dưới dạng form-urlencoded với username và password
      const formData = new FormData();
      formData.append('username', loginCredentials.email); // username là email
      formData.append('password', loginCredentials.password);
      
      const tokenResponse = await axios.post(
        "http://34.87.90.190:8000/api/token",
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      if (tokenResponse.status === 200) {
        // Kết hợp thông tin từ cả hai API
        const combinedData = {
          encodedToken: tokenResponse.data.access_token,
          foundUser: userData.foundUser
        };
        
        // Lưu token và thông tin người dùng vào localStorage
        localStorage.setItem("token", tokenResponse.data.access_token);
        localStorage.setItem("userInfo", JSON.stringify(userData.foundUser));
        
        // Gọi loginHandler để cập nhật trạng thái trong context
        loginHandler(combinedData);
        
        // Thông báo đăng nhập thành công
        notify("success", "Đăng nhập thành công!");
        
        // Chuyển hướng người dùng
        if (userData.foundUser.is_admin === true) {
          navigate("/adminproduct");
          return;
        }
        navigate("/");
      }
    } catch (error) {
      console.error("Lỗi đăng nhập:", error);
      notify("error", "Đăng nhập thất bại! Vui lòng kiểm tra email và mật khẩu.");
    }
  };

  return (
    <main className="grid  grid-rows-1 lg:grid-cols-2 w-full  h-screen m-auto">
      <section className=" hidden lg:block max-h-screen  rounded-lg">
        <img src={bannerHero} alt="" className="w-full h-full object-cover" />
      </section>
      <div className="flex items-center justify-center w-full px-5">
        <section className="px-7 py-10 rounded-md shadow-md bg-white/[0.7] flex flex-col gap-6 w-full max-w-lg">
          <Logo />
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold mb-3 ">Đăng nhập</h1>

            <form
              action=""
              className="flex flex-col gap-3"
              onSubmit={handleSubmit}
            >
              <label className="flex flex-col">
                Email
                <input
                  type="email"
                  className="border rounded-md p-1.5 shadow-sm"
                  value={loginCredentials.email}
                  onChange={(e) =>
                    setLoginCredentials({
                      ...loginCredentials,
                      email: e.target.value,
                    })
                  }
                />
              </label>
              <label className="flex flex-col">
                Mật khẩu
                <input
                  type="password"
                  className="border rounded-md p-1.5 shadow-sm"
                  value={loginCredentials.password}
                  onChange={(e) =>
                    setLoginCredentials({
                      ...loginCredentials,
                      password: e.target.value,
                    })
                  }
                />
              </label>
              <div className="w-full py-2   flex flex-col gap-4 items-center ">
                <button
                  className="btn-primary w-2/3 text-lg text-center "
                  disabled={
                    loggingIn ||
                    !loginCredentials.email ||
                    !loginCredentials.password
                  }
                >
                  {loggingIn ? "Đang đăng nhập..." : "Đăng nhập"}
                </button>
                <button
                  type="button"
                  className="btn-secondary w-2/3 text-sm md:text-base text-center"
                  onClick={() => {
                    setLoginCredentials({
                      ...loginCredentials,
                      email: "duong@example.com",
                      password: "duong2003",
                    });
                  }}
                >
                  Đăng nhập với tài khoản mẫu
                </button>
                <Link to="/signup" className="underline text-gray-600">
                  Đăng ký tài khoản
                </Link>
              </div>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
};

export default Login;
