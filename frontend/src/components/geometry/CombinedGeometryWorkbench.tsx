"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GeometryLibrary } from "./GeometryLibrary";

interface SuggestionResponse {
  status?: string;
  data?: {
    suggestions?: string;
  };
  error?: string;
}

function normalizeBaseUrl(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export function CombinedGeometryWorkbench() {
  const searchParams = useSearchParams();
  // V48.8修复：使用 useState + useEffect 避免 Hydration 不匹配
  const [apiBaseUrl, setApiBaseUrl] = useState("http://localhost:8000");
  const [isMounted, setIsMounted] = useState(false);
  
  // 在客户端挂载后初始化 apiBaseUrl
  useEffect(() => {
    const initialApiFromQuery = searchParams.get("apiUrl")?.trim() ?? "";
    // V48.9修复：GGB接口不使用包含 /langgraph/math-agent 的 URL
    // 无论是查询参数还是环境变量，都需要提取基础 URL
    let baseUrl: string;
    
    if (initialApiFromQuery) {
      // 从查询参数中提取基础 URL（去掉 /langgraph/math-agent）
      baseUrl = initialApiFromQuery.replace(/\/langgraph\/math-agent$/, "");
    } else {
      // 从 NEXT_PUBLIC_API_URL 中提取基础 URL（去掉 /langgraph/math-agent）
      const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      baseUrl = envUrl.replace(/\/langgraph\/math-agent$/, "");
    }
    
    setApiBaseUrl(baseUrl);
    setIsMounted(true);
  }, [searchParams]);
  const [chapter, setChapter] = useState("");
  const [topic, setTopic] = useState("");
  const [teachingPurpose, setTeachingPurpose] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resultMarkdown, setResultMarkdown] = useState("");
  const [errorText, setErrorText] = useState("");

  const placeholder = useMemo(
    () =>
      '填写左侧表单，点击"获取建议"。建议会显示在这里，你可以在右侧图形库中直接画图。',
    [],
  );

  const handleFetchSuggestions = async () => {
    if (!chapter.trim() || !topic.trim() || !teachingPurpose.trim()) {
      setErrorText("请填写章节、主题、教学用途后再提交。");
      return;
    }

    setIsSubmitting(true);
    setErrorText("");
    setResultMarkdown("");

    try {
      const response = await fetch(
        `${normalizeBaseUrl(apiBaseUrl)}/ggb/innovation-suggestions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chapter: chapter.trim(),
            topic: topic.trim(),
            teaching_purpose: teachingPurpose.trim(),
          }),
        },
      );

      const data = (await response.json().catch(() => ({}))) as SuggestionResponse;

      if (!response.ok) {
        throw new Error(`请求失败（${response.status}）`);
      }

      if (data.status !== "success" || !data.data) {
        throw new Error(data.error || "获取建议失败");
      }

      const markdown =
        data.data.suggestions?.trim() || "未返回详细建议，请稍后重试。";
      setResultMarkdown(markdown);
    } catch (error) {
      const msg =
        error instanceof Error ? error.message : "获取建议失败，请稍后重试。";
      setErrorText(
        `调用后端建议接口失败：${msg}。请确认后端服务与接口已启动。`,
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClear = () => {
    setChapter("");
    setTopic("");
    setTeachingPurpose("");
    setErrorText("");
    setResultMarkdown("");
  };

  return (
    <main className="min-h-screen bg-muted/30 p-4 md:p-6">
      <div className="mx-auto max-w-[1800px] rounded-2xl border bg-background p-4 md:p-6">
        <h1 className="mb-5 text-center text-2xl font-semibold md:text-3xl">
          画图建议 + 图形库
        </h1>

        <div className="grid gap-6 lg:grid-cols-[460px_1fr]">
          <section className="flex min-h-[860px] flex-col gap-4">
            <div className="rounded-xl border bg-muted/30 p-4">
              <h2 className="mb-3 text-base font-medium">获取画图建议</h2>
              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm font-medium">后端地址</label>
                  <Input
                    value={isMounted ? apiBaseUrl : ""}
                    onChange={(e) => setApiBaseUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">章节</label>
                  <Input
                    value={chapter}
                    onChange={(e) => setChapter(e.target.value)}
                    placeholder="例如：三角函数"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">主题</label>
                  <Input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="例如：正弦函数图像"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">教学用途</label>
                  <textarea
                    value={teachingPurpose}
                    onChange={(e) => setTeachingPurpose(e.target.value)}
                    placeholder="例如：帮助学生理解正弦函数的周期性和相位变化"
                    className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 min-h-[120px] w-full resize-y rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-[3px]"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    onClick={handleFetchSuggestions}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <LoaderCircle className="size-4 animate-spin" />
                        获取中
                      </>
                    ) : (
                      "获取建议"
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleClear}
                    disabled={isSubmitting}
                  >
                    清空
                  </Button>
                </div>
              </div>
            </div>

            <div className="min-h-[420px] flex-1 overflow-auto rounded-xl border bg-muted/20 p-4">
              {!resultMarkdown && !errorText && (
                <p className="text-sm leading-7 text-muted-foreground">{placeholder}</p>
              )}
              {errorText && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-700">
                  {errorText}
                </div>
              )}
              {resultMarkdown && (
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {resultMarkdown}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </section>

          <section className="min-h-[860px]">
            <GeometryLibrary title="图形库" />
          </section>
        </div>
      </div>
    </main>
  );
}
