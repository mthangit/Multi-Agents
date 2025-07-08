import React, { useState, useEffect } from "react";
import { getOrderDetailsService } from "../../api/apiServices";
import { format } from "date-fns";

const OrderDetails = ({ orderId, onGoBack }) => {
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!orderId) return;

    const fetchOrderDetails = async () => {
      setLoading(true);
      try {
        const response = await getOrderDetailsService(orderId);
        if (response.status === 200) {
          setOrder(response.data);
          console.log("✅ Đã load chi tiết đơn hàng:", response.data);
        }
      } catch (error) {
        console.error("❌ Lỗi khi load chi tiết đơn hàng:", error);
        setOrder(null);
      } finally {
        setLoading(false);
      }
    };

    fetchOrderDetails();
  }, [orderId]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(amount);
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return format(date, "dd/MM/yyyy HH:mm:ss");
    } catch (error) {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "cancelled":
        return "bg-red-100 text-red-800 border-red-200";
      case "processing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case "pending":
        return "Chờ xử lý";
      case "completed":
        return "Hoàn thành";
      case "cancelled":
        return "Đã hủy";
      case "processing":
        return "Đang xử lý";
      default:
        return status || "Không xác định";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Đang tải chi tiết đơn hàng...</span>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">❌</div>
        <h3 className="text-xl font-semibold text-gray-600 mb-2">
          Không tìm thấy đơn hàng
        </h3>
        <p className="text-gray-500 mb-4">
          Đơn hàng #{orderId} không tồn tại hoặc đã bị xóa
        </p>
        <button
          onClick={onGoBack}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
        >
          Quay lại danh sách
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={onGoBack}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h2 className="text-2xl font-bold text-white">
                Chi tiết đơn hàng #{order.id}
              </h2>
            </div>
            <span
              className={`px-4 py-2 rounded-full text-sm font-medium border-2 ${getStatusColor(
                order.order_status
              )}`}
            >
              {getStatusText(order.order_status)}
            </span>
          </div>
        </div>

        {/* Order Info */}
        <div className="p-6 bg-gray-50 border-b">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="text-sm text-gray-500 font-medium mb-1">Ngày đặt hàng</h3>
              <p className="text-lg font-semibold text-gray-900">
                {formatDate(order.created_at)}
              </p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="text-sm text-gray-500 font-medium mb-1">Tổng số sản phẩm</h3>
              <p className="text-lg font-semibold text-gray-900">
                {order.total_items} sản phẩm
              </p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="text-sm text-gray-500 font-medium mb-1">Tổng tiền</h3>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(order.total_price)}
              </p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="text-sm text-gray-500 font-medium mb-1">Tiền thực tế</h3>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(order.actual_price)}
              </p>
            </div>
          </div>
        </div>

        {/* Customer Info */}
        <div className="p-6 bg-white border-b">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Thông tin giao hàng</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <span className="text-gray-500 w-20">Địa chỉ:</span>
                <span className="font-medium text-gray-900">
                  {order.shipping_address || "Chưa cập nhật"}
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-gray-500 w-20">Điện thoại:</span>
                <span className="font-medium text-gray-900">
                  {order.phone || "Chưa cập nhật"}
                </span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <span className="text-gray-500 w-24">User ID:</span>
                <span className="font-medium text-gray-900">#{order.user_id}</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-gray-500 w-24">Cập nhật:</span>
                <span className="font-medium text-gray-900">
                  {formatDate(order.updated_at)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Products List */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Sản phẩm đã đặt ({order.details?.length || 0})
          </h3>
          
          {order.details && order.details.length > 0 ? (
            <div className="space-y-4">
              {order.details.map((detail) => (
                <div
                  key={detail.id}
                  className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    {/* Product Image */}
                    <div className="flex-shrink-0 w-20 h-20">
                      <img
                        src={detail.product_image_url || detail.product_image || '/placeholder.jpg'}
                        alt={detail.product_name || 'Sản phẩm'}
                        className="w-full h-full object-cover rounded-lg border"
                        onError={(e) => {
                          e.target.src = '/placeholder.jpg';
                        }}
                      />
                    </div>
                    
                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="text-lg font-semibold text-gray-900 truncate">
                        {detail.product_name || `Sản phẩm ID: ${detail.product_id}`}
                      </h4>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        {detail.brand && (
                          <span>Thương hiệu: <span className="font-medium">{detail.brand}</span></span>
                        )}
                        {detail.category && (
                          <span>Loại: <span className="font-medium">{detail.category}</span></span>
                        )}
                      </div>
                    </div>
                    
                    {/* Quantity & Price */}
                    <div className="flex-shrink-0 text-right">
                      <div className="text-lg font-semibold text-gray-900">
                        {formatCurrency(detail.price)}
                      </div>
                      <div className="text-sm text-gray-500">
                        Số lượng: <span className="font-medium">{detail.quantity}</span>
                      </div>
                      <div className="text-sm font-medium text-blue-600">
                        = {formatCurrency(detail.price * detail.quantity)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-2">📦</div>
              <p className="text-gray-500">Không có sản phẩm nào trong đơn hàng này</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t">
          <div className="flex justify-between items-center">
            <button
              onClick={onGoBack}
              className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
            >
              ← Quay lại danh sách
            </button>
            
            <div className="text-right">
              <div className="text-sm text-gray-500">Tổng thanh toán</div>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(order.actual_price)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderDetails; 