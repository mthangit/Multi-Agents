"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  return (
    <div className={cn(
      "prose prose-sm max-w-none",
      "prose-headings:inherit prose-p:inherit prose-li:inherit",
      "prose-strong:inherit prose-em:inherit",
      "prose-code:inherit prose-pre:bg-muted/20",
      "prose-blockquote:opacity-80 prose-blockquote:border-current",
      "prose-a:text-current prose-a:no-underline hover:prose-a:underline prose-a:opacity-80",
      className
    )}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code blocks với syntax highlighting
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');

            // Kiểm tra xem có phải là code block (có className language-*) hay không
            // Nếu không có className language-* thì đây là inline code
            const isInline = !match;

            if (isInline) {
              return (
                <code
                  className="bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono border border-current/20"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <pre className="bg-black/5 dark:bg-white/5 p-4 rounded-lg overflow-x-auto border border-current/20">
                <code
                  className={cn(
                    "text-sm font-mono block",
                    className
                  )}
                  {...props}
                >
                  {children}
                </code>
              </pre>
            );
          },

          // Blockquotes với styling đặc biệt
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-current pl-4 py-2 bg-current/10 rounded-r-lg my-4 italic opacity-80">
              <div className="text-sm">
                {children}
              </div>
            </blockquote>
          ),

          // Links mở trong tab mới
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 font-medium opacity-80 hover:opacity-100"
            >
              {children}
            </a>
          ),

          // Tables với styling đẹp hơn
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border border-current/20 rounded-lg overflow-hidden">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-current/10">
              {children}
            </thead>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-current/20 last:border-b-0">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-4 py-3 text-left text-sm font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
