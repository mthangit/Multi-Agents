"use client";

import React, { useRef, useEffect } from "react";

interface PopoverProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

function useOnClickOutside(ref: React.RefObject<HTMLElement>, handler: () => void) {
  useEffect(() => {
    const listener = (event: MouseEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) {
        return;
      }
      handler();
    };
    document.addEventListener("mousedown", listener);
    return () => {
      document.removeEventListener("mousedown", listener);
    };
  }, [ref, handler]);
}

export const Popover: React.FC<PopoverProps> & {
  Trigger: React.FC<{ asChild?: boolean; children: React.ReactNode }>;
  Content: React.FC<{ align?: "start" | "end"; className?: string; children: React.ReactNode }>;
} = ({ open, onOpenChange, children }) => {
  // Tách children thành Trigger và Content
  let trigger: React.ReactNode = null;
  let content: React.ReactNode = null;
  React.Children.forEach(children, (child: any) => {
    if (child?.type?.displayName === "PopoverTrigger") trigger = child;
    if (child?.type?.displayName === "PopoverContent") content = child;
  });
  return (
    <div className="relative inline-block">
      {trigger && React.isValidElement(trigger)
        ? (typeof (trigger as React.ReactElement<any, any>).type === 'string' && (trigger as React.ReactElement<any, any>).type === 'button')
          ? React.cloneElement(trigger as React.ReactElement<any, any>, { onClick: () => onOpenChange(!open) })
          : <span onClick={() => onOpenChange(!open)}>{trigger}</span>
        : <span onClick={() => onOpenChange(!open)}>{trigger}</span>
      }
      {open && content}
    </div>
  );
};

const PopoverTrigger: React.FC<{ asChild?: boolean; children: React.ReactNode; onClick?: () => void }> = ({ asChild, children, onClick }) => {
  if (asChild && React.isValidElement(children)) {
    return (typeof (children as React.ReactElement<any, any>).type === 'string' && (children as React.ReactElement<any, any>).type === 'button')
      ? React.cloneElement(children as React.ReactElement<any, any>, { onClick })
      : <span onClick={onClick}>{children}</span>;
  }
  if (React.isValidElement(children)) {
    return (typeof (children as React.ReactElement<any, any>).type === 'string' && (children as React.ReactElement<any, any>).type === 'button')
      ? React.cloneElement(children as React.ReactElement<any, any>, { onClick })
      : <span onClick={onClick}>{children}</span>;
  }
  return (
    <button type="button" onClick={onClick} className="outline-none">
      {children}
    </button>
  );
};
PopoverTrigger.displayName = "PopoverTrigger";
Popover.Trigger = PopoverTrigger;

const PopoverContent: React.FC<{ align?: "start" | "end"; className?: string; children: React.ReactNode }> = ({ align = "start", className = "", children }) => {
  const ref = useRef<HTMLDivElement>(null);
  useOnClickOutside(ref as React.RefObject<HTMLElement>, () => {
    // Không làm gì ở đây, sẽ đóng từ parent
  });
  return (
    <div
      ref={ref}
      className={`absolute z-50 ${align === "end" ? "right-0" : "left-0"} ${className}`}
      tabIndex={-1}
    >
      {children}
    </div>
  );
};
PopoverContent.displayName = "PopoverContent";
Popover.Content = PopoverContent;

export default Popover; 