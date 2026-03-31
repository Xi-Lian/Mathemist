from .._shared import *


class _ExportPdfMixin:
    def export_pdf(
        self,
        lesson_plan_content: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        导出为PDF格式
        
        Args:
            lesson_plan_content: 教案内容（Markdown格式）
            filename: 文件名（不含扩展名）
            metadata: 元数据字典
        
        Returns:
            导出的文件路径
        """
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError("请安装weasyprint库: pip install weasyprint")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lesson_plan_{timestamp}"
        
        html_content = markdown.markdown(
            lesson_plan_content,
            extensions=['extra', 'tables', 'toc']
        )
        html_doc = self._build_html_document(html_content, metadata, include_css=True)
        filepath = self.output_dir / f"{filename}.pdf"
        HTML(string=html_doc).write_pdf(str(filepath))
        
        print(f"✅ PDF导出成功: {filepath}")
        return str(filepath)
