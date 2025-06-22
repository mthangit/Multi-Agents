import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "EyeVi - Chatbot hỗ trợ mua sắm mắt kính",
  description: "Chatbot hỗ trợ mua sắm mắt kính trực tuyến sử dụng mô hình ngôn ngữ lớn",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={cn("min-h-screen bg-background", inter.variable)}>
        {children}
      </body>
    </html>
  );
} 