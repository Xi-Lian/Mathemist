"""
资源汇总表解析模块
用于解析learning_resource文件夹中的markdown表格数据
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceTableParser:
    """资源汇总表解析器"""
    
    def __init__(self, learning_resource_path: str):
        """
        初始化解析器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        # 确保learning_resource_path是绝对路径
        self.learning_resource_path = Path(learning_resource_path).resolve()
        
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
        
        # 解析表头
        header_line = table_lines[0]
        headers = self._parse_table_row(header_line)
        
        # 跳过分隔线（第二行）
        data_lines = table_lines[1:] if len(table_lines) > 1 else []
        
        # 解析数据行
        data = []
        for line in data_lines:
            row = self._parse_table_row(line)
            
            # 检查是否是分隔线（包含:---或类似的模式）
            is_separator = any(':---' in cell or '---' in cell for cell in row)
            
            # 如果不是分隔线，且列数匹配，则添加到数据中
            if not is_separator and len(row) == len(headers):
                row_dict = {headers[i]: row[i] for i in range(len(headers))}
                data.append(row_dict)
        
        return data
    
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
    
    def _parse_table_row(self, line: str) -> List[str]:
        """
        解析表格行
        
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
        
        # 分割单元格
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def parse_ggb_table(self) -> List[Dict[str, str]]:
        """
        解析GGB资源汇总表
        
        Returns:
            GGB资源列表
        """
        ggb_file = self.learning_resource_path / 'ggb' / 'ggb信息.md'
        
        if not ggb_file.exists():
            logger.warning(f"GGB汇总表不存在: {ggb_file}")
            return []
        
        with open(ggb_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = self.parse_markdown_table(content)
        
        # 添加资源类型
        for item in data:
            item['resource_type'] = 'ggb'
        
        logger.info(f"解析GGB汇总表，共{len(data)}条记录")
        return data
    
    def parse_syllabus_table(self) -> List[Dict[str, str]]:
        """
        解析教学大纲汇总表
        
        Returns:
            教学大纲资源列表
        """
        syllabus_file = self.learning_resource_path / '教学大纲' / '函数教学大纲.md'
        
        if not syllabus_file.exists():
            logger.warning(f"教学大纲汇总表不存在: {syllabus_file}")
            return []
        
        with open(syllabus_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析所有表格
        all_data = []
        
        # 先尝试标准表格格式（使用|符号）
        standard_data = self.parse_markdown_table(content)
        all_data.extend(standard_data)
        
        # 尝试解析特殊表格格式（使用+和|符号）
        lines = content.split('\n')
        special_data = self._parse_special_table(lines)
        all_data.extend(special_data)
        
        # 尝试解析空格分隔的表格
        space_data = self._parse_space_separated_table(lines)
        all_data.extend(space_data)
        
        # 如果没有找到任何表格，尝试解析包含章节和教学任务的行
        if not standard_data and not special_data and not space_data:
            current_chapter = ""
            current_task = ""
            
            for line in lines:
                line = line.strip()
                
                # 跳过空行和标题
                if not line or line.startswith('#'):
                    continue
                
                # 检查是否是章节行（以数字开头，如"3.1"）
                if re.match(r'^\d+\.\d+', line):
                    # 保存上一条记录
                    if current_chapter and current_task:
                        all_data.append({
                            '章节': current_chapter,
                            '教学任务（教学内容）': current_task
                        })
                    
                    # 开始新记录
                    current_chapter = line.split()[0]  # 提取章节号
                    current_task = line
                
                # 检查是否是任务行（以①、②等开头）
                elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                    current_task += "\n" + line
            
            # 保存最后一条记录
            if current_chapter and current_task:
                all_data.append({
                    '章节': current_chapter,
                    '教学任务（教学内容）': current_task
                })
        
        # 添加资源类型
        for item in all_data:
            item['resource_type'] = 'syllabus'
        
        logger.info(f"解析教学大纲汇总表，共{len(all_data)}条记录")
        return all_data
    
    def parse_exercise_tables(self) -> List[Dict[str, str]]:
        """
        解析习题资源汇总表
        
        Returns:
            习题资源列表
        """
        exercise_folder = self.learning_resource_path / '习题'
        
        if not exercise_folder.exists():
            logger.warning(f"习题文件夹不存在: {exercise_folder}")
            return []
        
        all_exercises = []
        
        # 遍历习题文件夹中的所有.md文件
        for md_file in exercise_folder.rglob('*.md'):
            # 跳过目录文件
            if md_file.name in ['题目目录.md', '答案目录.md']:
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型和文件路径
                for item in data:
                    item['resource_type'] = 'exercise'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                
                all_exercises.extend(data)
                logger.info(f"解析习题汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析习题文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析习题汇总表完成，共{len(all_exercises)}条记录")
        return all_exercises
    
    def parse_lesson_plan_tables(self) -> List[Dict[str, str]]:
        """
        解析教案资源汇总表
        
        Returns:
            教案资源列表
        """
        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if not lesson_plan_folder.exists():
            logger.warning(f"教案文件夹不存在: {lesson_plan_folder}")
            return []
        
        all_lesson_plans = []
        
        # 遍历教案文件夹中的所有.md文件
        for md_file in lesson_plan_folder.rglob('*.md'):
            # 跳过理论卡片和共性整合文档
            if md_file.name in ['优秀教案共性整合（最终版）.md']:
                continue
            
            # 检查是否是理论卡片
            if '理论卡片' in md_file.name:
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含表格
                if '|' not in content:
                    # 如果没有表格，创建一个简单的记录
                    item = {
                        'resource_type': 'lesson_plan',
                        'source_file': str(md_file.relative_to(self.learning_resource_path)),
                        'title': md_file.stem,
                        'content': content[:500]  # 只取前500个字符作为预览
                    }
                    all_lesson_plans.append(item)
                else:
                    data = self.parse_markdown_table(content)
                    
                    # 添加资源类型和文件路径
                    for item in data:
                        item['resource_type'] = 'lesson_plan'
                        item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    
                    all_lesson_plans.extend(data)
                
                logger.info(f"解析教案汇总表: {md_file.name}")
                
            except Exception as e:
                logger.error(f"解析教案文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析教案汇总表完成，共{len(all_lesson_plans)}条记录")
        return all_lesson_plans
    
    def parse_theory_cards(self) -> List[Dict[str, str]]:
        """
        解析理论卡片
        
        Returns:
            理论卡片列表
        """
        theory_cards = []
        
        # 在理论卡片文件夹中查找理论卡片
        theory_folder = self.learning_resource_path / '理论卡片'
        
        if theory_folder.exists():
            for md_file in theory_folder.rglob('*.md'):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    item = {
                        'resource_type': 'theory',
                        'source_file': str(md_file.relative_to(self.learning_resource_path)),
                        'title': md_file.stem,
                        'content': content
                    }
                    theory_cards.append(item)
                    
                    logger.info(f"解析理论卡片: {md_file.name}")
                    
                except Exception as e:
                    logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 在教案文件夹中查找理论卡片（向后兼容）
        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if lesson_plan_folder.exists():
            for md_file in lesson_plan_folder.rglob('*.md'):
                if '理论卡片' in md_file.name:
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        item = {
                            'resource_type': 'theory',
                            'source_file': str(md_file.relative_to(self.learning_resource_path)),
                            'title': md_file.stem,
                            'content': content
                        }
                        theory_cards.append(item)
                        
                        logger.info(f"解析理论卡片: {md_file.name}")
                        
                    except Exception as e:
                        logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 解析优秀教案共性整合文档
        theory_file = lesson_plan_folder / '优秀教案共性整合（最终版）.md'
        if theory_file.exists():
            try:
                with open(theory_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                item = {
                    'resource_type': 'theory',
                    'source_file': str(theory_file.relative_to(self.learning_resource_path)),
                    'title': theory_file.stem,
                    'content': content
                }
                theory_cards.append(item)
                
                logger.info(f"解析优秀教案共性整合文档")
                
            except Exception as e:
                logger.error(f"解析优秀教案共性整合文档失败: {e}")
        
        logger.info(f"解析理论卡片完成，共{len(theory_cards)}条记录")
        return theory_cards
    
    def parse_courseware_table(self) -> List[Dict[str, str]]:
        """
        解析课件资源汇总表
        
        Returns:
            课件资源列表
        """
        courseware_folder = self.learning_resource_path / '课件'
        
        if not courseware_folder.exists():
            logger.warning(f"课件文件夹不存在: {courseware_folder}")
            return []
        
        all_courseware = []
        
        # 遍历课件文件夹中的所有.md文件
        for md_file in courseware_folder.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型和文件路径
                for item in data:
                    item['resource_type'] = 'courseware'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                
                all_courseware.extend(data)
                logger.info(f"解析课件汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课件文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析课件汇总表完成，共{len(all_courseware)}条记录")
        return all_courseware
    
    def parse_lesson_case_table(self) -> List[Dict[str, str]]:
        """
        解析课例资源汇总表
        
        Returns:
            课例资源列表
        """
        lesson_case_folder = self.learning_resource_path / '课例视频'
        
        if not lesson_case_folder.exists():
            logger.warning(f"课例视频文件夹不存在: {lesson_case_folder}")
            return []
        
        all_lesson_cases = []
        
        # 遍历课例视频文件夹中的所有.md文件
        for md_file in lesson_case_folder.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型和文件路径
                for item in data:
                    item['resource_type'] = 'lesson_case'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                
                all_lesson_cases.extend(data)
                logger.info(f"解析课例视频汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课例视频文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析课例视频汇总表完成，共{len(all_lesson_cases)}条记录")
        return all_lesson_cases
    
    def parse_all_tables(self) -> Dict[str, List[Dict[str, str]]]:
        """
        解析所有资源汇总表
        
        Returns:
            所有资源的字典，按类型分组
        """
        logger.info("开始解析所有资源汇总表...")
        
        all_resources = {
            'ggb': self.parse_ggb_table(),
            'syllabus': self.parse_syllabus_table(),
            'exercise': self.parse_exercise_tables(),
            'lesson_plan': self.parse_lesson_plan_tables(),
            'theory': self.parse_theory_cards(),
            'courseware': self.parse_courseware_table(),
            'lesson_case': self.parse_lesson_case_table()
        }
        
        total_count = sum(len(resources) for resources in all_resources.values())
        logger.info(f"解析完成，共{total_count}条记录")
        
        return all_resources
    
    def format_resource_for_search(self, resource: Dict[str, str]) -> str:
        """
        将资源格式化为用于搜索的文本
        
        Args:
            resource: 资源字典
            
        Returns:
            格式化后的文本
        """
        resource_type = resource.get('resource_type', '')
        
        if resource_type == 'ggb':
            return f"章节：{resource.get('章节', '')}，教学用途：{resource.get('教学用途', '')}"
        
        elif resource_type == 'syllabus':
            return f"章节：{resource.get('章节', '')}，教学任务：{resource.get('教学任务（教学内容）', '')}"
        
        elif resource_type == 'exercise':
            # 习题资源特殊处理
            question = resource.get('题干', '')
            filename = resource.get('题目文件名', '')
            
            # 如果有文件名，说明是图片题目
            if filename:
                return f"题目类型：{resource.get('题目类型', '')}，题目描述：{question}，知识点：{resource.get('知识点标签', '')}"
            else:
                # 文字题目，显示完整题目
                return f"题目类型：{resource.get('题目类型', '')}，题目：{question}，知识点：{resource.get('知识点标签', '')}"
        
        elif resource_type == 'lesson_plan':
            return f"标题：{resource.get('title', '')}，内容：{resource.get('content', '')}"
        
        elif resource_type == 'theory':
            return f"标题：{resource.get('title', '')}，内容：{resource.get('content', '')}"
        
        elif resource_type == 'courseware':
            # 课件资源
            content = resource.get('内容', '')
            filename = resource.get('文件名', '')
            usage = resource.get('教学用途', '')
            return f"内容：{content}，文件名：{filename}，教学用途：{usage}"
        
        elif resource_type == 'lesson_case':
            # 课例资源
            chapter = resource.get('章节', '')
            filename = resource.get('视频文件名/网址', '')
            analysis = resource.get('分析', '')
            textbook = resource.get('教材', '')
            
            # 构建描述，优先使用分析内容，如果为空则使用章节和文件名
            description_parts = []
            
            # 添加资源类型关键词
            description_parts.append("课例")
            description_parts.append("教学视频")
            description_parts.append("课堂实录")
            
            if textbook:
                description_parts.append(f"教材：{textbook}")
            
            if chapter:
                description_parts.append(f"章节：{chapter}")
            
            # 尝试从文件名中提取知识点信息
            if filename and not filename.startswith('http'):
                # 从文件名中提取关键信息
                topic_info = self._extract_topic_from_filename(filename)
                if topic_info:
                    description_parts.append(f"知识点：{topic_info}")
            
            if analysis and analysis.strip():
                description_parts.append(f"分析：{analysis}")
            elif filename:
                # 如果分析为空，从文件名中提取关键信息
                description_parts.append(f"视频：{filename}")
            
            return "，".join(description_parts)
        
        else:
            return str(resource)
    
    def _extract_topic_from_filename(self, filename: str) -> str:
        """
        从课例文件名中提取知识点信息
        
        Args:
            filename: 文件名，如 "4.2.1指数函数的概念.mp4"
            
        Returns:
            提取的知识点信息
        """
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 移除常见的标记
        name = re.sub(r'【.*?】', '', name)  # 移除【单调性】等标记
        name = re.sub(r'\(.*?\)', '', name)  # 移除括号内容
        name = re.sub(r'\（.*?\）', '', name)  # 移除中文括号内容
        
        # 提取数字编号后的内容（如 "4.2.1指数函数的概念" -> "指数函数的概念"）
        match = re.search(r'^[\d\.]+\s*(.+)$', name)
        if match:
            return match.group(1).strip()
        
        # 如果没有数字编号，直接返回文件名
        return name
    
    def get_resource_filename(self, resource: Dict[str, str]) -> Optional[str]:
        """
        获取资源的文件名
        
        Args:
            resource: 资源字典
            
        Returns:
            文件名，如果没有则返回None
        """
        resource_type = resource.get('resource_type', '')
        
        if resource_type == 'ggb':
            return resource.get('ggb文件名')
        
        elif resource_type == 'exercise':
            return resource.get('题目文件名')
        
        elif resource_type in ['lesson_plan', 'theory']:
            return resource.get('source_file')
        
        elif resource_type == 'courseware':
            return resource.get('文件名')
        
        elif resource_type == 'lesson_case':
            return resource.get('视频文件名/网址')
        
        return None