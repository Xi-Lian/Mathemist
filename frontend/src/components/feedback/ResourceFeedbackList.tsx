"use client";

import { useMemo } from "react";
import { ResourceFeedbackButtons } from "./ResourceFeedbackButtons";
import { parseResourcesFromResponse } from "./resourceParser";

interface ResourceFeedbackListProps {
  messageText: string;
  apiBaseUrl: string;
  query: string;
}

export function ResourceFeedbackList({
  messageText,
  apiBaseUrl,
  query,
}: ResourceFeedbackListProps) {
  const resources = useMemo(
    () => parseResourcesFromResponse(messageText),
    [messageText],
  );

  if (!resources.length) return null;

  return (
    <div className="mt-3 overflow-hidden rounded-lg border bg-card">
      <div className="border-b bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
        请对下方资源进行点赞/点踩（每个资源仅可反馈一次）
      </div>
      <div className="divide-y">
        {resources.map((resource) => (
          <div
            key={resource.resourceId}
            className="flex items-center justify-between gap-3 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{resource.title}</p>
              <p className="truncate text-xs text-muted-foreground">
                {resource.source || resource.category}
              </p>
            </div>
            <ResourceFeedbackButtons
              apiBaseUrl={apiBaseUrl}
              resourceId={resource.resourceId}
              query={query}
              resourceType={resource.resourceType}
              metadata={{
                source: resource.source,
                category: resource.category,
                title: resource.title,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
