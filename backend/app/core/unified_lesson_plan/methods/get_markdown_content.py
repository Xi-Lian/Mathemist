from .._shared import *


class _GetMarkdownContentMixin:
    def _get_markdown_content(self, lesson_plan_content: str, metadata: Dict[str, Any]) -> str:
        """
        获取Markdown格式的内容
        
        Args:
            lesson_plan_content: 教案内容
            metadata: 元数据
        
        Returns:
            Markdown格式的内容
        """
        # 添加元数据头部
        header_lines = ["---"]
        for key, value in metadata.items():
            if value:
                header_lines.append(f"{key}: {value}")
        header_lines.append(f"export_time: {datetime.now().isoformat()}")
        header_lines.append("---")
        header_lines.append("")
        
        return "\n".join(header_lines) + lesson_plan_content
