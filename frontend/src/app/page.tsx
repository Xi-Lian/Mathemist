"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { Toaster } from "@/components/ui/sonner";
import React, { useEffect } from "react";
import { useQueryState } from "nuqs";

function ChatPage() {
  const [threadId, setThreadId] = useQueryState("threadId");
  
  useEffect(() => {
    // 当用户首次访问时，清除threadId以创建新会话
    // 检查是否是新的访问（例如，通过检查localStorage中的标志）
    const hasVisitedBefore = localStorage.getItem("mathemist_has_visited");
    if (!hasVisitedBefore && threadId) {
      // 首次访问，清除threadId
      setThreadId(null);
      localStorage.setItem("mathemist_has_visited", "true");
    } else if (!hasVisitedBefore) {
      // 设置访问标志
      localStorage.setItem("mathemist_has_visited", "true");
    }
  }, [threadId, setThreadId]);

  return (
    <ThreadProvider>
      <StreamProvider>
        <ArtifactProvider>
          <Thread />
        </ArtifactProvider>
      </StreamProvider>
    </ThreadProvider>
);
}

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <ChatPage />
    </React.Suspense>
  );
}
