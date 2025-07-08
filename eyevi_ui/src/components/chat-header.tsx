"use client";

import React, { useState, useEffect } from "react";
import { Share2, MoreVertical, SunMoon, Plus } from "lucide-react";
import { Button } from "./ui/button";
import { useChatApi } from "@/hooks/useChatApi";
import { useTheme } from "./theme-provider";
import { Popover } from "@/components/ui/popover";

interface ChatHeaderProps {
  onNewChat?: () => void;
  isViewingHistory?: boolean;
  onBackToCurrentChat?: () => void;
}

const ChatHeader = ({ onNewChat, isViewingHistory, onBackToCurrentChat }: ChatHeaderProps) => {
  const { sessionId } = useChatApi();
  const { theme, toggleTheme } = useTheme();
  const [title, setTitle] = useState("Trò chuyện mới");
  const [showMenu, setShowMenu] = useState(false);
  
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
  
  const iconButtonBase =
    "relative w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-300 border border-border bg-background/80 hover:bg-accent/60 hover:shadow-md hover:scale-105 active:scale-95 focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:z-10";

  return (
    <header className="flex items-center justify-between border-b border-border h-14 px-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-medium">{isViewingHistory ? "Xem lịch sử" : title}</h2>
        {isViewingHistory && (
          <Button
            variant="outline"
            size="sm"
            onClick={onBackToCurrentChat}
            className="text-xs"
          >
            Quay lại chat hiện tại
          </Button>
        )}
      </div>
      <div className="flex items-center gap-2">
        {onNewChat && (
          <Button
            variant="ghost"
            size="icon"
            aria-label="Trò chuyện mới"
            onClick={onNewChat}
            title="Tạo trò chuyện mới"
            className={iconButtonBase + " group"}
          >
            <Plus className="h-5 w-5 text-[#237be3] transition-transform duration-300 group-hover:rotate-90 group-active:scale-90" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          aria-label="Chuyển chế độ tối/sáng"
          title="Chuyển đổi giao diện"
          className={iconButtonBase + " group"}
          onClick={toggleTheme}
        >
          <SunMoon className="h-5 w-5 text-yellow-400 dark:text-blue-400 transition-transform duration-300 group-hover:rotate-180 group-active:scale-90" />
        </Button>
        <Popover open={showMenu} onOpenChange={setShowMenu}>
          <Popover.Trigger asChild>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Menu"
              title="Tùy chọn khác"
              className={iconButtonBase + " group"}
            >
              <MoreVertical className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:scale-110 group-active:scale-90" />
            </Button>
          </Popover.Trigger>
          <Popover.Content align="end" className="w-48 p-2 bg-popover rounded-lg shadow-lg border border-border mt-2">
            <button className="w-full text-left px-3 py-2 rounded hover:bg-accent/50 text-sm" onClick={() => { setShowMenu(false); alert('Chức năng sắp ra mắt!'); }}>Chức năng sắp ra mắt</button>
            <button className="w-full text-left px-3 py-2 rounded hover:bg-accent/50 text-sm" onClick={() => { setShowMenu(false); }}>Đóng</button>
          </Popover.Content>
        </Popover>
      </div>
    </header>
  );
};

export default ChatHeader; 