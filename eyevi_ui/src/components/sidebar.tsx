"use client";

import React, { useState, useEffect } from "react";
import { Eye, Plus, Paperclip, Trash2, Loader2, Globe } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";
import { useChatApi, FIXED_USER_ID } from "@/hooks/useChatApi";
import ThemeToggle from "./theme-toggle";
import { cn } from "@/lib/utils";

interface SessionInfo {
  session_id: string;
  created_at: string;
  last_updated: string;
  message_count: number;
  last_message_preview: string;
}

interface SidebarProps {
  sessionId?: string | null;
  onNewChat?: () => void;
  onClearHistory?: () => void;
  onLoadHistory?: (sessionId: string) => void;
}

const Sidebar = ({ sessionId, onNewChat, onClearHistory, onLoadHistory }: SidebarProps) => {
  const [activeSessions, setActiveSessions] = useState<SessionInfo[]>([]);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const { clearChatHistory } = useChatApi();
  
  // Lấy danh sách các phiên hoạt động
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch(`/api/users/${FIXED_USER_ID}/sessions`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === "success") {
            setActiveSessions(data.sessions || []);
          }
        }
      } catch (error) {
        console.error("Lỗi khi lấy danh sách phiên:", error);
      }
    };
    
    fetchSessions();
  }, [sessionId]);

  const handleClearHistory = async () => {
    if (onClearHistory) {
      onClearHistory();
    } else {
      const success = await clearChatHistory();
      if (success && onNewChat) {
        onNewChat();
      }
    }
  };

  const handleNewChat = async () => {
    setIsCreatingSession(true);
    try {
      if (onNewChat) {
        await onNewChat();
      }
    } finally {
      // Add a small delay for smooth UX
      setTimeout(() => {
        setIsCreatingSession(false);
      }, 300);
    }
  };

  return (
    <div className="flex flex-col w-72 h-screen bg-sidebar border-r border-sidebar-border p-3 text-sidebar-foreground">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 px-2">
        <div className="flex items-center gap-2">
          <Eye className="w-6 h-6 text-sidebar-primary" />
          <h1 className="text-xl font-semibold">EyeVi</h1>
        </div>
        <ThemeToggle />
      </div>

      {/* New Chat Button */}
      <Button
        className="flex items-center gap-3 mb-4 px-4 py-3 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors duration-200 rounded-lg border"
        onClick={handleNewChat}
        disabled={isCreatingSession}
      >
        {isCreatingSession ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Plus className="w-4 h-4" />
        )}
        <span className="font-medium">
          {isCreatingSession ? "Đang tạo..." : "Tạo cuộc trò chuyện mới"}
        </span>
      </Button>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4">
        <div className="text-sm font-medium mb-2 px-2">Gần đây</div>
        <div className="space-y-1">
          {(() => {
            // Lọc ra các session có message_count > 0
            const validSessions = activeSessions.filter((session) => session.message_count > 0);

            return validSessions.length > 0 ? (
              // Sắp xếp theo thời gian cập nhật mới nhất lên đầu
              validSessions
                .sort((a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime())
                .map((session) => (
                  <ChatHistoryItem
                    key={session.session_id}
                    title={session.last_message_preview || `New Chat`}
                    active={session.session_id === sessionId}
                    timestamp={session.last_updated}
                    onClick={() => onLoadHistory?.(session.session_id)}
                  />
                ))
            ) : (
              <div className="text-sm text-muted-foreground px-3 py-2">
                Chưa có cuộc trò chuyện nào
              </div>
            );
          })()}
          
          {/* Fallback nếu không có session từ API */}
          {activeSessions.length === 0 && sessionId && (
            <ChatHistoryItem 
              key="current-session"
              title={`Cuộc hội thoại hiện tại`}
              active={true}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto border-t border-sidebar-border pt-4 space-y-2">
        <FooterItem
          icon={<Globe size={16} />}
          text="Trang web"
          onClick={() => {
            const shopUrl = process.env.NEXT_PUBLIC_SHOP_DOMAIN;
            if (shopUrl) {
              window.open(shopUrl, '_blank');
            }
          }}
        />
        {/* <FooterItem 
          icon={<Trash2 size={16} />} 
          text="Xóa lịch sử" 
          onClick={handleClearHistory}
        /> */}
      </div>
    </div>
  );
};

// Chat history item component
interface ChatHistoryItemProps {
  title: string;
  active?: boolean;
  preview?: string;
  timestamp?: string;
  onClick?: () => void;
}

const ChatHistoryItem = ({ title, active, timestamp, onClick }: ChatHistoryItemProps) => {
  // Format thời gian hiển thị
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "";

    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      // Nếu trong vòng 24h, hiển thị giờ:phút
      return date.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (diffInHours < 24 * 7) {
      // Nếu trong vòng 1 tuần, hiển thị thứ
      return date.toLocaleDateString('vi-VN', {
        weekday: 'short'
      });
    } else {
      // Nếu lâu hơn, hiển thị ngày/tháng
      return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit'
      });
    }
  };

  return (
    <button
      className={cn(
        "w-full text-left px-3 py-2 rounded-lg transition-colors duration-200",
        "hover:bg-accent/50",
        active ? "bg-accent" : "bg-transparent"
      )}
      onClick={onClick}
    >
      <div className="flex flex-col">
        <div className="flex items-center justify-between">
          <span className="font-medium truncate text-sm">{title}</span>
          {timestamp && (
            <span className="text-xs text-muted-foreground ml-2 flex-shrink-0">
              {formatTimestamp(timestamp)}
            </span>
          )}
        </div>
      </div>
    </button>
  );
};

// Footer item component
const FooterItem = ({ 
  icon, 
  text, 
  onClick 
}: { 
  icon: React.ReactNode; 
  text: string; 
  onClick?: () => void 
}) => {
  if (onClick) {
    return (
      <button 
        onClick={onClick}
        className="flex w-full items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-sidebar-accent/50"
      >
        {icon}
        <span>{text}</span>
      </button>
    );
  }
  
  return (
    <Link href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-sidebar-accent/50">
      {icon}
      <span>{text}</span>
    </Link>
  );
};

export default Sidebar; 