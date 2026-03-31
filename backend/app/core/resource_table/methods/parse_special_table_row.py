from .._shared import *


class _ParseSpecialTableRowMixin:
    def _parse_special_table_row(self, line: str) -> List[str]:
        """
        解析特殊表格行（使用|作为分隔符）
        
        Args:
            line: 表格行内容
            
        Returns:
            解析后的单元格列表
        """
        # 移除首尾的|
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # 分割单元格（使用|作为分隔符）
        cells = [cell.strip() for cell in line.split('|')]
        return cells
