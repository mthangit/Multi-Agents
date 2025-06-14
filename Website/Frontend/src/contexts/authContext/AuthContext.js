import { createContext, useState } from "react";
import { loginService, signupService } from "../../api/apiServices";
import { notify } from "../../utils/utils";
export const AuthContext = createContext();

const AuthContextProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [userInfo, setUserInfo] = useState(
    localStorage.getItem("userInfo")
      ? JSON.parse(localStorage.getItem("userInfo"))
      : null
  );
  const [loggingIn, setLoggingIn] = useState(false);
  const [signingUp, setSigningUp] = useState(false);

  const signupHandler = async ({
    username = "",
    email = "",
    password = "",
  }) => {
    setSigningUp(true);
    try {
      const response = await signupService(username, email, password);
      console.log(response);
      if (response.status === 200 || response.status === 201) {
        localStorage.setItem("token", response?.data?.encodedToken);
        localStorage.setItem(
          "userInfo",
          JSON.stringify(response?.data?.createdUser)
        );
        setToken(response?.data?.encodedToken);
        notify("success", "Đăng ký thành công!!");
      }
    } catch (err) {
      console.log(err);
      notify(
        "error",
        err?.response?.data?.errors
          ? err?.response?.data?.errors[0]
          : "Có lỗi xảy ra!"
      );
    } finally {
      setSigningUp(false);
    }
  };

  const loginHandler = async (data) => {
    setLoggingIn(true);
    try {
      // Nếu data là đối tượng response từ API, xử lý trực tiếp
      if (data?.encodedToken && data?.foundUser) {
        localStorage.setItem("token", data.encodedToken);
        localStorage.setItem("userInfo", JSON.stringify(data.foundUser));
        setToken(data.encodedToken);
        setUserInfo(data.foundUser);
        notify("success", "Đăng nhập thành công!!");
        return;
      }
      
      // Nếu data là thông tin đăng nhập, gọi API
      const { email = "", password = "" } = data;
      const response = await loginService(email, password);
      
      if (response.status === 200 || response.status === 201) {
        localStorage.setItem("token", response?.data?.encodedToken);
        localStorage.setItem(
          "userInfo",
          JSON.stringify(response?.data?.foundUser)
        );
        setToken(response?.data?.encodedToken);
        setUserInfo(response?.data?.foundUser);
        notify("success", "Đăng nhập thành công!!");
      } else if (response.status === 401) {
        notify("error", "Có lỗi khi đăng nhập!!");
      }
    } catch (err) {
      console.log(err);
      notify(
        "error",
        err?.response?.data?.errors
          ? err?.response?.data?.errors[0]
          : "Có lỗi xảy ra khi đăng nhập!"
      );
    } finally {
      setLoggingIn(false);
    }
  };

  const logoutHandler = () => {
    // Xóa token và thông tin người dùng khỏi localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
    
    // Cập nhật state
    setToken(null);
    setUserInfo(null);
    
    // Thông báo đăng xuất thành công
    notify("info", "Đăng xuất thành công!!", 100);
  };
  return (
    <AuthContext.Provider
      value={{
        token,
        loggingIn,
        loginHandler,
        logoutHandler,
        signupHandler,
        signingUp,
        userInfo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContextProvider;
