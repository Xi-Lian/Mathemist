from .._shared import *


class _BuildLessonPlanFallbackContentMixin:
    def _build_lesson_plan_fallback_content(
        self,
        row: Dict[str, str],
        logical_path: str,
        linked_row: Optional[Dict[str, str]],
        extracted_topics: List[str]
    ) -> str:
        """
        当云端Markdown不可用时，用索引元数据构建可检索摘要
        """
        parts = ["教案资源"]

        board = row.get("板块", "").strip()
        if board:
            parts.append(f"板块：{board}")

        directory = row.get("目录", "").strip()
        if directory:
            parts.append(f"目录：{directory}")

        filename = row.get("文件名", "").strip()
        if filename:
            parts.append(f"Markdown文件：{filename}")

        if extracted_topics:
            parts.append(f"知识点：{', '.join(dict.fromkeys(extracted_topics))}")

        if linked_row:
            original_name = linked_row.get("文件名", "").strip()
            original_url = linked_row.get("云端链接", "").strip()
            if original_name:
                parts.append(f"原文件：{original_name}")
            if original_url:
                parts.append(f"原文件链接：{original_url}")

        image_count = row.get("图片数量", "").strip()
        if image_count:
            parts.append(f"图片数量：{image_count}")

        remark = row.get("备注", "").strip()
        if remark:
            parts.append(f"备注：{remark}")

        full_path = row.get("完整路径", "").strip()
        if full_path:
            parts.append(f"完整路径：{full_path}")
        else:
            parts.append(f"逻辑路径：{logical_path}")

        parts.append("说明：云端Markdown正文缺失，当前使用索引摘要参与检索。")

        content = "\n".join(parts)

        # 添加额外的语义信息，从文件名和目录中提取更多关键词
        semantic_parts = []
        for text in [filename, directory, logical_path]:
            if text:
                semantic_parts.append(text)

        if semantic_parts:
            content += "\n" + " ".join(semantic_parts)

        return content
