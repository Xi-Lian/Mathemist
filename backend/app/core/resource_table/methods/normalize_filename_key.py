from .._shared import *


class _NormalizeFilenameKeyMixin:
    def _normalize_filename_key(self, filename: str) -> str:
        """
        规范化文件名，便于关联md与原文件
        """
        return Path((filename or "").strip()).stem.lower()
