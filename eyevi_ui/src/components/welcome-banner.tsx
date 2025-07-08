"use client";

import React from "react";
import { Button } from "./ui/button";
import { MessageCircle, Eye, ShoppingBag, Search, Sparkles } from "lucide-react";

interface WelcomeBannerProps {
  onStartChat: () => void;
}

const WelcomeBanner: React.FC<WelcomeBannerProps> = ({ onStartChat }) => {
  return (
    <div className="fixed inset-0 bg-background/95 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-card border border-border rounded-2xl shadow-2xl p-8 text-center">
        {/* Logo/Icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
              <Eye className="w-10 h-10 text-primary" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-primary-foreground" />
            </div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-foreground mb-4">
          Chào mừng đến với EyeVi
        </h1>
        
        {/* Subtitle */}
        <p className="text-lg text-muted-foreground mb-8">
          Trợ lý ảo thông minh hỗ trợ bạn mua sắm kính mắt
        </p>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="flex flex-col items-center p-4 rounded-lg bg-muted/50">
            <Search className="w-8 h-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Tìm kiếm thông minh</h3>
            <p className="text-sm text-muted-foreground text-center">
              Tìm kiếm kính mắt theo nhu cầu, phong cách và ngân sách của bạn
            </p>
          </div>
          
          <div className="flex flex-col items-center p-4 rounded-lg bg-muted/50">
            <MessageCircle className="w-8 h-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Tư vấn cá nhân</h3>
            <p className="text-sm text-muted-foreground text-center">
              Nhận tư vấn chuyên nghiệp về sản phẩm phù hợp với khuôn mặt
            </p>
          </div>
          
          <div className="flex flex-col items-center p-4 rounded-lg bg-muted/50">
            <ShoppingBag className="w-8 h-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Mua sắm dễ dàng</h3>
            <p className="text-sm text-muted-foreground text-center">
              Đặt hàng nhanh chóng và theo dõi đơn hàng một cách tiện lợi
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <Button 
          onClick={onStartChat}
          size="lg"
          className="px-8 py-3 text-lg font-semibold bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
        >
          <MessageCircle className="w-5 h-5 mr-2" />
          Bắt đầu chat ngay
        </Button>
        
        {/* Footer text */}
        <p className="text-xs text-muted-foreground mt-6">
          Nhấn "Bắt đầu chat ngay" để tạo cuộc trò chuyện mới và khám phá các sản phẩm kính mắt
        </p>
      </div>
    </div>
  );
};

export default WelcomeBanner;
