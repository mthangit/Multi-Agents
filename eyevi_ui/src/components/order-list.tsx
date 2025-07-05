"use client";

import React, { useState } from "react";
import OrderCard from "./order-card";
import { OrderData } from "@/hooks/useChatApi";
import { ShoppingBag, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "./ui/button";

interface OrderListProps {
  orders: OrderData[];
  initialDisplay?: number;
  loadMoreCount?: number;
}

const OrderList: React.FC<OrderListProps> = ({ 
  orders, 
  initialDisplay = 2,
  loadMoreCount = 5 
}) => {
  const [displayCount, setDisplayCount] = useState(initialDisplay);
  const [isExpanded, setIsExpanded] = useState(false);

  // Sắp xếp đơn hàng theo thời gian tạo (mới nhất trước)
  const sortedOrders = [...orders].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  // Lọc và giới hạn số lượng đơn hàng hiển thị
  const displayOrders = sortedOrders.slice(0, displayCount);
  const hasMoreOrders = sortedOrders.length > displayCount;
  const remainingOrders = sortedOrders.length - displayCount;

  const handleLoadMore = () => {
    const newCount = Math.min(displayCount + loadMoreCount, sortedOrders.length);
    setDisplayCount(newCount);
    setIsExpanded(true);
  };

  const handleCollapse = () => {
    setDisplayCount(initialDisplay);
    setIsExpanded(false);
  };

  if (!orders || orders.length === 0) {
    return null;
  }

  return (
    <div className="w-full space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <ShoppingBag className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium text-foreground">
          Đơn hàng của bạn ({orders.length})
        </span>
      </div>

      {/* Danh sách đơn hàng */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {displayOrders.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>

      {/* Nút xem thêm/thu gọn */}
      <div className="flex justify-center pt-2">
        {hasMoreOrders && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoadMore}
            className="flex items-center gap-2 text-sm"
          >
            <ChevronDown className="h-4 w-4" />
            Xem thêm ({remainingOrders} đơn hàng)
          </Button>
        )}
        
        {isExpanded && displayCount > initialDisplay && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleCollapse}
            className="flex items-center gap-2 text-sm ml-2"
          >
            <ChevronUp className="h-4 w-4" />
            Thu gọn
          </Button>
        )}
      </div>
    </div>
  );
};

export default OrderList; 