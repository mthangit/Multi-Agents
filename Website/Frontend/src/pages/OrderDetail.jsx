import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import OrderDetails from "../components/orders/OrderDetails";

const OrderDetail = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate("/orders");
  };

  return (
    <div className="min-h-[80vh] max-w-6xl mx-auto px-4 py-8">
      <OrderDetails
        orderId={parseInt(orderId)}
        onGoBack={handleGoBack}
      />
    </div>
  );
};

export default OrderDetail; 