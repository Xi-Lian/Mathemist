"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  FileQuestion,
  Lightbulb,
  Tag,
  Star,
  Target,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type ExerciseDetail } from "@/providers/Stream";
import { MarkdownText } from "../markdown-text";

const QUESTION_TYPE_ICON: Record<string, string> = {
  "选择题": "🔤",
  "填空题": "📝",
  "解答题": "📐",
  "证明题": "🔍",
  "计算题": "🔢",
  "判断题": "✅",
  "应用题": "📋",
};

const QUESTION_TYPE_COLOR: Record<string, string> = {
  "选择题": "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  "填空题": "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  "解答题": "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  "证明题": "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  "计算题": "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
  "判断题": "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300",
  "应用题": "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
};

function resolveImageUrl(url: string, apiUrl?: string | null): string {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  const base = (apiUrl || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/langgraph/math-agent");
  const root = base.includes("/langgraph") ? base.split("/langgraph")[0] : base;
  return `${root.replace(/\/$/, "")}/langgraph/math-agent/files/open?path=${encodeURIComponent(url)}`;
}

function DifficultyStars({ difficulty }: { difficulty: string }) {
  const level = parseInt(difficulty, 10) || 0;
  if (level <= 0) return null;
  return (
    <div className="flex items-center gap-0.5" title={`难度: ${level}/5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          className={cn(
            "size-3",
            i < level
              ? "fill-amber-400 text-amber-400"
              : "text-muted-foreground/30"
          )}
        />
      ))}
    </div>
  );
}

function RelevanceBadge({ relevance }: { relevance: number }) {
  if (!relevance && relevance !== 0) return null;
  const pct = Math.round(relevance * 100);
  let colorClass = "bg-muted text-muted-foreground";
  if (pct >= 70) colorClass = "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300";
  else if (pct >= 40) colorClass = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
  else colorClass = "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";

  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", colorClass)}>
      <Target className="size-3" />
      {pct}%
    </span>
  );
}

interface ExerciseCardProps {
  detail: ExerciseDetail;
  index: number;
  total: number;
  apiUrl?: string | null;
}

export function ExerciseCard({ detail, index, total, apiUrl }: ExerciseCardProps) {
  const [showAnswer, setShowAnswer] = useState(false);

  const typeIcon = QUESTION_TYPE_ICON[detail.question_type] || "📄";
  const typeColorClass =
    QUESTION_TYPE_COLOR[detail.question_type] ||
    "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";

  const knowledgeTags = detail.knowledge_tags
    .split(/[;；,，]/)
    .map((t) => t.trim())
    .filter(Boolean);

  const questionImageUrl = resolveImageUrl(detail.question_image_url, apiUrl);
  const answerImageUrl = resolveImageUrl(detail.answer_image_url, apiUrl);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className="group overflow-hidden rounded-xl border bg-card shadow-sm transition-shadow hover:shadow-md"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <FileQuestion className="size-4 flex-shrink-0 text-primary" />
          <span className="text-sm font-semibold truncate">
            {detail.title || `习题 ${index + 1}`}
          </span>
          {total > 1 && (
            <span className="text-xs text-muted-foreground flex-shrink-0">
              {index + 1}/{total}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <RelevanceBadge relevance={detail.relevance} />
          <DifficultyStars difficulty={detail.difficulty} />
        </div>
      </div>

      {/* Question Section */}
      <div className="px-4 py-3">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 flex-shrink-0 text-lg">{typeIcon}</span>
          <div className="min-w-0 flex-1">
            {/* Type badge */}
            <span className={cn("mb-2 inline-block rounded-md px-2 py-0.5 text-xs font-medium", typeColorClass)}>
              {detail.question_type}
            </span>

            {/* Question content */}
            {detail.is_image_exercise && questionImageUrl ? (
              <div className="mt-2">
                <img
                  src={questionImageUrl}
                  alt="题目图片"
                  className="max-h-64 w-auto max-w-full rounded-lg border object-contain"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="mt-2 text-sm leading-relaxed">
                <MarkdownText>{detail.question || "(题目文本缺失)"}</MarkdownText>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Knowledge Tags */}
      {knowledgeTags.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 px-4 pb-2">
          <Tag className="size-3 flex-shrink-0 text-muted-foreground" />
          {knowledgeTags.map((tag, i) => (
            <span
              key={i}
              className="inline-block rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Answer Toggle */}
      <div className="border-t">
        <button
          type="button"
          onClick={() => setShowAnswer(!showAnswer)}
          className="flex w-full items-center justify-between px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
        >
          <span className="flex items-center gap-2">
            <Lightbulb className="size-4" />
            {showAnswer ? "收起解析" : "查看解析"}
          </span>
          {showAnswer ? (
            <ChevronUp className="size-4" />
          ) : (
            <ChevronDown className="size-4" />
          )}
        </button>

        <AnimatePresence initial={false}>
          {showAnswer && (
            <motion.div
              key="answer-content"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="border-t bg-muted/20 px-4 py-3">
                {detail.is_image_exercise && answerImageUrl ? (
                  <img
                    src={answerImageUrl}
                    alt="答案解析图片"
                    className="max-h-64 w-auto max-w-full rounded-lg border object-contain"
                    loading="lazy"
                  />
                ) : (
                  <div className="text-sm leading-relaxed">
                    <MarkdownText>{detail.answer || "(解析内容缺失)"}</MarkdownText>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer: source info */}
      {(detail.source || detail.filename) && (
        <div className="flex items-center gap-2 border-t px-4 py-2 text-xs text-muted-foreground">
          <Eye className="size-3" />
          <span className="truncate">
            {detail.source || detail.filename}
          </span>
        </div>
      )}
    </motion.div>
  );
}

export function ExerciseCardList({
  details,
  apiUrl,
}: {
  details: ExerciseDetail[];
  apiUrl?: string | null;
}) {
  if (!details || details.length === 0) return null;

  return (
    <div className="my-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <FileQuestion className="size-4" />
        <span>检索到 {details.length} 道习题</span>
      </div>
      {details.map((detail, idx) => (
        <ExerciseCard
          key={idx}
          detail={detail}
          index={idx}
          total={details.length}
          apiUrl={apiUrl}
        />
      ))}
    </div>
  );
}
