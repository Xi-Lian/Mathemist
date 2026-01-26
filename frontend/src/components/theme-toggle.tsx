"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { TooltipIconButton } from "@/components/thread/tooltip-icon-button";
import { cn } from "@/lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className={cn("size-6", className)} />;
  }

  const isBasalt = theme === "basalt";

  return (
    <TooltipIconButton
      tooltip={isBasalt ? "Switch to paper" : "Switch to basalt"}
      onClick={() => setTheme(isBasalt ? "paper" : "basalt")}
      className={className}
    >
      {isBasalt ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </TooltipIconButton>
  );
}
