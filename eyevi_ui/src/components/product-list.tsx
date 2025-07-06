"use client";

import React, { useState } from "react";
import ProductCard from "./product-card";
import { ProductData } from "@/hooks/useChatApi";
import { ShoppingBag, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "./ui/button";

interface ProductListProps {
  products: ProductData[];
  initialDisplay?: number;
  loadMoreCount?: number;
}

const ProductList: React.FC<ProductListProps> = ({
  products,
  initialDisplay = 3,
  loadMoreCount = 3,
}) => {
  const [displayCount, setDisplayCount] = useState(initialDisplay);

  // Sản phẩm hiển thị hiện tại
  const displayProducts = products.slice(0, displayCount);
  const hasMoreProducts = products.length > displayCount;
  const remainingProducts = products.length - displayCount;
  const isExpanded = displayCount > initialDisplay;

  const handleLoadMore = () => {
    const newCount = Math.min(displayCount + loadMoreCount, products.length);
    setDisplayCount(newCount);
  };

  const handleCollapse = () => {
    setDisplayCount(initialDisplay);
  };

  if (!products || products.length === 0) {
    return null;
  }

  return (
    <div className="w-full space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <ShoppingBag className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium text-foreground">
          Sản phẩm gợi ý ({products.length})
        </span>
      </div>

      {/* Danh sách sản phẩm */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {displayProducts.map((product) => (
          <ProductCard key={product.product_id} product={product} />
        ))}
      </div>

      {/* Nút xem thêm/thu gọn */}
      <div className="flex justify-center pt-2">
        {hasMoreProducts && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoadMore}
            className="flex items-center gap-2 text-sm"
          >
            <ChevronDown className="h-4 w-4" />
            Xem thêm ({remainingProducts} sản phẩm)
          </Button>
        )}
        {isExpanded && (
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

export default ProductList; 