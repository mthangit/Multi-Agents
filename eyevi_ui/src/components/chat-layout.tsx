"use client";

import React from "react";
import Sidebar from "./sidebar";
import ChatContainer from "./chat-container";

const ChatLayout = () => {
  return (
    <div className="flex min-h-screen w-full">
      <Sidebar />
      <ChatContainer />
    </div>
  );
};

export default ChatLayout; 