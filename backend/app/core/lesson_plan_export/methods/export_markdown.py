from .._shared import *


class _ExportMarkdownMixin:
    def export_markdown(
        self,
        lesson_plan_content: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        导出为Markdown格式
        
        Args:
            lesson_plan_content: 教案内容（Markdown格式）
            filename: 文件名（不含扩展名）
            metadata: 元数据字典
        
        Returns:
            导出的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lesson_plan_{timestamp}"
        
        content = self._add_metadata_header(lesson_plan_content, metadata)
        filepath = self.output_dir / f"{filename}.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Markdown导出成功: {filepath}")
        return str(filepath)
