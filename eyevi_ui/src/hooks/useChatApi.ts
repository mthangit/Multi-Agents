import { useState, useEffect, useCallback } from 'react';

// Định nghĩa user_id cố định
export const FIXED_USER_ID = 1;

// Cache cho sản phẩm đã fetch với thời gian sống
interface ProductCacheItem {
  id: string;
  name: string;
  images?: string;
  newPrice?: number;
  image_url?: string;
  brand?: string;
  category?: string;
  color?: string;
  price?: string;
  description?: string;
  frameMaterial?: string;
  frameShape?: string;
  gender?: string;
  timestamp: number; // Thêm timestamp để quản lý cache
}

// Cache với thời gian sống 3 phút
const CACHE_EXPIRATION = 3 * 60 * 1000; // 3 phút
const productCache: Record<string, ProductCacheItem> = {};

// Kiểm tra xem item có bị hết hạn không
const isCacheExpired = (item: ProductCacheItem) => 
  Date.now() - item.timestamp > CACHE_EXPIRATION;

// Xóa các item cache đã hết hạn
const cleanExpiredCache = () => {
  Object.keys(productCache).forEach(key => {
    if (isCacheExpired(productCache[key])) {
      delete productCache[key];
    }
  });
};

// Interface cho Product Data
export interface ProductData {
  product_id: string;
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
  type?: string;
  variant?: string;
  search_type?: string;
  newPrice?: number;
}

export interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: {
    name: string;
    url: string;
    type: string;
  }[];
  products?: ProductData[];
  extracted_product_ids?: string[];
}

interface ChatResponse {
  response: string;
  agent_used?: string;
  session_id?: string;
  clarified_message?: string;
  analysis?: string;
  data?: ProductData[];
  user_info?: {
    user_id: string;
    name: string;
    phone: string;
  };
  orders?: {
    order_id: string;
    status: string;
    total: string;
  }[];
  extracted_product_ids?: string[];
  status: string;
  timestamp: string;
}

// URL cơ sở của Host Agent API - sử dụng proxy để bypass CORS
const API_BASE_URL = "/api";

export const useChatApi = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Khôi phục sessionId từ localStorage khi component mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('eyevi_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      // Tự động tạo session mới nếu chưa có
      createNewSession();
    }
  }, []);
  
  // Lưu sessionId vào localStorage khi thay đổi
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('eyevi_session_id', sessionId);
    }
  }, [sessionId]);
  
  const sendMessage = async (content: string, attachments?: File[]) => {
    setIsLoading(true);
    
    try {
      // Tạo FormData để gửi request
      const formData = new FormData();
      formData.append("message", content);
      formData.append("user_id", FIXED_USER_ID.toString());
      
      // Thêm session_id nếu có
      if (sessionId) {
        formData.append("session_id", sessionId);
      }
      
      // Thêm files nếu có
      if (attachments && attachments.length > 0) {
        attachments.forEach(file => {
          formData.append("files", file);
        });
      }
      console.log("formdata: ", formData)
      
      // Gửi request đến Host Agent
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        body: formData,
      });
      console.log("response: ", response)
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data: ChatResponse = await response.json();
      
      // Xóa cache nếu có dữ liệu sản phẩm từ API chat
      if (data.data && data.data.length > 0) {
        console.log("Clearing product cache due to new product data from chat API");
        clearProductCache();
      }
      
      // Lưu session_id nếu có
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      
      return data;
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  const getChatHistory = async () => {
    if (!sessionId) return [];
    
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history?user_id=${FIXED_USER_ID}`);
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error("Lỗi khi lấy lịch sử chat:", error);
      return [];
    }
  };
  
  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/create`, {
        method: "POST"
      });
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data = await response.json();
      setSessionId(data.session_id);
      return data.session_id;
    } catch (error) {
      console.error("Lỗi khi tạo phiên mới:", error);
      return null;
    }
  };
  
  const clearChatHistory = async () => {
    if (!sessionId) return false;
    
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history?user_id=${FIXED_USER_ID}`, {
        method: "DELETE"
      });
      
      return response.ok;
    } catch (error) {
      console.error("Lỗi khi xóa lịch sử chat:", error);
      return false;
    }
  };
  
  // Hàm lấy thông tin sản phẩm theo ID với cache
  const getProductById = useCallback(async (productId: string) => {
    // Xóa cache đã hết hạn
    cleanExpiredCache();
    
    // Kiểm tra cache trước
    const cachedProduct = productCache[productId];
    if (cachedProduct && !isCacheExpired(cachedProduct)) {
      console.log(`Using cached data for product ${productId}`);
      return cachedProduct;
    }
    
    try {
      console.log(`Calling API to get product with ID: ${productId}`);
      const response = await fetch(`${API_BASE_URL}/products/${productId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          console.warn(`Không tìm thấy sản phẩm với ID: ${productId}`);
          return null;
        }
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`API response for product ${productId}:`, data);
      
      // Lưu vào cache với timestamp
      productCache[productId] = {
        ...data,
        timestamp: Date.now()
      };
      
      return data;
    } catch (error) {
      console.error(`Lỗi khi lấy thông tin sản phẩm ${productId}:`, error);
      return null;
    }
  }, []);
  
  // Hàm lấy thông tin nhiều sản phẩm theo danh sách ID với cache
  const getProductsByIds = useCallback(async (productIds: string[]) => {
    if (!productIds.length) return [];
    
    // Xóa cache đã hết hạn
    cleanExpiredCache();
    
    // Lọc ra những ID chưa có trong cache hoặc đã hết hạn
    const uncachedIds = productIds.filter(id => 
      !productCache[id] || isCacheExpired(productCache[id])
    );
    
    // Nếu tất cả đã có trong cache và còn hiệu lực, trả về từ cache
    if (uncachedIds.length === 0) {
      console.log('Using cached data for all products');
      return productIds.map(id => productCache[id]);
    }
    
    try {
      const idsParam = uncachedIds.join(',');
      console.log(`Calling API to get products with IDs: ${idsParam}`);
      const response = await fetch(`${API_BASE_URL}/products?product_ids=${idsParam}`);
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const newData = await response.json() as ProductCacheItem[];
      console.log(`API response for products [${idsParam}]:`, newData);
      
      // Lưu các sản phẩm mới vào cache với timestamp
      if (newData && newData.length > 0) {
        newData.forEach((product: ProductCacheItem) => {
          if (product && product.id) {
            productCache[product.id] = {
              ...product,
              timestamp: Date.now()
            };
          }
        });
      }
      
      // Trả về tất cả sản phẩm (từ cache + mới fetch)
      return productIds.map(id => productCache[id] || null).filter(Boolean);
    } catch (error) {
      console.error("Lỗi khi lấy thông tin sản phẩm:", error);
      // Trả về những sản phẩm có trong cache
      return productIds.map(id => productCache[id] || null).filter(Boolean);
    }
  }, []);
  
  // Hàm để xóa cache sản phẩm
  const clearProductCache = useCallback(() => {
    Object.keys(productCache).forEach(key => delete productCache[key]);
    console.log("Đã xóa toàn bộ cache sản phẩm");
  }, []);
  
  return {
    sendMessage,
    getChatHistory,
    createNewSession,
    clearChatHistory,
    getProductById,
    getProductsByIds,
    clearProductCache,
    isLoading,
    sessionId
  };
}; 