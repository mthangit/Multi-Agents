"use client";

import { useState, useEffect } from "react";
import ChatHeader from "@/components/chat-header";
import ChatMessages from "@/components/chat-messages";
import ChatInput from "@/components/chat-input";
import Sidebar from "@/components/sidebar";
import { useChatApi } from "@/hooks/useChatApi";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: {
    name: string;
    url: string;
    type: string;
  }[];
}

interface ChatHistoryMessage {
  id: string;
  content: string;
  role: string;
  timestamp: string;
  attachments?: Array<{
    name: string;
    url: string;
    type: string;
  }>;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo của bạn. Tôi có thể giúp gì cho bạn hôm nay?",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  
  const { 
    sendMessage, 
    getChatHistory, 
    createNewSession, 
    clearChatHistory,
    isLoading, 
    sessionId 
  } = useChatApi();
  
  // Lấy lịch sử chat khi có sessionId
  useEffect(() => {
    const fetchChatHistory = async () => {
      if (sessionId) {
        const history = await getChatHistory();
        if (history && history.length > 0) {
          // Chuyển đổi định dạng tin nhắn từ API sang định dạng UI
          const formattedMessages = history.map((msg: ChatHistoryMessage) => ({
            id: msg.id || String(Date.now()),
            content: msg.content || "",
            sender: msg.role === "user" ? "user" : "bot",
            timestamp: new Date(msg.timestamp),
            attachments: msg.attachments || []
          }));
          
          setMessages(formattedMessages);
        }
      }
    };
    
    fetchChatHistory();
  }, [sessionId, getChatHistory]);

  // Xử lý tạo cuộc trò chuyện mới
  const handleNewChat = async () => {
    await createNewSession();
    setMessages([{
      id: "1",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo của bạn. Tôi có thể giúp gì cho bạn hôm nay?",
      sender: "bot",
      timestamp: new Date(),
    }]);
  };
  
  // Xử lý xóa lịch sử chat
  const handleClearHistory = async () => {
    if (await clearChatHistory()) {
      setMessages([{
        id: "1",
        content: "Lịch sử chat đã được xóa. Tôi có thể giúp gì cho bạn?",
        sender: "bot",
        timestamp: new Date(),
      }]);
    }
  };

  const handleSendMessage = async (content: string, attachments?: File[]) => {
    // Tạo ID duy nhất cho tin nhắn
    const messageId = Date.now().toString();
    
    // Thêm tin nhắn của người dùng vào state
    const userMessage: Message = {
      id: messageId,
      content,
      sender: "user",
      timestamp: new Date(),
      attachments: attachments?.map(file => ({
        name: file.name,
        url: URL.createObjectURL(file),
        type: file.type,
      })),
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Gửi tin nhắn đến API
      const response = await sendMessage(content, attachments);
      
      // Thêm phản hồi từ chatbot vào state
      const botMessage: Message = {
        id: Date.now().toString(),
        content: response.response,
        sender: "bot",
        timestamp: new Date(response.timestamp),
        // Nếu có data bổ sung, có thể thêm vào đây
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      
      // Thêm thông báo lỗi vào state
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: "Xin lỗi, đã xảy ra lỗi khi gửi tin nhắn. Vui lòng thử lại sau.",
        sender: "bot",
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar 
        sessionId={sessionId} 
        onNewChat={handleNewChat}
        onClearHistory={handleClearHistory}
      />
      <div className="flex-1 flex flex-col">
        <ChatHeader />
        <ChatMessages messages={messages} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
} 