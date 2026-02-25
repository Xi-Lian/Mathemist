"use client";

import { useEffect, useMemo, useState } from "react";
import { LoaderCircle, ThumbsDown, ThumbsUp } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  readStoredResourceFeedback,
  submitResourceFeedback,
  writeStoredResourceFeedback,
  type DislikeReason,
  type StoredResourceFeedback,
} from "@/services/feedbackService";
import { DislikeReasonModal } from "./DislikeReasonModal";

interface ResourceFeedbackButtonsProps {
  apiBaseUrl: string;
  resourceId: string;
  query: string;
  resourceType: string;
  metadata?: Record<string, unknown>;
}

export function ResourceFeedbackButtons({
  apiBaseUrl,
  resourceId,
  query,
  resourceType,
  metadata,
}: ResourceFeedbackButtonsProps) {
  const [storedFeedback, setStoredFeedback] = useState<StoredResourceFeedback | null>(
    null,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDislikeModal, setShowDislikeModal] = useState(false);
  const [optimisticChoice, setOptimisticChoice] = useState<"like" | "dislike" | null>(
    null,
  );

  useEffect(() => {
    const feedbackMap = readStoredResourceFeedback();
    setStoredFeedback(feedbackMap[resourceId] ?? null);
  }, [resourceId]);

  const effectiveChoice = useMemo(() => {
    if (optimisticChoice) return optimisticChoice;
    if (!storedFeedback) return null;
    return storedFeedback.isLike ? "like" : "dislike";
  }, [optimisticChoice, storedFeedback]);

  const alreadySubmitted = Boolean(storedFeedback);

  const persistFeedback = (nextFeedback: StoredResourceFeedback) => {
    const currentMap = readStoredResourceFeedback();
    currentMap[resourceId] = nextFeedback;
    writeStoredResourceFeedback(currentMap);
    setStoredFeedback(nextFeedback);
  };

  const rollbackOptimisticState = () => {
    setOptimisticChoice(null);
    setIsSubmitting(false);
  };

  const handleLike = async () => {
    if (alreadySubmitted || isSubmitting) return;

    setOptimisticChoice("like");
    setIsSubmitting(true);

    try {
      await submitResourceFeedback(apiBaseUrl, {
        resource_id: resourceId,
        is_like: true,
        query,
        resource_type: resourceType,
        metadata,
      });
      persistFeedback({ isLike: true });
      toast.success("感谢您的反馈！");
    } catch (error) {
      rollbackOptimisticState();
      toast.error(error instanceof Error ? error.message : "提交失败，请稍后重试");
      return;
    }

    setOptimisticChoice(null);
    setIsSubmitting(false);
  };

  const handleDislikeSubmit = async (reason: DislikeReason, otherText: string) => {
    if (alreadySubmitted || isSubmitting) return;

    setShowDislikeModal(false);
    setOptimisticChoice("dislike");
    setIsSubmitting(true);

    const extraMetadata =
      reason === "其他" && otherText
        ? { ...metadata, other_reason_detail: otherText }
        : metadata;

    const reasonToStore =
      reason === "其他" && otherText ? `其他: ${otherText}` : reason;

    try {
      await submitResourceFeedback(apiBaseUrl, {
        resource_id: resourceId,
        is_like: false,
        query,
        resource_type: resourceType,
        metadata: extraMetadata,
        dislike_reason: reason,
      });
      persistFeedback({ isLike: false, reason: reasonToStore });
      toast.success("感谢您的反馈！");
    } catch (error) {
      rollbackOptimisticState();
      toast.error(error instanceof Error ? error.message : "提交失败，请稍后重试");
      return;
    }

    setOptimisticChoice(null);
    setIsSubmitting(false);
  };

  return (
    <>
      <div className="flex items-center gap-1">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className={
            effectiveChoice === "like"
              ? "text-green-600 hover:text-green-700"
              : "text-muted-foreground hover:text-foreground"
          }
          disabled={alreadySubmitted || isSubmitting}
          onClick={handleLike}
          title={alreadySubmitted ? "该资源已反馈" : "点赞"}
        >
          {isSubmitting && effectiveChoice === "like" ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : (
            <ThumbsUp className="size-4" />
          )}
        </Button>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className={
            effectiveChoice === "dislike"
              ? "text-red-600 hover:text-red-700"
              : "text-muted-foreground hover:text-foreground"
          }
          disabled={alreadySubmitted || isSubmitting}
          onClick={() => setShowDislikeModal(true)}
          title={alreadySubmitted ? "该资源已反馈" : "点踩"}
        >
          {isSubmitting && effectiveChoice === "dislike" ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : (
            <ThumbsDown className="size-4" />
          )}
        </Button>
      </div>

      <DislikeReasonModal
        open={showDislikeModal}
        submitting={isSubmitting}
        onClose={() => setShowDislikeModal(false)}
        onSubmit={handleDislikeSubmit}
      />
    </>
  );
}
