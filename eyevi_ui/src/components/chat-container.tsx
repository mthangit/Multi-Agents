"use client";

import React, { useState } from "react";
import ChatHeader from "./chat-header";
import ChatMessages from "./chat-messages";
import ChatInput from "./chat-input";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
      timestamp: new Date().toISOString(),
    },
  ]);

  const handleSendMessage = (message: string) => {
    // Thêm tin nhắn của người dùng vào danh sách
    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    
    // Giả lập phản hồi từ chatbot (sẽ thay thế bằng API call sau này)
    setTimeout(() => {
      const botReply: Message = {
        id: messages.length + 2,
        role: "assistant",
        content: "Đây là phản hồi mẫu. Trong ứng dụng thực tế, phần này sẽ được thay thế bằng dữ liệu từ API.",
        timestamp: new Date().toISOString(),
      };
      
      setMessages((prev) => [...prev, botReply]);
    }, 1000);
  };

  return (
    <div className="flex flex-col flex-1 h-screen overflow-hidden">
      <ChatHeader />
      <ChatMessages messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatContainer; 