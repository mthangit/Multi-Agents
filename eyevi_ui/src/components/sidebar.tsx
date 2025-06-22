"use client";

import React from "react";
import { Eye, Plus, Settings, HelpCircle, Paperclip, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import Link from "next/link";

const Sidebar = () => {
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
        onClick={() => {/* handle new chat */}}
      >
        <Plus className="w-4 h-4" />
        <span>Tạo cuộc trò chuyện mới</span>
      </Button>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4">
        <div className="text-sm font-medium mb-2 px-2">Gần đây</div>
        <div className="space-y-1">
          {/* Các cuộc trò chuyện trước đây */}
          <ChatHistoryItem title="Tư vấn kính râm" active={true} />
          <ChatHistoryItem title="Chọn kính cận theo khuôn mặt" active={false} />
          <ChatHistoryItem title="So sánh các loại tròng kính" active={false} />
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto border-t border-sidebar-border pt-4 space-y-2">
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
const FooterItem = ({ icon, text }: { icon: React.ReactNode; text: string }) => {
  return (
    <Link href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-sidebar-accent/50">
      {icon}
      <span>{text}</span>
    </Link>
  );
};

export default Sidebar; 