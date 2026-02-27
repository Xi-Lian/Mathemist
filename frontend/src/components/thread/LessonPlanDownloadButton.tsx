import { useMemo, useState } from "react";
import { Download, LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { LessonPlanExportData } from "@/providers/Stream";

const MIME_TYPE_BY_FORMAT: Record<string, string> = {
  markdown: "text/markdown",
  html: "text/html",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

const EXTENSION_BY_FORMAT: Record<string, string> = {
  markdown: ".md",
  html: ".html",
  docx: ".docx",
};

function ensureFileExtension(filename: string, format: string): string {
  const ext = EXTENSION_BY_FORMAT[format];
  if (!ext) return filename;
  if (filename.toLowerCase().endsWith(ext)) return filename;
  return `${filename}${ext}`;
}

export function LessonPlanDownloadButton({
  exportData,
}: {
  exportData: LessonPlanExportData;
}) {
  const [downloading, setDownloading] = useState(false);

  const normalizedFormat = useMemo(
    () => exportData.format.trim().toLowerCase(),
    [exportData.format],
  );
  const buttonLabel = `下载教案 (${normalizedFormat.toUpperCase() || "FILE"})`;

  const handleDownload = () => {
    if (downloading) return;
    if (!exportData.content?.trim()) {
      toast.error("下载失败：文件内容为空");
      return;
    }
    if (!exportData.filename?.trim()) {
      toast.error("下载失败：缺少文件名");
      return;
    }
    if (normalizedFormat === "docx") {
      toast.error("DOCX 暂不支持前端直接下载");
      return;
    }

    setDownloading(true);
    try {
      const mimeType =
        MIME_TYPE_BY_FORMAT[normalizedFormat] ?? "application/octet-stream";
      const filename = ensureFileExtension(
        exportData.filename.trim(),
        normalizedFormat,
      );
      const content =
        mimeType.startsWith("text/")
          ? `\uFEFF${exportData.content}`
          : exportData.content;
      const blob = new Blob([content], {
        type: mimeType.startsWith("text/") ? `${mimeType};charset=utf-8` : mimeType,
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast.success("教案下载已开始");
    } catch (error) {
      console.error("Failed to download lesson plan", error);
      toast.error("下载失败，请重试");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Button
      type="button"
      onClick={handleDownload}
      disabled={downloading}
      className="mt-2 w-fit bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
    >
      {downloading ? (
        <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <Download className="mr-2 h-4 w-4" />
      )}
      {buttonLabel}
    </Button>
  );
}

