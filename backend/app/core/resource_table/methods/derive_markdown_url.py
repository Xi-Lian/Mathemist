from .._shared import *


class _DeriveMarkdownUrlMixin:
    def _derive_markdown_url(self, markdown_filename: str, linked_row: Optional[Dict[str, str]]) -> str:
        """
        当Markdown行缺少云端链接时，根据原文件链接推导Markdown链接
        """
        if not linked_row:
            return ""

        original_url = linked_row.get("云端链接", "").strip()
        if not original_url:
            return ""

        parts = urlsplit(original_url)
        path = parts.path
        if "." not in path.rsplit("/", 1)[-1]:
            return ""

        new_path = path.rsplit(".", 1)[0] + ".md"

        return self._sanitize_cloud_url(
            urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))
        )
