"use client";

import React, { useState, useEffect, useRef } from "react";
import ProductCard from "./product-card";
import { ProductData, useChatApi } from "@/hooks/useChatApi";
import { Package, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "./ui/button";


interface ProductListProps {
  products?: ProductData[];
  productIds?: string[];
  initialDisplay?: number;
  loadMoreCount?: number;
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

const ProductList: React.FC<ProductListProps> = ({
  products: initialProducts,
  productIds,
  initialDisplay = 3,
  loadMoreCount = 5
}) => {
  const [products, setProducts] = useState<ProductData[]>(initialProducts || []);
  const [loading, setLoading] = useState(false);
  const [displayCount, setDisplayCount] = useState(initialDisplay);
  const [isExpanded, setIsExpanded] = useState(false);
  const { getProductsByIds } = useChatApi();
  
  // Refs để theo dõi việc đã fetch dữ liệu hay chưa
  const hasFetchedIdsRef = useRef<boolean>(false);
  const hasFetchedMissingDetailsRef = useRef<boolean>(false);
  const processedProductIdsRef = useRef<Set<string>>(new Set());

  // Xử lý logic hiển thị sản phẩm - lọc ra các sản phẩm hợp lệ
  const validProducts = products.filter(product =>
    product && (product.product_id || product.name) // Đảm bảo có ít nhất product_id hoặc name
  );
  const displayProducts = validProducts.slice(0, displayCount);
  const hasMoreProducts = validProducts.length > displayCount;
  const remainingProducts = validProducts.length - displayCount;

  const handleLoadMore = () => {
    const newCount = Math.min(displayCount + loadMoreCount, validProducts.length);
    setDisplayCount(newCount);
    setIsExpanded(true);
  };

  const handleCollapse = () => {
    setDisplayCount(initialDisplay);
    setIsExpanded(false);
  };
  
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
  
  if (validProducts.length === 0 && !loading) {
    return null;
  }
  
  return (
    <div className="w-full space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Package className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium text-foreground">
          Danh sách sản phẩm ({validProducts.length})
        </span>
      </div>

      {/* Danh sách sản phẩm */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {displayProducts.map((product, index) => (
          <ProductCard
            key={product.product_id || `product-${index}-${product.name || 'unknown'}`}
            product={product}
          />
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

export default ProductList; 