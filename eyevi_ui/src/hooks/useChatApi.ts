import { useState, useEffect } from 'react';

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: {
    name: string;
    url: string;
    type: string;
  }[];
}

interface ChatResponse {
  response: string;
  agent_used?: string;
  session_id?: string;
  clarified_message?: string;
  analysis?: string;
  data?: string;
  status: string;
  timestamp: string;
}

// URL cơ sở của Host Agent API
const API_BASE_URL = "http://localhost:8080";

export const useChatApi = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Khôi phục sessionId từ localStorage khi component mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('eyevi_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      // Tự động tạo session mới nếu chưa có
      createNewSession();
    }
  }, []);
  
  // Lưu sessionId vào localStorage khi thay đổi
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('eyevi_session_id', sessionId);
    }
  }, [sessionId]);
  
  const sendMessage = async (content: string, attachments?: File[]) => {
    setIsLoading(true);
    
    try {
      // Tạo FormData để gửi request
      const formData = new FormData();
      formData.append("message", content);
      
      // Thêm session_id nếu có
      if (sessionId) {
        formData.append("session_id", sessionId);
      }
      
      // Thêm files nếu có
      if (attachments && attachments.length > 0) {
        attachments.forEach(file => {
          formData.append("files", file);
        });
      }
      
      // Gửi request đến Host Agent
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data: ChatResponse = await response.json();
      
      // Lưu session_id nếu có
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      
      return data;
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  const getChatHistory = async () => {
    if (!sessionId) return [];
    
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history`);
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error("Lỗi khi lấy lịch sử chat:", error);
      return [];
    }
  };
  
  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/create`, {
        method: "POST"
      });
      
      if (!response.ok) {
        throw new Error(`Lỗi: ${response.status}`);
      }
      
      const data = await response.json();
      setSessionId(data.session_id);
      return data.session_id;
    } catch (error) {
      console.error("Lỗi khi tạo phiên mới:", error);
      return null;
    }
  };
  
  const clearChatHistory = async () => {
    if (!sessionId) return false;
    
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history`, {
        method: "DELETE"
      });
      
      return response.ok;
    } catch (error) {
      console.error("Lỗi khi xóa lịch sử chat:", error);
      return false;
    }
  };
  
  return {
    sendMessage,
    getChatHistory,
    createNewSession,
    clearChatHistory,
    isLoading,
    sessionId
  };
}; 