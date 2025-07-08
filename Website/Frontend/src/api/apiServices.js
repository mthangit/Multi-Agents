import axios from "axios";
import {
  CART_URL,
  PRODUCTS_URL,
  PRODUCTS_PAGINATED_URL,
  LOGIN_URL,
  SIGNUP_URL,
  WISHLIST_URL,
  CATEGORIES_URL,
  CHECKOUT_URL,
  ALL_USER,
  ALL_INVOICE,
  ORDERS_URL,
  USER_ORDERS_URL,
  ORDER_DETAILS_URL,
} from "./apiUrls";

export const loginService = (email, password) =>
  axios.post(LOGIN_URL, { email, password });

export const signupService = (username, email, password) =>
  axios.post(SIGNUP_URL, { username, email, password });

export const getAllUsersService = () => axios.get(ALL_USER);

export const getAllInvoicesService = () => axios.get(ALL_INVOICE);

export const getAllInvoicesDetailsService = (invoiceID) =>
  axios.get(`${ALL_INVOICE}/${invoiceID}`);

export const getAllProductsService = () => axios.get(PRODUCTS_URL);

export const getProductsPaginatedService = (page = 1, limit = 20, search = "", category = "", brand = "") => {
  const params = new URLSearchParams();
  params.append("page", page);
  params.append("limit", limit);
  
  if (search) params.append("search", search);
  if (category) params.append("category", category);
  if (brand) params.append("brand", brand);
  
  return axios.get(`${PRODUCTS_PAGINATED_URL}?${params.toString()}`);
};

export const getProductByIdService = (productId) =>
  //axios.get(`http://34.87.90.190:8000/api/products/${productId}`);
  axios.get(`${PRODUCTS_URL}/${productId}`);

// export const getCartItemsService = (token) =>
//   axios.get(`${CART_URL}/get`, {
//     headers: {
//       authorization: token,
//     },
//   });

export const getCartItemsService = (token) => {
  console.log("Token in Axios Request:", token); // In ra token để kiểm tra
  return axios.get(`${CART_URL}/get`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};

export const postAddProductToCartService = (product, token) =>
  axios.post(
    `${CART_URL}/add`,
    { product },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

export const postUpdateProductQtyCartService = (productId, type, token) => {
  console.log("ProductID of Update:", productId);
  return axios.post(
    `${CART_URL}/update/${productId}`,
    {
      action: {
        type,
      },
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
};

export const deleteProductFromCartService = (productId, token) =>
  axios.delete(`${CART_URL}/remove/${productId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

export const getWishlistItemsService = (token) =>
  axios.get(`${WISHLIST_URL}/get`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

export const postAddProductToWishlistService = (product, token) =>
  axios.post(
    `${WISHLIST_URL}/add`,
    { product },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

export const deleteProductFromWishlistService = (productId, token) =>
  axios.delete(`${WISHLIST_URL}/remove/${productId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

export const getAllCategoriesService = () => axios.get(CATEGORIES_URL);

export const postCashOnDeliveryService = (token) =>
  axios.post(
    `${CHECKOUT_URL}/cash-on-delivery`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

export const processPaymentService = async (paymentMethod, token) => {
  try {
    const response = await axios.post(
      `${CHECKOUT_URL}/process-payment`,
      {
        paymentMethod,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (response.status === 200) {
      // Xử lý kết quả thanh toán thành công nếu cần
      return response.data;
    } else {
      // Xử lý lỗi thanh toán
      throw new Error("Payment failed");
    }
  } catch (error) {
    console.error("Payment error:", error);
    throw error;
  }
};

export const placeOrderService = (orderData, paymentMethod, token) => {
  const headers = token
    ? {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    : {};
  // Thêm thông tin về phương thức thanh toán vào dữ liệu đơn hàng
  const dataWithPaymentMethod = {
    ...orderData,
    paymentMethod,
  };

  return axios.post(
    `${CHECKOUT_URL}/place-order`,
    dataWithPaymentMethod,
    headers
  );
};

export const newAddresses = async (data, token) => {
  try {
    const response = await axios.post(`http://34.87.90.190:8000/api/user/address`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error creating address:", error);
    throw error;
  }
};

export const updateAddressById = async (addressId, data, token) => {
  try {
    const response = await axios.put(`http://34.87.90.190:8000/api/user/address/${addressId}`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error updating address:", error);
    throw error;
  }
};

export const deleteAddressById = async (addressId, token) => {
  try {
    const response = await axios.delete(`http://34.87.90.190:8000/api/user/address/${addressId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error deleting address:", error);
    throw error;
  }
};

export const getAllAddressesService = async (token) => {
  try {
    const response = await axios.get(
      "http://34.87.90.190:8000/api/user/address/get",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching addresses:", error);
    throw error;
  }
};

export const postAddProduct = (product) =>
  axios.post(`http://34.87.90.190:8000/api/admin/addproduct`, { product });

// === ORDERS API SERVICES (không cần token) ===

export const getAllOrdersService = () => axios.get(ORDERS_URL);

export const getUserOrdersService = (userId) => 
  axios.get(`${USER_ORDERS_URL}/${userId}`);

export const getOrderDetailsService = (orderId) => 
  axios.get(`${ORDER_DETAILS_URL}/${orderId}/details`);
