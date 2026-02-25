"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DISLIKE_REASONS, type DislikeReason } from "@/services/feedbackService";

interface DislikeReasonModalProps {
  open: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (reason: DislikeReason, otherText: string) => void;
}

export function DislikeReasonModal({
  open,
  submitting,
  onClose,
  onSubmit,
}: DislikeReasonModalProps) {
  const [selectedReason, setSelectedReason] = useState<DislikeReason | "">("");
  const [otherText, setOtherText] = useState("");

  useEffect(() => {
    if (!open) {
      setSelectedReason("");
      setOtherText("");
    }
  }, [open]);

  if (!open) return null;

  const showOtherInput = selectedReason === "其他";
  const canSubmit = selectedReason !== "" && !submitting;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !submitting) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-xl border bg-background p-4 shadow-lg">
        <h3 className="text-base font-semibold">这个资源不相关的原因是？</h3>
        <div className="mt-3 space-y-2">
          {DISLIKE_REASONS.map((reason) => (
            <label
              key={reason}
              className="flex cursor-pointer items-center gap-2 text-sm"
            >
              <input
                type="radio"
                name="dislike_reason"
                checked={selectedReason === reason}
                onChange={() => setSelectedReason(reason)}
                disabled={submitting}
              />
              <span>{reason}</span>
            </label>
          ))}
        </div>

        {showOtherInput && (
          <div className="mt-3">
            <Input
              value={otherText}
              onChange={(e) => setOtherText(e.target.value)}
              placeholder="其他说明（可选）"
              disabled={submitting}
            />
          </div>
        )}

        <div className="mt-4 flex items-center justify-end gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={submitting}
          >
            取消
          </Button>
          <Button
            onClick={() => {
              if (!selectedReason) return;
              onSubmit(selectedReason, otherText.trim());
            }}
            disabled={!canSubmit}
          >
            提交
          </Button>
        </div>
      </div>
    </div>
  );
}
