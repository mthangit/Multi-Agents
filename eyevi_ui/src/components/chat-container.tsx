"use client";

import React, { useState, useEffect, useRef, createContext, useContext } from "react";
import ChatHeader from "./chat-header";
import ChatMessages from "./chat-messages";
import ChatInput, { ChatInputRef } from "./chat-input";
import ProductList from "./product-list";
import { useChatApi, ProductData, OrderData } from "@/hooks/useChatApi";

// Tạo context để truy cập chatInputRef từ các component khác
interface ChatContextType {
  setChatInputMessage: (text: string) => void;
}

export const ChatContext = createContext<ChatContextType | null>(null);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within a ChatContextProvider");
  }
  return context;
};

// Interface cho Message trong ChatContainer
interface ContainerMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  products?: ProductData[];
  extracted_product_ids?: string[];
  orders?: OrderData[];
  agent_used?: string;
  is_loading?: boolean;
  loading_step?: string;
}

// Interface cho Message trong ChatMessages (để tham chiếu)
interface ChatMessage {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: Array<{name: string; url: string; type: string}>;
  products?: ProductData[];
  extracted_product_ids?: string[];
  orders?: OrderData[];
  agent_used?: string;
  is_loading?: boolean;
  loading_step?: string;
}

// Các bước loading và thông báo tương ứng
const LOADING_STEPS = [
  "Đang phân tích yêu cầu...",
  "Đang tìm kiếm thông tin liên quan...",
  "Đang giao nhiệm vụ cho agent chuyên môn...",
  "Đang xử lý dữ liệu...",
  "Đang tổng hợp thông tin...",
  "Đang chuẩn bị phản hồi...",
];

const ChatContainer = () => {
  const { sendMessage, createNewSession, isLoading, sessionId } = useChatApi();
  const [messages, setMessages] = useState<ContainerMessage[]>([
    {
      id: 1,
      role: "assistant",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [products, setProducts] = useState<ProductData[]>([]);
  const [productIds, setProductIds] = useState<string[]>([]);
  const [loadingMessageId, setLoadingMessageId] = useState<number | null>(null);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const chatInputRef = useRef<ChatInputRef>(null);

  // Tạo context value
  const chatContextValue = {
    setChatInputMessage: (text: string) => {
      chatInputRef.current?.setInputMessage(text);
      chatInputRef.current?.focusInput();
    }
  };

  // Tạo session mới khi component mount nếu chưa có
  useEffect(() => {
    if (!sessionId) {
      createNewSession();
    }
  }, [sessionId, createNewSession]);
  
  // Hiệu ứng thay đổi thông báo loading
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    
    if (loadingMessageId !== null) {
      intervalId = setInterval(() => {
        setLoadingStepIndex((prev) => (prev + 1) % LOADING_STEPS.length);
        
        setMessages((prevMessages) => 
          prevMessages.map((msg) => 
            msg.id === loadingMessageId 
              ? { ...msg, loading_step: LOADING_STEPS[loadingStepIndex] }
              : msg
          )
        );
      }, 1400); // Thay đổi thông báo mỗi 2 giây
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [loadingMessageId, loadingStepIndex]);

  const handleSendMessage = async (message: string, attachments?: File[]) => {
    // Thêm tin nhắn của người dùng vào danh sách
    const userMessage: ContainerMessage = {
      id: messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    
    // Thêm tin nhắn loading
    const loadingMessageId = messages.length + 2;
    const loadingMessage: ContainerMessage = {
      id: loadingMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      is_loading: true,
      loading_step: LOADING_STEPS[0],
    };
    
    setMessages((prev) => [...prev, loadingMessage]);
    setLoadingMessageId(loadingMessageId);
    setLoadingStepIndex(0);
    
    try {
      // Gửi tin nhắn đến API
      const response = await sendMessage(message, attachments);
      console.log("API Response:", response);
      
      // Xóa tin nhắn loading và thêm tin nhắn phản hồi từ API
      const botReply: ContainerMessage = {
        id: loadingMessageId,
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        products: response.data,
        extracted_product_ids: response.extracted_product_ids,
        orders: response.orders,
        agent_used: response.agent_used,
        is_loading: false,
      };
      
      setMessages((prev) => 
        prev.map((msg) => (msg.id === loadingMessageId ? botReply : msg))
      );
      setLoadingMessageId(null);
      
      // Cập nhật danh sách sản phẩm nếu có
      if (response.data && response.data.length > 0) {
        setProducts(response.data);
      }
      
      // Cập nhật danh sách ID sản phẩm nếu có
      if (response.extracted_product_ids && response.extracted_product_ids.length > 0) {
        setProductIds(response.extracted_product_ids);
      }
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      
      // Xóa tin nhắn loading và thêm tin nhắn lỗi
      const errorMessage: ContainerMessage = {
        id: loadingMessageId,
        role: "assistant",
        content: "Xin lỗi, đã xảy ra lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại sau.",
        timestamp: new Date().toISOString(),
        is_loading: false,
      };
      
      setMessages((prev) => 
        prev.map((msg) => (msg.id === loadingMessageId ? errorMessage : msg))
      );
      setLoadingMessageId(null);
    }
  };

  // Chuyển đổi từ ContainerMessage sang định dạng mà ChatMessages mong đợi
  const transformMessages = (): ChatMessage[] => {
    return messages.map(msg => {
      // Log để debug
      console.log("Transforming message:", msg);
      if (msg.extracted_product_ids) {
        console.log("Found extracted_product_ids:", msg.extracted_product_ids);
      }
      
      return {
        id: msg.id.toString(),
        content: msg.content,
        sender: msg.role === "user" ? "user" : "bot",
        timestamp: new Date(msg.timestamp),
        attachments: [],
        products: msg.products,
        extracted_product_ids: msg.extracted_product_ids,
        orders: msg.orders,
        agent_used: msg.agent_used,
        is_loading: msg.is_loading,
        loading_step: msg.loading_step,
      };
    });
  };

  // Xử lý tạo cuộc trò chuyện mới
  const handleNewChat = async () => {
    const newSessionId = await createNewSession();
    if (newSessionId) {
      setMessages([
        {
          id: 1,
          role: "assistant",
          content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
          timestamp: new Date().toISOString(),
        },
      ]);
      setProducts([]);
      setProductIds([]);
      setLoadingMessageId(null);
    }
  };

  return (
    <ChatContext.Provider value={chatContextValue}>
      <div className="flex flex-col flex-1 h-screen overflow-hidden">
        <ChatHeader onNewChat={handleNewChat} />
        <div className="flex-1 overflow-hidden flex flex-col">
          <ChatMessages messages={transformMessages()} />
        </div>
        <ChatInput ref={chatInputRef} onSendMessage={handleSendMessage} isLoading={isLoading || loadingMessageId !== null} />
      </div>
    </ChatContext.Provider>
  );
};

export default ChatContainer; 