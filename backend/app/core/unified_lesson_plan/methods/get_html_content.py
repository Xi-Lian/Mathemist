from .._shared import *


class _GetHtmlContentMixin:
    def _get_html_content(self, lesson_plan_content: str, metadata: Dict[str, Any]) -> str:
        """
        获取HTML格式的内容
        
        Args:
            lesson_plan_content: 教案内容
            metadata: 元数据
        
        Returns:
            HTML格式的内容
        """
        import markdown
        
        title = metadata.get("topic", "教案")
        html_content = markdown.markdown(
            lesson_plan_content,
            extensions=['extra', 'tables', 'toc']
        )
        
        meta_tags = ""
        for key, value in metadata.items():
            if value:
                meta_tags += f'<meta name="{key}" content="{value}">\n'
        
        css = self._get_html_css()
        
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
