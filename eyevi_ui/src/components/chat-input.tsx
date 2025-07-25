"use client";

import React, { useState, useRef, useImperativeHandle, forwardRef, useEffect } from "react";
import { Send, Paperclip, ImageIcon } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";

interface ChatInputProps {
  onSendMessage: (message: string, attachments?: File[]) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

// Tạo ref type để export
export interface ChatInputRef {
  setInputMessage: (text: string) => void;
  focusInput: () => void;
}

const ChatInput = forwardRef<ChatInputRef, ChatInputProps>(({ onSendMessage, isLoading = false, disabled = false }, ref) => {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  // Expose methods to parent components via ref
  useImperativeHandle(ref, () => ({
    setInputMessage: (text: string) => {
      setMessage(text);
      // Auto-resize textarea after setting text
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
          textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
      }, 0);
    },
    focusInput: () => {
      textareaRef.current?.focus();
    }
  }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((message.trim() || attachments.length > 0) && !isLoading && !disabled) {
      onSendMessage(message, attachments);
      setMessage("");
      setAttachments([]);

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading && !disabled) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleAttachFile = () => {
    if (!isLoading && !disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleUploadImage = () => {
    if (!isLoading && !disabled) {
      imageInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAttachments(prev => [...prev, ...newFiles]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // Cleanup object URLs khi component unmount
  useEffect(() => {
    return () => {
      // Chỉ cleanup khi component unmount, không cleanup khi attachments thay đổi
      // vì object URLs cần được giữ để hiển thị trong chat
    };
  }, []);

  return (
    <div className="border-t border-border p-4">
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Button
            type="button"
            size="icon"
            variant="outline"
            aria-label="Đính kèm tệp"
            onClick={handleAttachFile}
            disabled={isLoading || disabled}
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
            multiple
            disabled={isLoading || disabled}
          />
          
          <Button
            type="button"
            size="icon"
            variant="outline"
            aria-label="Tải ảnh lên"
            onClick={handleUploadImage}
            disabled={isLoading || disabled}
          >
            <ImageIcon className="h-4 w-4" />
          </Button>
          <input
            type="file"
            ref={imageInputRef}
            className="hidden"
            onChange={handleFileChange}
            accept="image/*"
            multiple
            disabled={isLoading || disabled}
          />
        </div>
        
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {attachments.map((file, index) => (
              <div key={index} className="relative bg-muted p-2 rounded-md">
                {file.type.startsWith("image/") ? (
                  <div className="flex items-center gap-2">
                    <img
                      src={URL.createObjectURL(file)}
                      alt={file.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                    <span className="text-sm truncate max-w-[100px]">{file.name}</span>
                  </div>
                ) : (
                  <span className="text-sm truncate max-w-[150px]">{file.name}</span>
                )}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="ml-1 h-5 w-5"
                  onClick={() => removeAttachment(index)}
                  disabled={isLoading}
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        )}
        
        <div className="flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Chế độ xem lịch sử - không thể chat" : "Nhập tin nhắn của bạn..."}
            className="min-h-[60px] max-h-[200px] resize-none"
            disabled={isLoading || disabled}
          />
          <Button
            type="submit"
            size="icon"
            className="bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90"
            disabled={(!message.trim() && attachments.length === 0) || isLoading || disabled}
          >
            {isLoading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
});

ChatInput.displayName = "ChatInput";

export default ChatInput; 