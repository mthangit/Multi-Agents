import React from "react";
import { useNavigate } from "react-router-dom";
import OrderList from "../components/orders/OrderList";

const Orders = () => {
  const navigate = useNavigate();
  
  // Lấy thông tin user từ localStorage
  const userDetails = localStorage.getItem("userInfo")
    ? JSON.parse(localStorage.getItem("userInfo"))
    : null;

  const handleSelectOrder = (orderId) => {
    navigate(`/order/${orderId}`);
  };

  return (
    <div className="min-h-[80vh] max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Đơn hàng của tôi</h1>
        <p className="text-gray-600">Xem và theo dõi tất cả đơn hàng của bạn</p>
      </div>
      
      <OrderList 
        onSelectOrder={handleSelectOrder} 
        userId={userDetails?.id || 1} 
      />
    </div>
  );
};

export default Orders;
