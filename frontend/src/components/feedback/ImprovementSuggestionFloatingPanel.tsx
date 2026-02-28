"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageCircleWarning } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ImprovementSuggestionBox } from "./ImprovementSuggestionBox";

interface ImprovementSuggestionFloatingPanelProps {
  apiBaseUrl: string;
  query: string;
  className?: string;
}

export function ImprovementSuggestionFloatingPanel({
  apiBaseUrl,
  query,
  className,
}: ImprovementSuggestionFloatingPanelProps) {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div
      className={cn(
        "pointer-events-none fixed bottom-6 left-2 z-30",
        className,
      )}
    >
      <div className="pointer-events-auto flex items-end gap-2">
        {!collapsed && (
          <section className="w-[min(90vw,360px)] overflow-hidden rounded-xl border bg-background/95 shadow-xl backdrop-blur supports-[backdrop-filter]:bg-background/85">
            <header className="flex items-center justify-between border-b px-3 py-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <MessageCircleWarning className="size-4 text-blue-600" />
                <span>问题反馈</span>
              </div>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => setCollapsed(true)}
                aria-label="收起建议面板"
              >
                <ChevronLeft className="size-4" />
              </Button>
            </header>
            <div className="p-2">
              <ImprovementSuggestionBox
                apiBaseUrl={apiBaseUrl}
                query={query}
                className="w-full border-0 bg-transparent p-1 shadow-none"
              />
            </div>
          </section>
        )}

        {collapsed && (
          <Button
            type="button"
            variant="outline"
            className="h-12 rounded-r-xl rounded-l-sm px-2 shadow-md"
            onClick={() => setCollapsed(false)}
            aria-label="展开建议面板"
          >
            <ChevronRight className="mr-1 size-4" />
            建议
          </Button>
        )}
      </div>
    </div>
  );
}
