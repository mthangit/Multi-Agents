"use client";

import React, { useState, useEffect } from "react";
import { Eye, Plus, Settings, HelpCircle, Paperclip, Sparkles, Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";

interface SessionInfo {
  id: string;
  title?: string;
  created_at?: string;
  last_updated?: string;
}

interface SidebarProps {
  sessionId?: string | null;
  onNewChat?: () => void;
  onClearHistory?: () => void;
}

const Sidebar = ({ sessionId, onNewChat, onClearHistory }: SidebarProps) => {
  const [activeSessions, setActiveSessions] = useState<SessionInfo[]>([]);
  
  // Lấy danh sách các phiên hoạt động
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch("http://localhost:8080/sessions");
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

  return (
    <div className="flex flex-col w-72 h-screen bg-sidebar border-r border-sidebar-border p-3 text-sidebar-foreground">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 px-2">
        <div className="flex items-center gap-2">
          <Eye className="w-6 h-6 text-sidebar-primary" />
          <h1 className="text-xl font-semibold">EyeVi</h1>
        </div>
      </div>

      {/* New Chat Button */}
      <Button 
        className="flex items-center gap-2 mb-4 bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/90"
        onClick={onNewChat}
      >
        <Plus className="w-4 h-4" />
        <span>Tạo cuộc trò chuyện mới</span>
      </Button>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4">
        <div className="text-sm font-medium mb-2 px-2">Gần đây</div>
        <div className="space-y-1">
          {activeSessions.length > 0 ? (
            activeSessions.map(session => (
              <ChatHistoryItem 
                key={session.id}
                title={session.title || `Cuộc hội thoại ${session.id.slice(0, 8)}`} 
                active={session.id === sessionId} 
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
              title={`Cuộc hội thoại hiện tại`}
              active={true}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto border-t border-sidebar-border pt-4 space-y-2">
        <FooterItem 
          icon={<Trash2 size={16} />} 
          text="Xóa lịch sử" 
          onClick={onClearHistory}
        />
        <FooterItem icon={<Paperclip size={16} />} text="Đính kèm tệp" />
        <FooterItem icon={<Sparkles size={16} />} text="Nâng cấp tài khoản" />
        <FooterItem icon={<HelpCircle size={16} />} text="Trợ giúp & Hỗ trợ" />
        <FooterItem icon={<Settings size={16} />} text="Cài đặt" />
      </div>
    </div>
  );
};

// Chat history item component
const ChatHistoryItem = ({ title, active }: { title: string; active: boolean }) => {
  return (
    <button
      className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? "bg-sidebar-primary text-sidebar-primary-foreground"
          : "hover:bg-sidebar-accent/50 text-sidebar-foreground"
      }`}
    >
      {title}
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