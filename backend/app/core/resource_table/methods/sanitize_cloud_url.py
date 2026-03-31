from .._shared import *


class _SanitizeCloudUrlMixin:
    def _sanitize_cloud_url(self, url: str) -> str:
        """
        规范化云端URL，避免空格/中文路径导致urlopen报错
        """
        if not url:
            return ""

        parts = urlsplit(url.strip())
        sanitized_path = quote(unquote(parts.path), safe="/-_.~")
        sanitized_query = quote(unquote(parts.query), safe="=&-_.~")
        return urlunsplit(
            (parts.scheme, parts.netloc, sanitized_path, sanitized_query, parts.fragment)
        )
