"use client";

import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Button } from "./ui/button";
import { useTheme } from "./theme-provider";

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="relative w-10 h-10 rounded-xl transition-all duration-300 border border-sidebar-border/50"
        disabled
      >
        <div className="relative flex items-center justify-center">
          <Sun className="h-4 w-4 opacity-50 text-amber-500" />
        </div>
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="relative w-10 h-10 rounded-xl transition-all duration-300 hover:bg-sidebar-accent/60 hover:shadow-lg hover:scale-105 active:scale-95 active:bg-sidebar-accent/80 border border-sidebar-border/50 hover:border-sidebar-border"
      aria-label={`Chuyển sang ${theme === "light" ? "dark" : "light"} mode`}
    >
      <div className="relative flex items-center justify-center">
        <Sun
          className={`h-4 w-4 absolute transition-all duration-500 ease-in-out text-amber-500 ${
            theme === "light"
              ? "rotate-0 scale-100 opacity-100"
              : "rotate-180 scale-0 opacity-0"
          }`}
        />
        <Moon
          className={`h-4 w-4 absolute transition-all duration-500 ease-in-out text-blue-400 ${
            theme === "dark"
              ? "rotate-0 scale-100 opacity-100"
              : "-rotate-180 scale-0 opacity-0"
          }`}
        />
      </div>
      
      {/* Glow effect */}
      <div className={`absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300 ${
        theme === "light" 
          ? "bg-amber-500/10 hover:opacity-100" 
          : "bg-blue-400/10 hover:opacity-100"
      }`} />
    </Button>
  );
};

export default ThemeToggle; 