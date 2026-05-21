from .._shared import *


class _ParseStandardTableMixin:
    def _parse_standard_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析标准markdown表格（使用|符号）
        
        Args:
            lines: 文件行列表
            
        Returns:
            解析后的表格数据
        """
        # 找到表格开始和结束位置
        table_start = -1
        table_end = len(lines)  # 默认到文件末尾
        
        for i, line in enumerate(lines):
            # 跳过标题行（以#开头）
            if line.strip().startswith('#'):
                continue
            
            # 检查是否是表格开始行（包含|）
            if '|' in line and table_start == -1:
                table_start = i
            # 检查是否是表格结束：连续2个非表格行（不包含|且不是空行）
            elif '|' not in line and '+' not in line and table_start != -1:
                # 空行不计入结束判断
                if line.strip() == '':
                    continue
                # 检查后续是否还有表格行
                has_more_table_rows = False
                for j in range(i + 1, min(i + 3, len(lines))):  # 检查后面3行
                    if '|' in lines[j]:
                        has_more_table_rows = True
                        break
                
                if not has_more_table_rows:
                    # 后面没有表格行了，表格结束
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
        
        # 检查是否是Excel导出的表格（第一行是标题，第二行是空白/分隔线，第三行是表头）
        is_excel_table = False
        if len(table_lines) >= 3:
            # 检查文件第一行是否包含".xlsx"（Excel导出的文件通常在第一行有.xlsx文件名）
            # 注意：这里检查的是原始文件的第一行，而不是表格的第一行
            if len(lines) > 0:
                file_first_line = lines[0].strip()
                if '.xlsx' in file_first_line or ('Unnamed' in file_first_line):
                    # 检测到Excel导出的表格
                    is_excel_table = True
        
        # V53.9改进：检测并处理两行表头的情况
        # 如果表格第一行包含"Unnamed"，说明是Excel导出的错误表头，需要跳过
        has_two_headers = False
        if len(table_lines) >= 4:
            first_row = self._parse_table_row(table_lines[0])
            # 检查第一行是否包含"Unnamed"或文件名（如"课件汇总"）
            if any('Unnamed' in cell for cell in first_row) or any('.xlsx' in cell for cell in first_row):
                # 检查第三行是否是实际的列名（不包含Unnamed）
                third_row = self._parse_table_row(table_lines[2])
                if not any('Unnamed' in cell for cell in third_row):
                    has_two_headers = True
                    print(f"   📝 V53.9检测到两行表头，跳过第一行错误表头")
        
        # 如果是Excel导出的表格，跳过原始文件的第2行（Excel导出的文件名），保留表头行
        if is_excel_table:
            # 重新提取表格行，跳过原始文件的第2行
            table_lines = []
            for i in range(table_start, table_end):
                # 跳过第2行（Excel导出的文件名）
                if i == 1:
                    continue
                line = lines[i]
                if '|' in line:
                    table_lines.append(line)
        
        # V53.9改进：如果检测到两行表头，跳过第一行（错误表头）和第二行（分隔线），使用第三行（实际列名）
        if has_two_headers and len(table_lines) >= 4:
            # 跳过第一行（错误表头）和第二行（分隔线），使用第三行作为表头
            header_line = table_lines[2]
            # 数据行从第四行开始
            data_lines = table_lines[3:] if len(table_lines) > 3 else []
            print(f"   📝 V53.9使用第三行作为表头: {header_line[:80]}...")
        else:
            # 解析表头
            header_line = table_lines[0]
            # 跳过分隔线（第二行），数据行从第三行开始
            data_lines = table_lines[1:] if len(table_lines) > 1 else []
        
        headers = self._parse_table_row(header_line)
        
        # 过滤掉分隔线行，并合并多行表格单元格
        filtered_data_lines = []
        for i in range(len(data_lines)):
            line = data_lines[i]
            
            # 检查是否是分隔线（包含:---或类似的模式）
            row = self._parse_table_row(line)
            is_separator = any(':---' in cell or '---' in cell for cell in row)
            if is_separator:
                continue
            
            # 检查这一行是否是表格行的延续（第一列为空）
            if len(row) > 0 and not row[0].strip() and filtered_data_lines:
                # 这是表格行的延续，合并到上一行
                filtered_data_lines[-1] += " " + line.strip()
            else:
                # 这是一个新的表格行
                filtered_data_lines.append(line.strip())
        
        data_lines = filtered_data_lines
        
        # 解析数据行
        data = []
        skipped_count = 0
        for line in data_lines:
            row = self._parse_table_row(line)
            
            # 检查是否是分隔线（包含:---或类似的模式）
            is_separator = any(':---' in cell or '---' in cell for cell in row)
            
            # 如果不是分隔线，且列数匹配，则添加到数据中
            if not is_separator:
                # 如果列数不匹配，尝试调整
                if len(row) != len(headers):
                    logger.debug(f"    [跳过] 列数不匹配: 期望{len(headers)}列, 实际{len(row)}列, 内容: {line[:80]}...")
                    skipped_count += 1
                    # 如果列数比表头多，且最后一列为空，则去掉最后一列
                    if len(row) > len(headers) and not row[-1].strip():
                        row = row[:-1]
                    # 如果列数还是不匹配，跳过这一行
                    if len(row) != len(headers):
                        continue
                
                # 如果列数匹配，则添加到数据中
                if len(row) == len(headers):
                    row_dict = {headers[i]: row[i] for i in range(len(headers))}
                    data.append(row_dict)
        
        if skipped_count > 0:
            logger.warning(f"    [V53.10修复] 跳过了{skipped_count}行列数不匹配的数据")
        
        return data
