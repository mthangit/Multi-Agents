"use client";

import React, { useState, useEffect } from "react";
import { Share2, MoreVertical, SunMoon, Plus } from "lucide-react";
import { Button } from "./ui/button";
import { useChatApi } from "@/hooks/useChatApi";

interface ChatHeaderProps {
  onNewChat?: () => void;
}

const ChatHeader = ({ onNewChat }: ChatHeaderProps) => {
  const { sessionId } = useChatApi();
  const [title, setTitle] = useState("Trò chuyện mới");
  
  // Cập nhật tiêu đề khi sessionId thay đổi
  useEffect(() => {
    if (sessionId) {
      // Tạo tiêu đề dựa trên sessionId
      // Ví dụ: Trò chuyện #abc123
      const shortId = sessionId.substring(0, 6);
      setTitle(`Trò chuyện #${shortId}`);
    } else {
      setTitle("Trò chuyện mới");
    }
  }, [sessionId]);
  
  return (
    <header className="flex items-center justify-between border-b border-border h-14 px-4">
      <div className="flex items-center">
        <h2 className="text-lg font-medium">{title}</h2>
      </div>
      <div className="flex items-center gap-2">
        {onNewChat && (
          <Button 
            variant="ghost" 
            size="icon" 
            aria-label="Trò chuyện mới" 
            onClick={onNewChat}
            title="Tạo trò chuyện mới"
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
        <Button variant="ghost" size="icon" aria-label="Chia sẻ" title="Chia sẻ cuộc trò chuyện">
          <Share2 className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Chuyển chế độ tối/sáng" title="Chuyển đổi giao diện">
          <SunMoon className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Menu" title="Tùy chọn khác">
          <MoreVertical className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
};

export default ChatHeader; 