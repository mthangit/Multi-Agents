"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import ProductCard from "./product-card";
import { ProductData, useChatApi } from "@/hooks/useChatApi";
import { X } from "lucide-react";
import { useChatContext } from "./chat-container";

interface ProductListProps {
  products?: ProductData[];
  productIds?: string[];
  maxDisplay?: number;
}

// Interface cho dữ liệu sản phẩm từ API
interface ApiProduct {
  id: string;
  name: string;
  brand?: string;
  category?: string;
  color?: string;
  price?: string;
  description?: string;
  frameMaterial?: string;
  frameShape?: string;
  gender?: string;
  image_url?: string;
  images?: string;
  image?: string;
  weight?: number;
  quantity?: number;
  rating?: number;
  newPrice?: number;
  trending?: boolean;
  lensMaterial?: string;
  lensFeatures?: string;
  lensWidth?: number;
  bridgeWidth?: number;
  templeLength?: number;
  availability?: boolean;
  stock?: number;
}

const ProductList: React.FC<ProductListProps> = ({ products: initialProducts, productIds, maxDisplay = 5 }) => {
  const [products, setProducts] = useState<ProductData[]>(initialProducts || []);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(true);
  const { getProductsByIds } = useChatApi();
  const { setChatInputMessage } = useChatContext();
  
  // Refs để theo dõi việc đã fetch dữ liệu hay chưa
  const hasFetchedIdsRef = useRef<boolean>(false);
  const hasFetchedMissingDetailsRef = useRef<boolean>(false);
  const processedProductIdsRef = useRef<Set<string>>(new Set());
  
  // Nếu có initialProducts, sử dụng chúng làm dữ liệu ban đầu
  useEffect(() => {
    if (initialProducts && initialProducts.length > 0) {
      setProducts(initialProducts);
      
      // Lưu lại các product_id đã xử lý
      initialProducts.forEach(product => {
        if (product.product_id) {
          processedProductIdsRef.current.add(product.product_id);
        }
      });
    }
  }, [initialProducts]);
  
  // Xử lý trường hợp có productIds
  useEffect(() => {
    // Nếu không có productIds hoặc đã fetch rồi, không cần fetch
    if (!productIds || productIds.length === 0 || hasFetchedIdsRef.current) {
      return;
    }
    
    // Lọc ra những ID chưa được xử lý
    const newProductIds = productIds.filter(id => !processedProductIdsRef.current.has(id));
    
    // Nếu không có ID mới, không cần fetch
    if (newProductIds.length === 0) {
      hasFetchedIdsRef.current = true;
      return;
    }
    
    const fetchProducts = async () => {
      setLoading(true);
      try {
        console.log("Fetching products with IDs:", newProductIds);
        const data = await getProductsByIds(newProductIds);
        console.log("API Products data:", data);
        
        if (data && data.length > 0) {
          // Chuyển đổi dữ liệu API thành ProductData
          const formattedData: ProductData[] = data.map((item: ApiProduct) => {
            // Xử lý hình ảnh: ưu tiên image_url, nếu không có thì lấy ảnh đầu tiên từ mảng images
            let imageUrl = item.image_url;
            if (!imageUrl && item.images) {
              try {
                const parsedImages = JSON.parse(item.images);
                if (Array.isArray(parsedImages) && parsedImages.length > 0) {
                  imageUrl = parsedImages[0];
                }
              } catch (e) {
                console.error("Lỗi khi parse chuỗi JSON images:", e);
              }
            }
            
            // Đánh dấu ID đã được xử lý
            if (item.id) {
              processedProductIdsRef.current.add(item.id);
            }
            
            return {
              product_id: item.id,
              name: item.name,
              brand: item.brand,
              category: item.category,
              color: item.color,
              price: item.newPrice ? item.newPrice.toString() : item.price,
              description: item.description,
              frameMaterial: item.frameMaterial,
              frameShape: item.frameShape,
              gender: item.gender,
              image_url: imageUrl,
              images: item.images,
              type: item.category,
              newPrice: item.newPrice
            };
          });
          
          // Kết hợp với sản phẩm hiện có
          setProducts(prevProducts => {
            // Lọc ra các sản phẩm không trùng lặp
            const existingIds = new Set(prevProducts.map(p => p.product_id));
            const newProducts = formattedData.filter(p => !existingIds.has(p.product_id));
            return [...prevProducts, ...newProducts];
          });
        }
      } catch (err) {
        console.error("Lỗi khi tải danh sách sản phẩm:", err);
      } finally {
        setLoading(false);
        hasFetchedIdsRef.current = true;
      }
    };
    
    fetchProducts();
  }, [productIds, getProductsByIds]);
  
  // Xử lý trường hợp có sản phẩm thiếu thông tin
  useEffect(() => {
    // Nếu đã fetch chi tiết rồi hoặc không có sản phẩm, không cần fetch
    if (hasFetchedMissingDetailsRef.current || !products || products.length === 0) {
      return;
    }
    
    // Kiểm tra các sản phẩm thiếu thông tin
    const incompleteProducts = products.filter(
      p => p.product_id && (!p.name || !p.image_url)
    );
    
    if (incompleteProducts.length === 0) {
      hasFetchedMissingDetailsRef.current = true;
      return;
    }
    
    const fetchMissingDetails = async () => {
      // Lấy danh sách ID sản phẩm cần bổ sung thông tin
      const idsToFetch = incompleteProducts.map(p => p.product_id);
      console.log("Fetching missing details for products:", idsToFetch);
      
      setLoading(true);
      try {
        const data = await getProductsByIds(idsToFetch);
        console.log("API response for missing details:", data);
        
        if (data && data.length > 0) {
          // Cập nhật thông tin cho các sản phẩm
          setProducts(prevProducts => {
            const updatedProducts = [...prevProducts];
            
            data.forEach((apiProduct: ApiProduct) => {
              const index = updatedProducts.findIndex(p => p.product_id === apiProduct.id);
              if (index !== -1) {
                // Xử lý hình ảnh
                let imageUrl = apiProduct.image_url;
                if (!imageUrl && apiProduct.images) {
                  try {
                    const parsedImages = JSON.parse(apiProduct.images);
                    if (Array.isArray(parsedImages) && parsedImages.length > 0) {
                      imageUrl = parsedImages[0];
                    }
                  } catch (e) {
                    console.error("Lỗi khi parse chuỗi JSON images:", e);
                  }
                }
                
                // Cập nhật thông tin sản phẩm
                updatedProducts[index] = {
                  ...updatedProducts[index],
                  name: apiProduct.name || updatedProducts[index].name,
                  price: apiProduct.newPrice ? apiProduct.newPrice.toString() : updatedProducts[index].price,
                  image_url: imageUrl || updatedProducts[index].image_url
                };
              }
            });
            
            return updatedProducts;
          });
        }
      } catch (err) {
        console.error("Lỗi khi tải thông tin bổ sung cho sản phẩm:", err);
      } finally {
        setLoading(false);
        hasFetchedMissingDetailsRef.current = true;
      }
    };
    
    fetchMissingDetails();
  }, [products, getProductsByIds]);
  
  // Xử lý ẩn danh sách sản phẩm
  const handleHideProductList = useCallback(() => {
    setVisible(false);
  }, []);
  
  // Xử lý khi click vào nút "Xem thêm"
  const handleViewMore = useCallback(() => {
    if (products.length > 0) {
      // Tạo một tin nhắn liệt kê tất cả sản phẩm
      const productList = products
        .slice(maxDisplay)
        .map(p => `${p.name || 'Sản phẩm kính mắt'} (ID: ${p.product_id})`)
        .join(', ');
      
      setChatInputMessage(`Tôi muốn xem thêm thông tin về các sản phẩm: ${productList}`);
    }
  }, [products, maxDisplay, setChatInputMessage]);
  
  // Nếu đã ẩn, không hiển thị gì cả
  if (!visible) {
    return null;
  }
  
  // Giới hạn số lượng sản phẩm hiển thị
  const displayProducts = products.slice(0, maxDisplay);
  
  if (loading && products.length === 0) {
    return (
      <div className="w-full py-3 px-4 border-t border-border">
        <h3 className="text-sm font-medium mb-3">Đang tải sản phẩm...</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div 
              key={`skeleton-${index}`} 
              className="flex flex-col w-full max-w-[220px] h-[300px] rounded-lg border border-border overflow-hidden bg-card animate-pulse"
            >
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
          ))}
        </div>
      </div>
    );
  }
  
  if (products.length === 0 && !loading) {
    return null;
  }
  
  return (
    <div className="w-full py-3 px-4 border-t border-border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Danh sách sản phẩm ({products.length})</h3>
        <button 
          onClick={handleHideProductList}
          className="p-1 rounded-full hover:bg-muted transition-colors"
          aria-label="Ẩn danh sách sản phẩm"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {displayProducts.map((product) => (
          <ProductCard key={product.product_id} product={product} />
        ))}
      </div>
      {products.length > maxDisplay && (
        <div className="mt-3 text-center">
          <button 
            className="text-sm text-primary hover:underline"
            onClick={handleViewMore}
          >
            Xem thêm {products.length - maxDisplay} sản phẩm khác
          </button>
        </div>
      )}
    </div>
  );
};

export default ProductList; 