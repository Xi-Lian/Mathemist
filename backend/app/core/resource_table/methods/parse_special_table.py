from .._shared import *


class _ParseSpecialTableMixin:
    def _parse_special_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析特殊表格格式（使用+和|符号）
        
        Args:
            lines: 文件行列表
            
        Returns:
            解析后的表格数据
        """
        # 找到表格开始和结束位置
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            # 跳过标题行（以#开头）
            if line.strip().startswith('#'):
                continue
            
            # 检查是否是表格开始行（包含|）
            if '|' in line and table_start == -1:
                table_start = i
            # 检查是否是表格结束行（不包含|且不包含+，且不是空行）
            elif '|' not in line and '+' not in line and table_start != -1:
                # 检查是否是空行（只有空格或完全为空）
                if line.strip() == '':
                    # 空行，继续解析
                    continue
                # 非空行且不包含|或+，表格结束
                table_end = i
                break
        
        if table_start == -1:
            return []
        
        if table_end == -1:
            table_end = len(lines)
        
        # 提取表格行（只包含|的行）
        table_lines = []
        for i in range(table_start, table_end):
            line = lines[i]
            if '|' in line:
                table_lines.append(line)
        
        # 检查是否是Excel导出的表格（第一行是标题，第二行是分隔线，第三行是表头）
        if len(table_lines) >= 3:
            first_line = table_lines[0].strip()
            # 检查第一行是否包含".xlsx"或看起来像Excel标题
            if '.xlsx' in first_line or ('Unnamed' in first_line):
                # 跳过Excel标题行和分隔线，从第三行开始解析
                table_lines = table_lines[2:]
        
        # 解析表头（第一行）
        header_line = table_lines[0]
        headers = self._parse_special_table_row(header_line)
        
        # 跳过分隔线（第二行）
        data_lines = table_lines[1:] if len(table_lines) > 1 else []
        
        # 解析数据行（处理多行单元格）
        data = []
        current_record = {}
        
        for line in data_lines:
            row = self._parse_special_table_row(line)
            
            # 跳过分隔行（只包含-）
            if len(row) > 1 and all(c in '- ' for c in row[1].strip()):
                continue
            
            # 检查是否是新的记录行（第一列不为空）
            if len(row) > 0 and row[0].strip():
                # 保存上一条记录
                if current_record:
                    data.append(current_record)
                
                # 开始新记录
                if len(row) == len(headers):
                    current_record = {headers[i]: row[i] for i in range(len(headers))}
            # 检查是否是续行（第一列为空，第二列不为空）
            elif len(row) > 1 and not row[0].strip() and row[1].strip():
                if current_record and len(headers) > 1:
                    current_record[headers[1]] += "\n" + row[1].strip()
        
        # 保存最后一条记录
        if current_record:
            data.append(current_record)
        
        return data
