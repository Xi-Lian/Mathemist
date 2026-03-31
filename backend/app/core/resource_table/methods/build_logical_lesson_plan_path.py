from .._shared import *


class _BuildLogicalLessonPlanPathMixin:
    def _build_logical_lesson_plan_path(self, row: Dict[str, str]) -> str:
        """
        为云端教案记录构建逻辑路径，兼容现有路径推断逻辑
        """
        board = row.get("板块", "")
        directory = row.get("目录", "").replace("\\", "/").strip("/")
        filename = row.get("文件名", "")
        parts = ["教案"]
        if board:
            parts.append(board)
        if directory:
            parts.append(directory)
        if filename:
            parts.append(filename)
        return "/".join(part for part in parts if part)
