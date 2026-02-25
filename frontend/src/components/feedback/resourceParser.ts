export interface ParsedResource {
  title: string;
  source: string;
  resourceId: string;
  resourceType: string;
  category: string;
}

const CATEGORY_TO_RESOURCE_TYPE: Record<string, string> = {
  习题资源: "exercise",
  教案资源: "lesson_plan",
  课件资源: "courseware",
  课例资源: "lesson_case",
  GGB资源: "ggb",
  教学大纲: "syllabus",
  可视化示例: "visualization",
};

function normalizeTitle(rawTitle: string): string {
  return rawTitle.replace(/^[^A-Za-z0-9\u4e00-\u9fa5]+/, "").trim();
}

function inferResourceType(category: string): string {
  return CATEGORY_TO_RESOURCE_TYPE[category] || "general";
}

function createResourceId(
  source: string,
  resourceType: string,
  normalizedTitle: string,
): string {
  return source || `${resourceType}:${normalizedTitle}`;
}

export function parseResourcesFromResponse(content: string): ParsedResource[] {
  if (!content) return [];

  const lines = content.split("\n");
  const resources: ParsedResource[] = [];
  const seen = new Set<string>();

  let currentCategory = "";
  let pendingTitle = "";

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    const categoryMatch = line.match(/^【(.+?)】$/);
    if (categoryMatch) {
      currentCategory = categoryMatch[1].trim();
      pendingTitle = "";
      continue;
    }

    if (!currentCategory) continue;

    if (
      line.startsWith("内容:") ||
      line.startsWith("相似度:") ||
      line.startsWith("=") ||
      line.startsWith("---") ||
      line.startsWith("#")
    ) {
      continue;
    }

    if (line.startsWith("文件路径:")) {
      const source = line.slice("文件路径:".length).trim();
      const normalizedTitle = normalizeTitle(pendingTitle || source || "未知资源");
      const resourceType = inferResourceType(currentCategory);
      const resourceId = createResourceId(source, resourceType, normalizedTitle);

      if (!seen.has(resourceId)) {
        seen.add(resourceId);
        resources.push({
          title: normalizedTitle,
          source,
          resourceId,
          resourceType,
          category: currentCategory,
        });
      }
      pendingTitle = "";
      continue;
    }

    pendingTitle = line;
  }

  return resources;
}
