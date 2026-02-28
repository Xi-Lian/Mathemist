import { useMemo, useState } from "react";
import { Download, LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { LessonPlanExportData } from "@/providers/Stream";

const MIME_TYPE_BY_FORMAT: Record<string, string> = {
  markdown: "text/markdown",
  html: "text/html",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pdf: "application/pdf",
  zip: "application/zip",
};

const EXTENSION_BY_FORMAT: Record<string, string> = {
  markdown: ".md",
  html: ".html",
  docx: ".docx",
  pdf: ".pdf",
  zip: ".zip",
};

function ensureFileExtension(filename: string, format: string): string {
  const ext = EXTENSION_BY_FORMAT[format];
  if (!ext) return filename;
  if (filename.toLowerCase().endsWith(ext)) return filename;
  return `${filename}${ext}`;
}

function decodeBase64ToUint8Array(base64Content: string): Uint8Array {
  const normalized = base64Content.replace(/\s/g, "");
  const binary = atob(normalized);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
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

    setDownloading(true);
    try {
      const mimeType =
        exportData.mime_type?.trim() ||
        MIME_TYPE_BY_FORMAT[normalizedFormat] ||
        "application/octet-stream";
      const filename = ensureFileExtension(
        exportData.filename.trim(),
        normalizedFormat,
      );
      const normalizedEncoding = exportData.encoding?.trim().toLowerCase();
      const blobPart =
        normalizedEncoding === "base64"
          ? decodeBase64ToUint8Array(exportData.content)
          : mimeType.startsWith("text/")
            ? `\uFEFF${exportData.content}`
            : exportData.content;
      const blob = new Blob([blobPart], {
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
