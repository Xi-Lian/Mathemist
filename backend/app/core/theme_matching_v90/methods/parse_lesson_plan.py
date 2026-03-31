from .._shared import *


class _ParseLessonPlanMixin:
    def _parse_lesson_plan(self, content: str) -> Dict[str, str]:
        """
        V11.4：增强教案结构解析的鲁棒性，支持表格格式
        
        改进：
        - 支持多种章节标题表述方式
        - 处理混合格式和无明确章节划分的情况
        - 提高解析的灵活性和准确性
        - 支持表格格式的内容（Markdown表格）
        - 合并"教学重点"和"教学难点"
        """
        structured = {
            "objectives": "",
            "key_points": "",
            "process": "",
            "full_content": content
        }
        
        if not content:
            return structured
        
        lines = content.split('\n')
        current_section = None
        section_content = []
        in_table = False
        table_buffer = []
        
        # V11.4：章节标题关键词列表（增强版）
        section_keywords = {
            "objectives": [
                "教学目标", "学习目标", "教学目的", "学习目的", "课程目标",
                "目标", "教学要求", "学习要求", "教学任务", "学习任务",
                "课程目标", "教学目标与核心素养"
            ],
            "key_points": [
                "教学重难点", "重难点", "重点难点", "教学重点", "教学难点",
                "重点", "难点", "关键", "核心", "重点内容", "难点内容",
                "教学重点：", "教学难点："
            ],
            "process": [
                "教学过程", "教学实施", "教学步骤", "教学环节", "教学活动",
                "过程", "实施", "步骤", "环节", "活动", "教学流程", "教学安排"
            ]
        }
        
        # V11.4：章节标题模式匹配函数（增强版）
        # V53.8改进：支持Markdown格式（**标题**）
        def match_section(line):
            line_lower = line.lower().strip()
            
            # V53.8改进：去除Markdown格式标记
            line_clean = line_lower.replace('**', '').replace('*', '').replace('#', '').strip()
            
            # 特殊处理：如果同时包含"教学重点"和"教学难点"，识别为key_points
            if "教学重点" in line_lower and "教学难点" in line_lower:
                return "key_points"
            
            # 特殊处理：单独的"教学重点"或"教学难点"
            if "教学重点" in line_lower or "教学难点" in line_lower:
                return "key_points"
            
            for section, keywords in section_keywords.items():
                for keyword in keywords:
                    # V53.8改进：同时检查原始行和去除Markdown格式后的行
                    if keyword in line_lower or keyword in line_clean:
                        # 检查是否是标题（通常标题会有特殊标记或格式）
                        # 简单判断：包含关键词且长度较短
                        if len(line_clean) < 30 or any(mark in line for mark in ["：", ":", "、", "\t", " " * 4, "**"]):
                            return section
            return None
        
        # V11.4：用于合并"教学重点"和"教学难点"的内容
        key_points_parts = []
        
        # V11.4：解析表格行的函数
        def parse_table_row(line):
            """解析Markdown表格行，提取单元格内容"""
            if '|' not in line:
                return None
            # 分割表格单元格
            cells = [cell.strip() for cell in line.split('|')]
            # 过滤空单元格
            cells = [cell for cell in cells if cell]
            return cells
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # V11.4：检测表格开始/结束
            if '|' in line_stripped:
                if not in_table:
                    in_table = True
                    table_buffer = []
                table_buffer.append(line_stripped)
                continue
            else:
                if in_table:
                    # 表格结束，处理表格内容
                    in_table = False
                    # 解析表格内容
                    for table_line in table_buffer:
                        cells = parse_table_row(table_line)
                        if cells and len(cells) >= 2:
                            # 检查第一列是否是章节标题
                            first_col = cells[0].lower()
                            matched = match_section(first_col)
                            if matched:
                                # 将表格内容分配给对应章节
                                content_text = ' '.join(cells[1:])
                                if matched == "key_points":
                                    key_points_parts.append(content_text)
                                else:
                                    if structured[matched]:
                                        structured[matched] += '\n' + content_text
                                    else:
                                        structured[matched] = content_text
                    table_buffer = []
            
            # 识别章节标题（非表格行）
            matched_section = match_section(line_stripped)
            if matched_section:
                # 保存当前章节内容
                if current_section and section_content:
                    content_text = '\n'.join(section_content)
                    if current_section == "key_points":
                        key_points_parts.append(content_text)
                    else:
                        structured[current_section] = content_text
                # 开始新章节
                current_section = matched_section
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # 保存最后一个章节
        if current_section and section_content:
            content_text = '\n'.join(section_content)
            if current_section == "key_points":
                key_points_parts.append(content_text)
            else:
                structured[current_section] = content_text
        
        # V11.4：合并所有key_points部分
        if key_points_parts:
            structured["key_points"] = '\n'.join(key_points_parts)
        
        # V10.0：处理无明确章节划分的情况
        if not any([structured["objectives"], structured["key_points"], structured["process"]]):
            # 整个内容作为教学过程
            structured["process"] = content
        
        # V10.0：处理章节内容不完整的情况
        if not structured["objectives"]:
            # 尝试从内容中提取目标相关内容
            objectives_patterns = ["目标", "要求", "任务"]
            objectives_content = []
            for line in lines:
                line_lower = line.lower()
                if any(pattern in line_lower for pattern in objectives_patterns):
                    objectives_content.append(line)
            if objectives_content:
                structured["objectives"] = '\n'.join(objectives_content)
        
        return structured
