from .._shared import *


class _ParseMarkdownTableMixin:
    def parse_markdown_table(self, content: str) -> List[Dict[str, str]]:
        """
        解析markdown表格内容
        
        Args:
            content: markdown文件内容
            
        Returns:
            解析后的表格数据，每行是一个字典
        """
        lines = content.strip().split('\n')
        
        # 检查是否是特殊表格格式（使用+和-符号）
        if '+:' in content or '+---' in content:
            return self._parse_special_table(lines)
        
        # 标准markdown表格格式
        return self._parse_standard_table(lines)
