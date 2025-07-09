"use client";

import React, { useState, useEffect, useRef, createContext, useContext, useImperativeHandle, forwardRef } from "react";
import ChatHeader from "./chat-header";
import ChatMessages from "./chat-messages";
import ChatInput, { ChatInputRef } from "./chat-input";
import { useChatApi, ProductData, OrderData } from "@/hooks/useChatApi";

// Tạo context để truy cập chatInputRef từ các component khác
interface ChatContextType {
  setChatInputMessage: (text: string) => void;
  loadHistoryBySessionId: (sessionId: string) => void;
}

export const ChatContext = createContext<ChatContextType | null>(null);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within a ChatContextProvider");
  }
  return context;
};

// Interface cho ChatContainer ref
export interface ChatContainerRef {
  loadHistoryBySessionId: (sessionId: string) => void;
  resetChat: () => void;
}

// Interface cho Message trong ChatContainer
interface ContainerMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  attachments?: Array<{name: string; url: string; type: string}>;
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

const ChatContainer = forwardRef<ChatContainerRef>((_, ref) => {
  const { sendMessage, createNewSession, getChatHistoryBySessionId, isLoading, sessionId } = useChatApi();
  const [messages, setMessages] = useState<ContainerMessage[]>([]);
  const [products, setProducts] = useState<ProductData[]>([]);
  const [productIds, setProductIds] = useState<string[]>([]);
  const [loadingMessageId, setLoadingMessageId] = useState<number | null>(null);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const [isViewingHistory, setIsViewingHistory] = useState(false);
  const [viewingSessionId, setViewingSessionId] = useState<string | null>(null);
  const [resetTrigger, setResetTrigger] = useState(0);

  // Lưu tạm chat hiện tại khi xem lịch sử
  const [tempCurrentMessages, setTempCurrentMessages] = useState<ContainerMessage[]>([]);
  const [tempCurrentProducts, setTempCurrentProducts] = useState<ProductData[]>([]);
  const [tempCurrentProductIds, setTempCurrentProductIds] = useState<string[]>([]);

  const chatInputRef = useRef<ChatInputRef>(null);
  const previousSessionIdRef = useRef<string | null>(null);

  // Reset messages khi sessionId thay đổi (tạo session mới)
  useEffect(() => {
    console.log("SessionId effect triggered:", {
      sessionId,
      previousSessionId: previousSessionIdRef.current,
      isViewingHistory,
      messagesLength: messages.length
    });

    if (sessionId && sessionId !== previousSessionIdRef.current && !isViewingHistory) {
      console.log("🔄 Resetting chat container - Session changed from", previousSessionIdRef.current, "to", sessionId);

      // Reset tất cả state khi có session mới
      setMessages([]);
      setProducts([]);
      setProductIds([]);
      setLoadingMessageId(null);

      // Cập nhật ref để theo dõi session hiện tại
      previousSessionIdRef.current = sessionId;
    }
  }, [sessionId, isViewingHistory]);

  // Cleanup object URLs khi component unmount (không cleanup khi messages thay đổi)
  useEffect(() => {
    return () => {
      messages.forEach(msg => {
        if (msg.attachments) {
          msg.attachments.forEach(attachment => {
            if (attachment.url.startsWith('blob:')) {
              URL.revokeObjectURL(attachment.url);
            }
          });
        }
      });
    };
  }, []); // Chỉ cleanup khi component unmount

  // Khởi tạo tin nhắn chào mừng khi có sessionId và messages rỗng
  useEffect(() => {
    console.log("Welcome message effect triggered:", {
      sessionId,
      isViewingHistory,
      messagesLength: messages.length,
      resetTrigger
    });

    if (sessionId && !isViewingHistory && messages.length === 0) {
      console.log("✅ Adding welcome message");
      setMessages([
        {
          id: 1,
          role: "assistant",
          content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }, [sessionId, isViewingHistory, messages.length, resetTrigger]);

  // Function để reset chat
  const resetChat = () => {
    console.log("🔄 Manual reset chat triggered");
    setMessages([]);
    setProducts([]);
    setProductIds([]);
    setLoadingMessageId(null);
    setIsViewingHistory(false);
    setViewingSessionId(null);

    // Clear temp data
    setTempCurrentMessages([]);
    setTempCurrentProducts([]);
    setTempCurrentProductIds([]);

    setResetTrigger(prev => prev + 1);
  };

  // Function để load lịch sử từ session_id cụ thể
  const loadHistoryBySessionId = async (targetSessionId: string) => {
    try {
      console.log("📚 Loading history for session:", targetSessionId);

      // Lưu tạm chat hiện tại trước khi xem lịch sử
      console.log("💾 Saving current chat temporarily");
      setTempCurrentMessages([...messages]);
      setTempCurrentProducts([...products]);
      setTempCurrentProductIds([...productIds]);

      setIsViewingHistory(true);
      setViewingSessionId(targetSessionId);

      const historyMessages = await getChatHistoryBySessionId(targetSessionId);

      // Chuyển đổi format từ API thành ContainerMessage
      const formattedMessages: ContainerMessage[] = historyMessages.map((msg: any, index: number) => ({
        id: index + 1,
        role: msg.sender_type === "user" ? "user" : "assistant",
        content: msg.message_content,
        timestamp: msg.created_at,
        products: msg.metadata?.products,
        extracted_product_ids: msg.metadata?.extracted_product_ids,
        orders: msg.metadata?.orders,
        agent_used: msg.metadata?.agent_used,
        is_loading: false,
      }));

      setMessages(formattedMessages);
      setProducts([]);
      setProductIds([]);
      setLoadingMessageId(null);

      console.log("✅ History loaded, current chat saved temporarily");
    } catch (error) {
      console.error("Lỗi khi load lịch sử:", error);
    }
  };

  // Expose methods to parent components via ref
  useImperativeHandle(ref, () => ({
    loadHistoryBySessionId,
    resetChat
  }));

  // Tạo context value
  const chatContextValue = {
    setChatInputMessage: (text: string) => {
      chatInputRef.current?.setInputMessage(text);
      chatInputRef.current?.focusInput();
    },
    loadHistoryBySessionId
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
    // Tạo attachment URLs cho preview
    const attachmentData = attachments?.map(file => ({
      name: file.name,
      url: URL.createObjectURL(file),
      type: file.type
    })) || [];

    // Thêm tin nhắn của người dùng vào danh sách
    const userMessage: ContainerMessage = {
      id: messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
      attachments: attachmentData,
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

      // Logic ưu tiên:
      // 1. Nếu có orders → chỉ hiển thị orders
      // 2. Nếu có data (products) → hiển thị data, không hiển thị extracted_product_ids
      // 3. Nếu chỉ có extracted_product_ids → hiển thị extracted_product_ids
      const hasOrders = response.orders && response.orders.length > 0;
      const hasProducts = response.data && response.data.length > 0;
      const hasExtractedIds = response.extracted_product_ids && response.extracted_product_ids.length > 0;

      // Xóa tin nhắn loading và thêm tin nhắn phản hồi từ API
      const botReply: ContainerMessage = {
        id: loadingMessageId,
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        products: !hasOrders && hasProducts ? response.data : undefined,
        extracted_product_ids: !hasOrders && !hasProducts && hasExtractedIds ? response.extracted_product_ids : undefined,
        orders: hasOrders ? response.orders : undefined,
        agent_used: response.agent_used,
        is_loading: false,
      };

      setMessages((prev) =>
        prev.map((msg) => (msg.id === loadingMessageId ? botReply : msg))
      );
      setLoadingMessageId(null);

      // Logic ưu tiên state update:
      // 1. Nếu có orders → clear products
      // 2. Nếu có data (products) → set products, clear product IDs
      // 3. Nếu chỉ có extracted_product_ids → set product IDs, clear products
      if (hasOrders) {
        setProducts([]); // Clear products khi có orders
        setProductIds([]); // Clear product IDs khi có orders
      } else if (hasProducts) {
        setProducts(response.data!); // Set products khi có data
        setProductIds([]); // Clear product IDs khi có products
      } else if (hasExtractedIds) {
        setProducts([]); // Clear products khi chỉ có extracted IDs
        setProductIds(response.extracted_product_ids!); // Set product IDs
      } else {
        setProducts([]); // Clear tất cả nếu không có gì
        setProductIds([]);
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
        attachments: msg.attachments || [],
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
    try {
      // Reset state trước khi tạo session mới
      setIsViewingHistory(false);
      setViewingSessionId(null);

      // Tạo session mới và đợi kết quả
      const newSessionId = await createNewSession();
      console.log("Created new session:", newSessionId);

      if (newSessionId) {
        // Messages sẽ được reset tự động bởi useEffect khi sessionId thay đổi
        // Tin nhắn chào mừng sẽ được thêm tự động sau đó
        console.log("New chat initialized with session:", newSessionId);
      } else {
        console.error("Failed to create new session");
        // Nếu tạo session thất bại, vẫn hiển thị tin nhắn chào mừng
        setMessages([
          {
            id: 1,
            role: "assistant",
            content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };

  // Xử lý quay lại chat hiện tại
  const handleBackToCurrentChat = async () => {
    console.log("🔙 Returning to current chat");

    setIsViewingHistory(false);
    setViewingSessionId(null);
    setLoadingMessageId(null);

    // Restore chat đã lưu tạm
    console.log("📤 Restoring temporarily saved chat");
    setMessages([...tempCurrentMessages]);
    setProducts([...tempCurrentProducts]);
    setProductIds([...tempCurrentProductIds]);

    // Clear temp data
    setTempCurrentMessages([]);
    setTempCurrentProducts([]);
    setTempCurrentProductIds([]);

    console.log("✅ Current chat restored");
  };

  return (
    <ChatContext.Provider value={chatContextValue}>
      <div className="flex flex-col flex-1 h-screen overflow-hidden">
        <ChatHeader
          onNewChat={handleNewChat}
          isViewingHistory={isViewingHistory}
          onBackToCurrentChat={handleBackToCurrentChat}
        />
        <div className="flex-1 overflow-hidden flex flex-col">
          <ChatMessages messages={transformMessages()} />
        </div>
        <ChatInput
          ref={chatInputRef}
          onSendMessage={handleSendMessage}
          isLoading={isLoading || loadingMessageId !== null}
          disabled={isViewingHistory}
        />
      </div>
    </ChatContext.Provider>
  );
});

ChatContainer.displayName = "ChatContainer";

export default ChatContainer;