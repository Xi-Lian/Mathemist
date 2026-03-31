from .._shared import *


class _ExportAllMixin:
    def export_all(
        self,
        lesson_plan_content: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        formats: Optional[list] = None
    ) -> Dict[str, str]:
        """
        导出为多种格式
        
        Args:
            lesson_plan_content: 教案内容（Markdown格式）
            filename: 文件名（不含扩展名）
            metadata: 元数据字典
            formats: 要导出的格式列表，默认为 ['markdown', 'html', 'docx']
        
        Returns:
            格式到文件路径的字典
        """
        if formats is None:
            formats = ['markdown', 'html', 'docx']
        
        results = {}
        for format_type in formats:
            try:
                if format_type == 'markdown':
                    results['markdown'] = self.export_markdown(
                        lesson_plan_content, filename, metadata
                    )
                elif format_type == 'html':
                    results['html'] = self.export_html(
                        lesson_plan_content, filename, metadata
                    )
                elif format_type == 'docx':
                    results['docx'] = self.export_docx(
                        lesson_plan_content, filename, metadata
                    )
                elif format_type == 'pdf':
                    results['pdf'] = self.export_pdf(
                        lesson_plan_content, filename, metadata
                    )
            except Exception as e:
                print(f"⚠️  导出{format_type}格式失败: {e}")
                results[format_type] = f"导出失败: {e}"
        
        return results
