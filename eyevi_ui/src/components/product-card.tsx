"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { ProductData, useChatApi } from "@/hooks/useChatApi";
import { Button } from "./ui/button";
import { useChatContext } from "./chat-container";

interface ProductCardProps {
  product: ProductData | null;
  productId?: string;
}

const ProductCard: React.FC<ProductCardProps> = ({ product: initialProduct, productId }) => {
  const [product, setProduct] = useState<ProductData | null>(initialProduct);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getProductById } = useChatApi();
  const { setChatInputMessage } = useChatContext();
  
  // Sử dụng useRef để theo dõi việc đã fetch dữ liệu hay chưa
  const hasFetchedRef = useRef<boolean>(false);
  const hasFetchedDetailsRef = useRef<boolean>(false);
  
  // Xử lý trường hợp có productId nhưng không có initialProduct
  useEffect(() => {
    // Nếu đã fetch rồi hoặc không có productId, không cần fetch
    if (hasFetchedRef.current || !productId) return;
    
    // Nếu đã có initialProduct với đầy đủ thông tin, không cần fetch
    if (initialProduct && initialProduct.name && initialProduct.image_url) {
      hasFetchedRef.current = true;
      return;
    }
    
    const fetchProduct = async () => {
      setLoading(true);
      try {
        console.log(`Fetching product with ID: ${productId}`);
        const data = await getProductById(productId);
        console.log("API Product data:", data);
        
        if (data) {
          // Chuyển đổi id thành product_id để phù hợp với ProductData interface
          const formattedData: ProductData = {
            ...data,
            product_id: data.id,
            price: data.newPrice ? data.newPrice.toString() : undefined,
            image_url: data.image_url || (data.images ? JSON.parse(data.images)[0] : undefined)
          };
          setProduct(formattedData);
          hasFetchedRef.current = true;
        } else {
          setError("Không tìm thấy thông tin sản phẩm");
        }
      } catch (err) {
        setError("Lỗi khi tải thông tin sản phẩm");
        console.error("Lỗi fetch product:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProduct();
  }, [productId, initialProduct, getProductById]);

  // Xử lý trường hợp có initialProduct nhưng không có hình ảnh
  useEffect(() => {
    // Nếu đã fetch chi tiết rồi, không cần fetch lại
    if (hasFetchedDetailsRef.current) return;
    
    // Nếu không có product hoặc đã có hình ảnh, không cần fetch
    if (!product || product.image_url) {
      hasFetchedDetailsRef.current = true;
      return;
    }
    
    // Nếu không có product_id, không thể fetch
    if (!product.product_id) {
      hasFetchedDetailsRef.current = true;
      return;
    }
    
    const fetchProductDetails = async () => {
      setLoading(true);
      try {
        console.log(`Fetching additional details for product ID: ${product.product_id}`);
        const data = await getProductById(product.product_id);
        console.log("Additional product data:", data);
        
        if (data) {
          // Cập nhật thông tin sản phẩm với dữ liệu mới
          let imageUrl = data.image_url;
          
          // Xử lý trường images nếu có
          if (!imageUrl && data.images) {
            try {
              const parsedImages = JSON.parse(data.images);
              if (Array.isArray(parsedImages) && parsedImages.length > 0) {
                imageUrl = parsedImages[0];
              }
            } catch (e) {
              console.error("Lỗi khi parse chuỗi JSON images:", e);
            }
          }
          
          setProduct(prev => {
            if (!prev) return null;
            return {
              ...prev,
              name: data.name || prev.name,
              price: data.newPrice ? (data.newPrice).toString() : prev.price,
              image_url: imageUrl || prev.image_url
            };
          });
        }
      } catch (err) {
        console.error("Lỗi khi tải thông tin bổ sung cho sản phẩm:", err);
      } finally {
        setLoading(false);
        hasFetchedDetailsRef.current = true;
      }
    };
    
    fetchProductDetails();
  }, [product?.product_id, getProductById]);
  
  // Xử lý sự kiện khi click vào nút Mua hàng
  const handleBuyProduct = () => {
    if (product) {
      const productId = product.product_id;
      const productName = product.name || "Sản phẩm kính mắt";
      setChatInputMessage(`Tôi muốn mua sản phẩm ${productName} với id ${productId}`);
    }
  };
  
  if (loading) {
    return (
      <div className="flex flex-col w-full max-w-[220px] h-[300px] rounded-lg border border-border overflow-hidden bg-card animate-pulse">
        <div className="h-[150px] w-full bg-muted"></div>
        <div className="p-3 flex flex-col gap-2">
          <div className="h-4 bg-muted rounded w-2/3"></div>
          <div className="h-8 bg-muted rounded"></div>
          <div className="h-4 bg-muted rounded w-1/2"></div>
          <div className="mt-2 flex items-center justify-between">
            <div className="h-5 bg-muted rounded w-1/3"></div>
            <div className="h-7 bg-muted rounded w-1/4"></div>
          </div>
        </div>
      </div>
    );
  }
  
  if (error || !product) {
    return (
      <div className="flex flex-col w-full max-w-[220px] rounded-lg border border-border overflow-hidden bg-card p-4 items-center justify-center text-center">
        <p className="text-sm text-red-500">{error || "Không có thông tin sản phẩm"}</p>
      </div>
    );
  }
  
  // Xử lý hình ảnh sản phẩm
  let imageUrl = product.image_url;
  console.log("Product data:", product);
  console.log("Image URL:", imageUrl);
  
  // Nếu có trường images dạng chuỗi JSON, parse và lấy ảnh đầu tiên
  if (!imageUrl && product.images && typeof product.images === 'string') {
    try {
      const parsedImages = JSON.parse(product.images);
      if (Array.isArray(parsedImages) && parsedImages.length > 0) {
        imageUrl = parsedImages[0];
      }
    } catch (e) {
      console.error("Lỗi khi parse chuỗi JSON images:", e);
    }
  }
  
  // Fallback nếu không có ảnh
  if (!imageUrl) {
    imageUrl = "https://placehold.co/200x150?text=Kính+mắt";
  }
  
  return (
    <div className="flex flex-col w-full max-w-[220px] rounded-lg border border-border overflow-hidden bg-card">
      <div className="relative h-[150px] w-full bg-muted">
        <Image
          src={imageUrl}
          alt={product.name || "Sản phẩm"}
          fill
          className="object-cover"
          sizes="(max-width: 220px) 100vw, 220px"
        />
      </div>
      
      <div className="p-3 flex flex-col gap-1">
        <div className="flex items-center gap-1">
          <span className="text-xs font-medium text-muted-foreground">{product.brand || "Thương hiệu"}</span>
          {product.gender && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
              {product.gender === "Man" ? "Nam" : product.gender === "Woman" ? "Nữ" : "Unisex"}
            </span>
          )}
        </div>
        
        <h3 className="font-medium text-sm line-clamp-2 h-10" title={product.name}>
          {product.name || "Sản phẩm kính mắt"}
        </h3>
        
        <div className="flex items-center gap-2 mt-1">
          {product.color && (
            <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
              {product.color}
            </span>
          )}
          {product.frameShape && (
            <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
              {product.frameShape}
            </span>
          )}
        </div>
        
        <div className="mt-2 flex items-center justify-between">
          <span className="font-medium text-primary">
            {product.price ? `${parseInt(product.price).toLocaleString('vi-VN')}₫` : "Liên hệ"}
          </span>
          <Button 
            size="sm" 
            variant="outline" 
            className="text-xs h-7"
            onClick={handleBuyProduct}
          >
            Mua hàng
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard; 