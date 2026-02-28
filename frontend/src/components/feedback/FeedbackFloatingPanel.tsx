"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, MessageSquareHeart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { parseResourcesFromResponse } from "./resourceParser";
import { ResourceFeedbackList } from "./ResourceFeedbackList";

interface FeedbackFloatingPanelProps {
  messageText: string;
  apiBaseUrl: string;
  query: string;
  className?: string;
}

export function FeedbackFloatingPanel({
  messageText,
  apiBaseUrl,
  query,
  className,
}: FeedbackFloatingPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const resources = useMemo(
    () => parseResourcesFromResponse(messageText),
    [messageText],
  );

  if (!resources.length) return null;

  return (
    <div
      className={cn(
        "pointer-events-none fixed top-1/2 left-2 z-30 -translate-y-1/2",
        className,
      )}
    >
      <div className="pointer-events-auto flex items-start gap-2">
        {!collapsed && (
          <section className="w-[min(90vw,360px)] overflow-hidden rounded-xl border bg-background/95 shadow-xl backdrop-blur supports-[backdrop-filter]:bg-background/85">
            <header className="flex items-center justify-between border-b px-3 py-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <MessageSquareHeart className="size-4 text-blue-600" />
                <span>资源反馈</span>
              </div>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => setCollapsed(true)}
                aria-label="收起反馈面板"
              >
                <ChevronLeft className="size-4" />
              </Button>
            </header>
            <div className="max-h-[68vh] overflow-y-auto px-2 pb-2">
              <ResourceFeedbackList
                messageText={messageText}
                apiBaseUrl={apiBaseUrl}
                query={query}
                className="mt-2"
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
            aria-label="展开反馈面板"
          >
            <ChevronRight className="mr-1 size-4" />
            反馈
          </Button>
        )}
      </div>
    </div>
  );
}
