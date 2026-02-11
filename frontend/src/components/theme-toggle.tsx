"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { TooltipIconButton } from "@/components/thread/tooltip-icon-button";
import { cn } from "@/lib/utils";
import { useI18n } from "@/providers/I18n";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const { t } = useI18n();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className={cn("h-8 w-8", className)} />;
  }

  const isBasalt = theme === "basalt";

  return (
    <TooltipIconButton
      tooltip={isBasalt ? t.switchToPaper : t.switchToBasalt}
      onClick={() => setTheme(isBasalt ? "paper" : "basalt")}
      className={className}
    >
      {isBasalt ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </TooltipIconButton>
  );
}
