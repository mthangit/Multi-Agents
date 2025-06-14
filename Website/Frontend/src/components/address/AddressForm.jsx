import React, { useState, useEffect, useReducer } from "react";
import { useProductsContext, useAuthContext } from "../../contexts";
import { v4 as uuid } from "uuid";
import axios from "axios";
import { newAddresses, updateAddressById } from "../../api/apiServices";
import { productsReducer, initialState } from "../../reducers/productsReducer";
import { addressTypes } from "../../utils/actionTypes";

const AddressForm = ({ setShowAddressForm, editAddress, setEditAddress }) => {
  const { addAddress, setCurrentAddress, updateAddress } = useProductsContext();
  const [newAddress, setNewAddress] = useState(
    editAddress
      ? editAddress
      : {
          name: "",
          phone: "",
          address: "",
          country: "",
          city: "",
          is_default: false,
          state: "active",
        }
  );
  const [cities, setCities] = useState([]);
  const [districts, setDistricts] = useState([]);
  const { token } = useAuthContext();
  const [state, dispatch] = useReducer(productsReducer, initialState);
  
  useEffect(() => {
    // Lấy dữ liệu tỉnh thành từ API
    axios
      .get(
        "https://raw.githubusercontent.com/kenzouno1/DiaGioiHanhChinhVN/master/data.json"
      )
      .then((response) => {
        setCities(response.data);
      })
      .catch((error) => {
        console.error("Error fetching cities:", error);
      });
  }, []);

  const handleCityChange = (selectedCityId) => {
    // Lọc dữ liệu quận huyện dựa trên tỉnh thành được chọn
    const selectedCity = cities.find((city) => city.Id === selectedCityId);
    setDistricts(selectedCity ? selectedCity.Districts : []);
  };

  const handleAddress = async (data, token) => {
    console.log("data address", data);
    console.log("data token", token);
    try {
      let response;
      if (editAddress) {
        // Nếu đang chỉnh sửa, gọi API cập nhật
        response = await updateAddressById(editAddress.id, data, token);
      } else {
        // Nếu đang thêm mới, gọi API tạo mới
        response = await newAddresses(data, token);
      }
      
      console.log("API response:", response);
      return response;
    } catch (error) {
      console.error("Error during API request:", error);
      if (error.response) {
        // Request was made and server responded with a status code
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
      } else if (error.request) {
        // Request was made but no response was received
        console.error("No response received");
      } else {
        // Something happened in setting up the request
        console.error("Error setting up the request:", error.message);
      }
      throw error;
    }
  };

  const submitHandler = async (e) => {
    e.preventDefault();

    // Chuyển đổi giá trị city và country về dạng chuỗi
    const cityString =
      cities.find((city) => city.Id === newAddress.city)?.Name || newAddress.city;
    const countryString =
      districts.find((district) => district.Id === newAddress.country)?.Name || newAddress.country;

    // Tạo một bản sao của newAddress với giá trị city và country được cập nhật
    const updatedAddress = {
      ...newAddress,
      city: cityString,
      country: countryString,
    };
    console.log("updatedAddress", updatedAddress);

    try {
      // Gọi API để lưu địa chỉ
      const response = await handleAddress(updatedAddress, token);
      
      // Cập nhật state local
      if (editAddress) {
        updateAddress(editAddress.id, response || updatedAddress);
      } else {
        // Nếu có response từ API, sử dụng ID từ response
        if (response && response.id) {
          addAddress({...updatedAddress, id: response.id});
          setCurrentAddress({...updatedAddress, id: response.id});
        } else {
          // Fallback nếu không có response
          const addressWithId = {...updatedAddress, id: uuid()};
          addAddress(addressWithId);
          setCurrentAddress(addressWithId);
        }
      }
      
      setShowAddressForm(false);
    } catch (error) {
      console.error("Failed to save address:", error);
      // Có thể hiển thị thông báo lỗi cho người dùng ở đây
    }
  };

  return (
    <form
      action=""
      className="flex flex-col gap-3 p-5 bg-gray-50 shadow-sm"
      onSubmit={submitHandler}
    >
      <div className="flex gap-2 flex-wrap">
        <label className="flex flex-1 flex-col">
          Họ và tên
          <input
            required
            type="text"
            className="border rounded-md p-1.5 shadow-sm"
            onChange={(e) =>
              setNewAddress({ ...newAddress, name: e.target.value })
            }
            value={newAddress.name}
          />
        </label>
        <label className="flex flex-1 flex-col">
          Số điện thoại
          <input
            required
            type="number"
            className="border rounded-md p-1.5 shadow-sm"
            onChange={(e) =>
              setNewAddress({ ...newAddress, phone: e.target.value })
            }
            value={newAddress.phone}
          />
        </label>
      </div>
      <label className="flex flex-col">
        Địa chỉ nhà
        <input
          required
          type="text"
          className="border rounded-md p-1.5 shadow-sm"
          onChange={(e) =>
            setNewAddress({ ...newAddress, address: e.target.value })
          }
          value={newAddress.address}
        />
      </label>
      <label className="flex flex-1 flex-col">
        Thành Phố/Tỉnh
        <select
          required
          className="border rounded-md p-1.5 shadow-sm"
          onChange={(e) => {
            setNewAddress({ ...newAddress, city: e.target.value });
            handleCityChange(e.target.value);
          }}
          value={newAddress.city}
        >
          <option value="" disabled>
            Chọn tỉnh thành
          </option>
          {cities.map((city) => (
            <option key={city.Id} value={city.Id}>
              {city.Name}
            </option>
          ))}
        </select>
      </label>
      <div className="flex gap-2 flex-wrap">
        <label className="flex flex-1 flex-col">
          Quận/Huyện
          <select
            required
            className="border rounded-md p-1.5 shadow-sm"
            onChange={(e) =>
              setNewAddress({ ...newAddress, country: e.target.value })
            }
            value={newAddress.country}
          >
            <option value="" disabled>
              Chọn quận huyện
            </option>
            {districts.map((district) => (
              <option key={district.Id} value={district.Id}>
                {district.Name}
              </option>
            ))}
          </select>
        </label>
      </div>
      
      <div className="flex items-center gap-2 mt-2">
        <input
          type="checkbox"
          id="default-address"
          checked={newAddress.is_default}
          onChange={(e) =>
            setNewAddress({ ...newAddress, is_default: e.target.checked })
          }
        />
        <label htmlFor="default-address">Đặt làm địa chỉ mặc định</label>
      </div>

      <div className="flex gap-3 mt-3 flex-wrap">
        {!editAddress && (
          <button
            type="button"
            className="btn-rounded-secondary rounded-full flex items-center gap-2 text-sm p-1"
            onClick={() => {
              setNewAddress({
                name: "Nguyễn Dương",
                phone: "0327879401",
                address: "KTX Khu B - ĐHQG TP.HCM",
                country: "Thủ Đức",
                city: "Hồ Chí Minh",
                is_default: false,
                state: "active"
              });
              if (editAddress) {
                setEditAddress(null);
              }
            }}
          >
            Địa chỉ ảo
          </button>
        )}
        <button
          type="button"
          className="btn-rounded-secondary rounded-full flex items-center gap-2 text-sm"
          onClick={() => {
            setShowAddressForm(false);
            setNewAddress({
              name: "",
              phone: "",
              address: "",
              country: "",
              city: "",
              state: "active",
              is_default: false
            });
            if (editAddress) {
              setEditAddress(null);
            }
          }}
        >
          Hủy bỏ
        </button>
        <button
          type="submit"
          className="btn-rounded-primary rounded-full flex items-center gap-2 text-sm"
        >
          Lưu
        </button>
      </div>
    </form>
  );
};

export default AddressForm;
