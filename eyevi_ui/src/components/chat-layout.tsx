"use client";

import React, { useRef, useState, useEffect } from "react";
import Sidebar from "./sidebar";
import ChatContainer, { ChatContainerRef } from "./chat-container";
import WelcomeBanner from "./welcome-banner";
import { useChatApi } from "@/hooks/useChatApi";

const ChatLayout = () => {
  const { createNewSession, clearChatHistory, sessionId } = useChatApi();
  const chatContainerRef = useRef<ChatContainerRef>(null);
  const [showWelcomeBanner, setShowWelcomeBanner] = useState(true);

  // Banner luôn hiển thị khi mở app, chỉ ẩn khi user nhấn "Chat ngay" hoặc "Tạo cuộc trò chuyện mới"
  useEffect(() => {
    console.log("🎉 App loaded, showing welcome banner by default");
    setShowWelcomeBanner(true);
  }, []);

  const handleNewChat = async () => {
    console.log("🆕 Creating new chat from sidebar");

    // Ẩn banner nếu đang hiển thị
    setShowWelcomeBanner(false);

    // Reset ChatContainer trước khi tạo session mới
    chatContainerRef.current?.resetChat();

    // Tạo session mới
    const newSessionId = await createNewSession();
    console.log("✅ New chat created with session:", newSessionId);
  };

  const handleClearHistory = async () => {
    await clearChatHistory();
  };

  const handleLoadHistory = (sessionId: string) => {
    chatContainerRef.current?.loadHistoryBySessionId(sessionId);
  };

  const handleStartChat = async () => {
    console.log("🚀 Starting new chat from welcome banner");

    // Reset ChatContainer trước
    chatContainerRef.current?.resetChat();

    // Tạo session mới
    const newSessionId = await createNewSession();

    if (newSessionId) {
      // Chỉ ẩn banner khi tạo session thành công
      setShowWelcomeBanner(false);
      console.log("✅ Welcome banner hidden, new session created:", newSessionId);
    } else {
      console.error("❌ Failed to create session, keeping banner visible");
    }
  };

  return (
    <div className="flex min-h-screen w-full relative">
      <Sidebar
        sessionId={sessionId}
        onNewChat={handleNewChat}
        onClearHistory={handleClearHistory}
        onLoadHistory={handleLoadHistory}
      />
      <ChatContainer ref={chatContainerRef} />

      {/* Welcome Banner Overlay */}
      {showWelcomeBanner && (
        <WelcomeBanner onStartChat={handleStartChat} />
      )}
    </div>
  );
};

export default ChatLayout; 