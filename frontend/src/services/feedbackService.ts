"use client";

export const RESOURCE_FEEDBACK_STORAGE_KEY = "resource_feedback_cache_v1";

export const DISLIKE_REASONS = ["主题不对", "难度不合适", "类型不对", "其他"] as const;

export type DislikeReason = (typeof DISLIKE_REASONS)[number];

export interface ResourceFeedbackPayload {
  resource_id: string;
  is_like: boolean;
  query: string;
  resource_type: string;
  metadata?: Record<string, unknown>;
  dislike_reason?: string;
}

export interface SuggestionPayload {
  query: string;
  suggestion: string;
  contact?: string;
}

export interface FeedbackApiResponse {
  success: boolean;
  message?: string;
}

export interface StoredResourceFeedback {
  isLike: boolean;
  reason?: string;
}

export type StoredFeedbackMap = Record<string, StoredResourceFeedback>;

function ensureNoTrailingSlash(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

async function parseResponse(response: Response): Promise<FeedbackApiResponse> {
  const raw = (await response.json().catch(() => ({}))) as
    | FeedbackApiResponse
    | [FeedbackApiResponse, number];

  // Backward-compatible parsing for tuple-like payloads such as:
  // [{ success: false, message: "..." }, 400]
  const data: FeedbackApiResponse =
    Array.isArray(raw) && raw.length > 0 && typeof raw[0] === "object"
      ? (raw[0] as FeedbackApiResponse)
      : (raw as FeedbackApiResponse);

  if (!response.ok || data.success === false) {
    throw new Error(data.message || "请求失败，请稍后重试");
  }

  return data;
}

export async function submitResourceFeedback(
  apiBaseUrl: string,
  payload: ResourceFeedbackPayload,
): Promise<FeedbackApiResponse> {
  const response = await fetch(
    `${ensureNoTrailingSlash(apiBaseUrl)}/feedback/resource`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  return parseResponse(response);
}

export async function submitImprovementSuggestion(
  apiBaseUrl: string,
  payload: SuggestionPayload,
): Promise<FeedbackApiResponse> {
  const response = await fetch(
    `${ensureNoTrailingSlash(apiBaseUrl)}/feedback/suggestion`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  return parseResponse(response);
}

export function readStoredResourceFeedback(): StoredFeedbackMap {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.localStorage.getItem(RESOURCE_FEEDBACK_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as StoredFeedbackMap;
    return typeof parsed === "object" && parsed !== null ? parsed : {};
  } catch {
    return {};
  }
}

export function writeStoredResourceFeedback(feedbackMap: StoredFeedbackMap): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    RESOURCE_FEEDBACK_STORAGE_KEY,
    JSON.stringify(feedbackMap),
  );
}
