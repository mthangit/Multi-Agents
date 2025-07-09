"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { User, Bot, Loader2 } from "lucide-react";
import Image from "next/image";
import { ProductData, OrderData } from "@/hooks/useChatApi";
import ProductList from "./product-list";
import OrderList from "./order-list";
import MarkdownRenderer from "./markdown-renderer";

interface Attachment {
  name: string;
  url: string;
  type: string;
}

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  attachments?: Attachment[];
  products?: ProductData[];
  extracted_product_ids?: string[];
  orders?: OrderData[];
  agent_used?: string;
  is_loading?: boolean;
  loading_step?: string;
}

interface ChatMessagesProps {
  messages: Message[];
}

const ChatMessages = ({ messages }: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderAttachment = (attachment: Attachment) => {
    if (attachment.type.startsWith("image/")) {
      return (
        <a href={attachment.url} target="_blank" rel="noopener noreferrer" className="block">
          <Image 
            src={attachment.url} 
            alt={attachment.name} 
            width={200}
            height={200}
            className="max-w-[200px] max-h-[200px] rounded-md object-contain"
            style={{ width: 'auto', height: 'auto' }}
          />
        </a>
      );
    } else {
      return (
        <a 
          href={attachment.url} 
          download={attachment.name}
          className="flex items-center p-2 bg-muted rounded-md hover:bg-muted/80"
        >
          <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm truncate max-w-[150px]">{attachment.name}</span>
        </a>
      );
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            "flex gap-4",
            message.sender === "user" ? "justify-end" : "justify-start"
          )}
        >
          {message.sender === "bot" && (
            <div className="min-w-10 h-10 rounded-full flex items-center justify-center bg-muted">
              <Bot className="h-6 w-6" />
            </div>
          )}
          
          <div className="flex flex-col gap-1 max-w-[80%]">
            {message.sender === "bot" && message.agent_used && !message.is_loading && (
              <span className="text-xs text-muted-foreground font-medium">
                Agent trả lời: {message.agent_used}
              </span>
            )}
            
            <div
              className={cn(
                "rounded-xl p-3",
                message.sender === "user"
                  ? "bg-primary text-primary-foreground rounded-tr-none"
                  : "bg-muted rounded-tl-none"
              )}
            >
              {message.is_loading ? (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    <span className="text-sm text-muted-foreground font-medium animate-pulse">
                      {message.loading_step || "Đang xử lý..."}
                    </span>
                  </div>
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: "0ms" }}></span>
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: "300ms" }}></span>
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: "600ms" }}></span>
                  </div>
                </div>
              ) : (
                <MarkdownRenderer
                  content={message.content}
                  className={cn(
                    message.sender === "user"
                      ? "text-primary-foreground [&_*]:text-primary-foreground"
                      : "text-foreground"
                  )}
                />
              )}
            </div>
            
            {message.attachments && message.attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-1">
                {message.attachments.map((attachment, index) => (
                  <div key={index}>
                    {renderAttachment(attachment)}
                  </div>
                ))}
              </div>
            )}
            
            {message.sender === "bot" && !message.is_loading && (
              <>
                {message.products && message.products.length > 0 && (
                  <div className="mt-2 w-full">
                    <ProductList products={message.products} initialDisplay={3} loadMoreCount={5} />
                  </div>
                )}

                {message.extracted_product_ids && message.extracted_product_ids.length > 0 && (
                  <div className="mt-2 w-full">
                    <ProductList productIds={message.extracted_product_ids} initialDisplay={3} loadMoreCount={5} />
                  </div>
                )}

                {message.orders && message.orders.length > 0 && (
                  <div className="mt-2 w-full">
                    <OrderList orders={message.orders} initialDisplay={2} loadMoreCount={5} />
                  </div>
                )}
              </>
            )}
            
            <span
              className={cn(
                "text-xs text-muted-foreground",
                message.sender === "user" ? "text-right" : "text-left"
              )}
            >
              {formatTime(message.timestamp)}
            </span>
          </div>
          
          {message.sender === "user" && (
            <div className="min-w-10 h-10 rounded-full flex items-center justify-center bg-primary text-primary-foreground">
              <User className="h-6 w-6" />
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages; 