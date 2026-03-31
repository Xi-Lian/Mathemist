from .._shared import *


class _ParseSyllabusTableMixin:
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
        
        # 添加资源类型、源文件路径和标题
        for i, item in enumerate(all_data):
            item['resource_type'] = 'syllabus'
            item['source_file'] = str(syllabus_file.relative_to(self.learning_resource_path))
            # 为教学大纲资源创建标题
            chapter = item.get('章节', '')
            task = item.get('教学任务（教学内容）', '')
            title = f"{chapter} - {task[:30]}" if task else f"{chapter}" if chapter else f"教学大纲资源_{i+1}"
            item['title'] = title
        
        logger.info(f"解析教学大纲汇总表，共{len(all_data)}条记录")
        return all_data
