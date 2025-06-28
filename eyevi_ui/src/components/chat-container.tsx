"use client";

import React, { useState } from "react";
import ChatHeader from "./chat-header";
import ChatMessages from "./chat-messages";
import ChatInput from "./chat-input";

// Interface cho Message trong ChatContainer
interface ContainerMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// Interface cho Message trong ChatMessages (để tham chiếu)
interface ChatMessage {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: Array<{name: string; url: string; type: string}>;
}

const ChatContainer = () => {
  const [messages, setMessages] = useState<ContainerMessage[]>([
    {
      id: 1,
      role: "assistant",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo hỗ trợ bạn mua sắm kính mắt. Tôi có thể giúp gì cho bạn hôm nay?",
      timestamp: new Date().toISOString(),
    },
  ]);

  const handleSendMessage = (message: string, attachments?: File[]) => {
    // Thêm tin nhắn của người dùng vào danh sách
    const userMessage: ContainerMessage = {
      id: messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    
    // Ghi log attachments nếu có (có thể xử lý tải lên file ở đây trong tương lai)
    if (attachments && attachments.length > 0) {
      console.log('Đí nh kèm files:', attachments);
      // Xử lý tải lên file ở đây
    }
    
    // Giả lập phản hồi từ chatbot (sẽ thay thế bằng API call sau này)
    setTimeout(() => {
      const botReply: ContainerMessage = {
        id: messages.length + 2,
        role: "assistant",
        content: "Đây là phản hồi mẫu. Trong ứng dụng thực tế, phần này sẽ được thay thế bằng dữ liệu từ API.",
        timestamp: new Date().toISOString(),
      };
      
      setMessages((prev) => [...prev, botReply]);
    }, 1000);
  };

  // Chuyển đổi từ ContainerMessage sang định dạng mà ChatMessages mong đợi
  const transformMessages = (): ChatMessage[] => {
    return messages.map(msg => ({
      id: msg.id.toString(),
      content: msg.content,
      sender: msg.role === "user" ? "user" : "bot",
      timestamp: new Date(msg.timestamp),
      attachments: []
    }));
  };

  return (
    <div className="flex flex-col flex-1 h-screen overflow-hidden">
      <ChatHeader />
      <ChatMessages messages={transformMessages()} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatContainer; 