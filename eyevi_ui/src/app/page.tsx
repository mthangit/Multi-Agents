"use client";

import { useState } from "react";
import ChatHeader from "@/components/chat-header";
import ChatMessages from "@/components/chat-messages";
import ChatInput from "@/components/chat-input";
import Sidebar from "@/components/sidebar";

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

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Xin chào! Tôi là EyeVi, trợ lý ảo của bạn. Tôi có thể giúp gì cho bạn hôm nay?",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);

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
    console.log("content: ", content)
    try {
      // Chuẩn bị FormData cho API
      // const formData = new FormData();
      // formData.append("message", content);
      
      // // Thêm tệp đính kèm vào FormData nếu có
      // if (attachments && attachments.length > 0) {
      //   attachments.forEach(file => {
      //     formData.append("attachments", file);
      //   });
      // }
      
      // // Gửi yêu cầu đến API chatbot
      // const response = await fetch("http://localhost:8001/search/text", {
      //   method: "POST",
      //   body: formData,
      // });
      const response = await fetch("http://localhost:8001/search/text", {
        method: "POST",
        body: JSON.stringify({
          query: content
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error("Lỗi khi gửi tin nhắn");
      }
      
      const data = await response.json();
      
      // Thêm phản hồi từ chatbot vào state
      const botMessage: Message = {
        id: Date.now().toString(),
        content: data.response,
        sender: "bot",
        timestamp: new Date(),
        attachments: data.attachments,
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
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <ChatHeader />
        <ChatMessages messages={messages} />
        <ChatInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
} 