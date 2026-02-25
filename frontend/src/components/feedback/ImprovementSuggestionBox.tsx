"use client";

import { useEffect, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { submitImprovementSuggestion } from "@/services/feedbackService";

interface ImprovementSuggestionBoxProps {
  apiBaseUrl: string;
  query: string;
}

const MIN_SUGGESTION_LENGTH = 10;

export function ImprovementSuggestionBox({
  apiBaseUrl,
  query,
}: ImprovementSuggestionBoxProps) {
  const [suggestion, setSuggestion] = useState("");
  const [contact, setContact] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = `${Math.min(
      textareaRef.current.scrollHeight,
      220,
    )}px`;
  }, [suggestion]);

  const trimmedSuggestion = suggestion.trim();
  const canSubmit = trimmedSuggestion.length >= MIN_SUGGESTION_LENGTH && !isSubmitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;

    setIsSubmitting(true);
    try {
      await submitImprovementSuggestion(apiBaseUrl, {
        query,
        suggestion: trimmedSuggestion,
        contact: contact.trim() || undefined,
      });
      setSuggestion("");
      setContact("");
      toast.success("感谢您的建议！");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "提交失败，请稍后重试");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto mb-4 w-full max-w-[min(960px,100%)] rounded-2xl border bg-card p-4">
      <h3 className="text-sm font-semibold">没有找到想要的资源？告诉我们</h3>
      <div className="mt-3 space-y-3">
        <textarea
          ref={textareaRef}
          value={suggestion}
          onChange={(e) => setSuggestion(e.target.value)}
          placeholder="输入您的建议...（至少10个字）"
          className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex max-h-[220px] min-h-[88px] w-full resize-none rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:ring-[3px]"
        />
        <Input
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          placeholder="联系方式（可选）"
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            {trimmedSuggestion.length < MIN_SUGGESTION_LENGTH
              ? `至少输入 ${MIN_SUGGESTION_LENGTH} 个字`
              : "建议长度已满足要求"}
          </p>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
          >
            {isSubmitting ? (
              <>
                <LoaderCircle className="size-4 animate-spin" />
                提交中
              </>
            ) : (
              "提交建议"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
