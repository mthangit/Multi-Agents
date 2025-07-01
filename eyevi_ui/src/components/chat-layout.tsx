"use client";

import React from "react";
import Sidebar from "./sidebar";
import ChatContainer from "./chat-container";
import { useChatApi } from "@/hooks/useChatApi";

const ChatLayout = () => {
  const { createNewSession, clearChatHistory, sessionId } = useChatApi();

  const handleNewChat = async () => {
    await createNewSession();
    // ChatContainer sẽ tự động phát hiện sessionId mới và reset
  };

  const handleClearHistory = async () => {
    await clearChatHistory();
  };

  return (
    <div className="flex min-h-screen w-full">
      <Sidebar 
        sessionId={sessionId} 
        onNewChat={handleNewChat} 
        onClearHistory={handleClearHistory} 
      />
      <ChatContainer />
    </div>
  );
};

export default ChatLayout; 