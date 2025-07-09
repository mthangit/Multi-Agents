import { useState } from "react";
import { useAuthContext, useProductsContext } from "../contexts";
// import { useHistory } from "react-router-dom";
import {
  AddressCard,
  AddressForm,
} from "../components";
import Address from "../components/address/Address";
import { useNavigate } from "react-router-dom";

const Profile = () => {
  const navigate = useNavigate();
  const userDetails = localStorage.getItem("userInfo")
    ? JSON.parse(localStorage.getItem("userInfo"))
    : null;
  console.log("userDetails: ", userDetails)
  const { addressList } = useProductsContext();
  const [selectedItem, setSelectedItem] = useState("profile");
  const [addNewAddress, setAddNewAddress] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const { logoutHandler, userInfo, token } = useAuthContext();

  const handleLogOut = () => {
    setLoggingOut(true);
    setTimeout(() => {
      logoutHandler();
      setLoggingOut(false);
    }, 1000);
  };

  return (
    <div className="min-h-[80vh] min-w-md max-w-none m-auto mt-6">
      <section className="h-full p-7 rounded-md shadow-sm bg-white/[0.7] flex w-full">
        <div className="flex-none w-1/4">
          <button
            className={`text-sm mb-3 ${
              selectedItem === "profile"
                ? "bg-[--primary-text-color] text-white"
                : "bg-gray-100"
            } p-5 shadow-sm transition-colors w-full text-left`}
            onClick={() => setSelectedItem("profile")}
          >
            Thông tin cá nhân
          </button>
          <button
            onClick={() => setSelectedItem("address")}
            className={`text-sm mb-3 ${
              selectedItem === "address"
                ? "bg-[--primary-text-color] text-white"
                : "bg-gray-100"
            } p-5 shadow-sm transition-colors w-full text-left`}
          >
            Địa chỉ
          </button>
          <button
            onClick={() => navigate("/orders")}
            className={`text-sm mb-3 bg-gray-100 p-5 shadow-sm transition-colors w-full text-left hover:bg-gray-200`}
          >
            Đơn hàng
          </button>
        </div>
        <div className="flex-1 ml-4">
          {selectedItem === "profile" ? (
            <div className="flex flex-col gap-4 w-full p-5">
              <p>
                <span className="text-gray-600 me-1">Username:</span>
                <span className="break-all">{userDetails?.name}</span>
              </p>
              <p>
                <span className="text-gray-600 me-1">Email:</span>
                <span className="break-all">{userDetails?.email ?? ""}</span>
              </p>
              <hr />
              <button
                disabled={loggingOut}
                className="w-1/2 text-sm bg-rose-600 py-2 px-4 text-white rounded-md hover:bg-rose-700"
                onClick={handleLogOut}
              >
                {loggingOut ? "Logging Out..." : "Logout"}
              </button>
              {userDetails?.is_admin === true && (
                <button
                  className="w-1/2 text-sm bg-blue-600 py-2 px-4 text-white rounded-md hover:bg-blue-700 mt-4"
                  onClick={() => navigate("/adminproduct")}
                >
                  Go to Admin
                </button>
              )}
            </div>
          ) : (
            <section className=" rounded-md shadow-sm bg-white/[0.7] flex flex-col gap-6 w-full h-min">
              <Address isEdit />
            </section>
          )}
        </div>
      </section>
    </div>
  );
};

export default Profile;
