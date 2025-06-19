"use client";

import React from "react";
import { Share2, MoreVertical, SunMoon } from "lucide-react";
import { Button } from "./ui/button";

const ChatHeader = () => {
  return (
    <header className="flex items-center justify-between border-b border-border h-14 px-4">
      <div className="flex items-center">
        <h2 className="text-lg font-medium">Trò chuyện mới</h2>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Chia sẻ">
          <Share2 className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Chuyển chế độ tối/sáng">
          <SunMoon className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Menu">
          <MoreVertical className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
};

export default ChatHeader; 