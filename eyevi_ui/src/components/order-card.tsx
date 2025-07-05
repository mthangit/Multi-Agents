"use client";

import React from "react";
import { OrderData } from "@/hooks/useChatApi";
import { Package, MapPin, Phone, User, Calendar, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";

interface OrderCardProps {
  order: OrderData;
}

const OrderCard: React.FC<OrderCardProps> = ({ order }) => {
  // Format giá tiền
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(price);
  };

  // Format ngày tháng
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Xác định màu và text cho trạng thái đơn hàng
  const getOrderStatusInfo = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return {
          text: 'Chờ xử lý',
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
        };
      case 'processing':
        return {
          text: 'Đang xử lý',
          className: 'bg-blue-100 text-blue-800 border-blue-200'
        };
      case 'shipped':
        return {
          text: 'Đã giao hàng',
          className: 'bg-purple-100 text-purple-800 border-purple-200'
        };
      case 'delivered':
        return {
          text: 'Đã giao thành công',
          className: 'bg-green-100 text-green-800 border-green-200'
        };
      case 'cancelled':
        return {
          text: 'Đã hủy',
          className: 'bg-red-100 text-red-800 border-red-200'
        };
      default:
        return {
          text: status,
          className: 'bg-gray-100 text-gray-800 border-gray-200'
        };
    }
  };

  const statusInfo = getOrderStatusInfo(order.order_status);

  return (
    <div className="w-full rounded-lg border border-border bg-card p-4 shadow-sm">
      {/* Header với order ID và status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-primary" />
          <h3 className="font-semibold text-sm text-foreground">
            #{order.id}
          </h3>
        </div>
        <span 
          className={cn(
            "px-2 py-1 rounded-full text-xs font-medium border",
            statusInfo.className
          )}
        >
          {statusInfo.text}
        </span>
      </div>

      {/* Thông tin khách hàng rút gọn */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium truncate">{order.user_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <Phone className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{order.phone}</span>
        </div>
        <div className="flex items-start gap-2">
          <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
          <span className="text-sm text-muted-foreground line-clamp-2">{order.shipping_address}</span>
        </div>
      </div>

      {/* Thông tin đơn hàng */}
      <div className="space-y-2 mb-4 p-3 bg-muted/50 rounded-md">
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Số lượng:</span>
          <span className="text-sm font-medium">{order.total_items} SP</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Thành tiền:</span>
          <span className="text-sm font-bold text-primary">
            {formatPrice(order.actual_price)}
          </span>
        </div>
      </div>

      {/* Ngày tạo */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span className="truncate">{formatDate(order.created_at)}</span>
      </div>
    </div>
  );
};

export default OrderCard; 