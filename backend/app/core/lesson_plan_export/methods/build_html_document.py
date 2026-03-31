from .._shared import *


class _BuildHtmlDocumentMixin:
    def _build_html_document(
        self,
        html_content: str,
        metadata: Optional[Dict[str, Any]],
        include_css: bool
    ) -> str:
        """
        构建完整的HTML文档
        
        Args:
            html_content: HTML内容
            metadata: 元数据字典
            include_css: 是否包含CSS
        
        Returns:
            完整的HTML文档
        """
        title = "教案"
        if metadata and 'topic' in metadata:
            title = metadata['topic']
        
        css = self._get_css() if include_css else ""
        meta_tags = ""
        if metadata:
            for key, value in metadata.items():
                meta_tags += f'<meta name="{key}" content="{value}">\n'
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {meta_tags}
    <title>{title}</title>
    {css}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
        return html
