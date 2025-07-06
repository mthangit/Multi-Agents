"use client";

import React, { useState, useEffect } from "react";
import { Eye, Plus, Paperclip, Trash2, Loader2, Globe } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";
import { useChatApi, FIXED_USER_ID } from "@/hooks/useChatApi";
import ThemeToggle from "./theme-toggle";

interface SessionInfo {
  id: string;
  title?: string;
  created_at?: string;
  last_updated?: string;
  message_count?: number;
  last_message_preview?: string;
}

interface SidebarProps {
  sessionId?: string | null;
  onNewChat?: () => void;
  onClearHistory?: () => void;
}

const Sidebar = ({ sessionId, onNewChat, onClearHistory }: SidebarProps) => {
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
          setActiveSessions(data.sessions || []);
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
        className="relative flex items-center gap-3 mb-4 px-4 py-3 bg-gradient-to-r from-sidebar-primary to-sidebar-primary/90 text-sidebar-primary-foreground hover:from-sidebar-primary/90 hover:to-sidebar-primary/80 transition-all duration-300 active:scale-[0.98] hover:scale-[1.02] hover:shadow-lg rounded-xl border border-sidebar-primary/20 overflow-hidden"
        onClick={handleNewChat}
        disabled={isCreatingSession}
      >
        {/* Background gradient effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] hover:translate-x-[100%] transition-transform duration-700" />
        
        <div className="relative z-10 flex items-center gap-3">
          {isCreatingSession ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Plus className="w-4 h-4 transition-all duration-300 group-hover:rotate-90" />
          )}
          <span className="font-medium">
            {isCreatingSession ? "Đang tạo..." : "Tạo cuộc trò chuyện mới"}
          </span>
        </div>
      </Button>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4">
        <div className="text-sm font-medium mb-2 px-2">Gần đây</div>
        <div className="space-y-1">
          {activeSessions.length > 0 ? (
            activeSessions.map((session, index) => (
              <ChatHistoryItem 
                key={session.id || `session-${index}`}
                title={session.id || `Cuộc hội thoại ${session.id}`} 
                active={session.id === sessionId} 
                messageCount={session.message_count}
                preview={session.last_message_preview}
              />
            ))
          ) : (
            <div className="text-sm text-muted-foreground px-3 py-2">
              Chưa có cuộc trò chuyện nào
            </div>
          )}
          
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
        <FooterItem icon={<Globe size={16} />} text="Trang web" onClick={() => { /* TODO: tích hợp link sau */ }} />
        <FooterItem 
          icon={<Trash2 size={16} />} 
          text="Xóa lịch sử" 
          onClick={handleClearHistory}
        />
        <FooterItem icon={<Paperclip size={16} />} text="Đính kèm tệp" />
      </div>
    </div>
  );
};

// Chat history item component
interface ChatHistoryItemProps {
  title: string;
  active: boolean;
  messageCount?: number;
  preview?: string;
}

const ChatHistoryItem = ({ title, active, messageCount, preview }: ChatHistoryItemProps) => {
  return (
    <button
      className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? "bg-sidebar-primary text-sidebar-primary-foreground"
          : "hover:bg-sidebar-accent/50 text-sidebar-foreground"
      }`}
    >
      <div className="flex flex-col">
        <span>{title}</span>
        {preview && (
          <span className="text-xs text-muted-foreground truncate mt-1">
            {preview}
          </span>
        )}
        {messageCount && (
          <span className="text-xs text-muted-foreground mt-0.5">
            {messageCount} tin nhắn
          </span>
        )}
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