from .._shared import *


class _ExtractSectionMixin:
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        从内容中提取特定章节
        
        Args:
            content: 完整内容
            section_name: 章节名称
        
        Returns:
            提取的章节内容
        """
        import re
        pattern = rf"\*\*{re.escape(section_name)}\*\*\s*\n(.*?)(?=\n\*\*|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
