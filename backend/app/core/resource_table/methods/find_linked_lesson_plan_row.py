from .._shared import *


class _FindLinkedLessonPlanRowMixin:
    def _find_linked_lesson_plan_row(
        self,
        row: Dict[str, str],
        rows_by_path: Dict[str, Dict[str, str]],
        rows_by_name: Dict[str, List[Dict[str, str]]]
    ) -> Optional[Dict[str, str]]:
        """
        为Markdown记录查找关联的原始教案文件
        """
        linked_filename = row.get("关联文件", "").strip()
        logical_path = self._build_logical_lesson_plan_path(row)

        if linked_filename:
            linked_logical_path = "/".join(logical_path.split("/")[:-1] + [linked_filename])
            linked_row = rows_by_path.get(linked_logical_path.lower())
            if linked_row:
                return linked_row

        # 回退策略：同目录下根据去扩展名匹配doc/docx/pdf原文件
        stem_key = self._normalize_filename_key(row.get("文件名", ""))
        directory = row.get("目录", "").replace("\\", "/").strip("/").lower()
        candidates = rows_by_name.get(stem_key, [])
        preferred_exts = {".doc", ".docx", "doc", "docx", ".pdf", "pdf"}
        for candidate in candidates:
            candidate_ext = candidate.get("扩展名", "").lower()
            candidate_dir = candidate.get("目录", "").replace("\\", "/").strip("/").lower()
            if candidate_dir == directory and candidate_ext in preferred_exts:
                return candidate

        return None
