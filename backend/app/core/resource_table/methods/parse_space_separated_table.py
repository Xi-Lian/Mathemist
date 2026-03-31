from .._shared import *


class _ParseSpaceSeparatedTableMixin:
    def _parse_space_separated_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析空格分隔的表格
        
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
            
            # 检查是否是分隔线（只包含-和空格）
            if line.strip().startswith('-') and all(c in '- ' for c in line.strip()):
                # 分隔线的下一行应该是表头
                if i + 1 < len(lines) and table_start == -1:
                    table_start = i + 1
            # 检查是否是表格结束行（新标题）
            elif line.strip().startswith('#') and table_start != -1:
                table_end = i
                break
        
        if table_start == -1:
            return []
        
        if table_end == -1:
            table_end = len(lines)
        
        # 提取表格行
        table_lines = lines[table_start:table_end]
        
        # 解析表头（第一行）
        header_line = table_lines[0].strip()
        headers = [h.strip() for h in header_line.split()]
        
        # 跳过分隔线（第二行）
        data_lines = table_lines[2:] if len(table_lines) > 2 else []
        
        # 解析数据行
        data = []
        current_record = {}
        
        for line in data_lines:
            line = line.strip()
            
            # 跳过空行和分隔线
            if not line or (line.startswith('-') and all(c in '- ' for c in line)):
                continue
            
            # 检查是否是章节行（以数字开头，如"3.1"）
            if re.match(r'^\d+\.\d+', line):
                # 保存上一条记录
                if current_record:
                    data.append(current_record)
                
                # 开始新记录
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    current_record = {
                        '章节': parts[0],
                        '教学任务（教学内容）': parts[1]
                    }
                else:
                    current_record = {
                        '章节': parts[0],
                        '教学任务（教学内容）': ''
                    }
            # 检查是否是任务行（以①、②等开头）
            elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                if current_record:
                    current_record['教学任务（教学内容）'] += "\n" + line
        
        # 保存最后一条记录
        if current_record:
            data.append(current_record)
        
        return data
