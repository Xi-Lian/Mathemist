from .._shared import *


class _ExportHtmlMixin:
    def export_html(
        self,
        lesson_plan_content: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        include_css: bool = True
    ) -> str:
        """
        导出为HTML格式
        
        Args:
            lesson_plan_content: 教案内容（Markdown格式）
            filename: 文件名（不含扩展名）
            metadata: 元数据字典
            include_css: 是否包含CSS样式
        
        Returns:
            导出的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lesson_plan_{timestamp}"
        
        html_content = markdown.markdown(
            lesson_plan_content,
            extensions=['extra', 'tables', 'toc']
        )
        html_doc = self._build_html_document(html_content, metadata, include_css)
        filepath = self.output_dir / f"{filename}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print(f"✅ HTML导出成功: {filepath}")
        return str(filepath)
