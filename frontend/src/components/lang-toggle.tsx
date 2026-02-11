"use client";

import { Languages } from "lucide-react";
import { useI18n } from "@/providers/I18n";
import { TooltipIconButton } from "@/components/thread/tooltip-icon-button";

const langNames = {
  "zh-CN": { switchTo: "Switch to English", name: "中文" },
  "en-US": { switchTo: "切换到中文", name: "English" },
} as const;

export function LangToggle() {
  const { language, setLanguage } = useI18n();

  return (
    <TooltipIconButton
      tooltip={langNames[language].switchTo}
      variant="ghost"
      onClick={() => setLanguage(language === "zh-CN" ? "en-US" : "zh-CN")}
    >
      <Languages className="size-4" />
    </TooltipIconButton>
  );
}
