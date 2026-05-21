from .._shared import *


class _ParseSyllabusTableMixin:
    def parse_syllabus_table(self) -> List[Dict[str, str]]:
        """
        解析教学大纲汇总表
        
        Returns:
            教学大纲资源列表
        """
        all_data = []
        
        # 1. 检查learning_resource目录下的教学大纲文件
        for md_file in self.learning_resource_path.glob('*教学大纲.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 尝试解析所有表格
                file_data = []
                
                # 先尝试标准表格格式（使用|符号）
                standard_data = self.parse_markdown_table(content)
                file_data.extend(standard_data)
                
                # 尝试解析特殊表格格式（使用+和|符号）
                lines = content.split('\n')
                special_data = self._parse_special_table(lines)
                file_data.extend(special_data)
                
                # 尝试解析空格分隔的表格
                space_data = self._parse_space_separated_table(lines)
                file_data.extend(space_data)
                
                # 如果没有找到任何表格，尝试解析包含章节和教学任务的行
                if not standard_data and not special_data and not space_data:
                    chapters = {}
                    current_chapter = ""
                    current_task = ""
                    general_content = ""
                    in_general_section = False
                    
                    for line in lines:
                        line = line.strip()
                        
                        # 检查是否是Markdown二级标题（如 ## 三角函数）
                        match = re.match(r'^##\s+(.+)', line)
                        if match:
                            # 如果已经在通用内容部分（【教学提示】等），停止收集章节
                            if in_general_section:
                                general_content += "\n" + line
                                continue
                            
                            # 保存上一条记录
                            if current_chapter and current_task:
                                chapters[current_chapter] = current_task.strip()
                            
                            # 开始新记录
                            current_chapter = match.group(1).strip()
                            current_task = ""
                            continue
                        
                        # 检查是否是通用内容部分（【教学提示】、【学业要求】等）
                        if line.startswith('【'):
                            in_general_section = True
                            section_title = line
                            general_content += line
                            continue
                        
                        # 如果在通用内容部分，尝试匹配章节特定内容
                        if in_general_section:
                            if line:
                                # 检查该行是否提到某个章节名称
                                matched_chapter = None
                                for chapter_name in chapters.keys():
                                    if chapter_name in line:
                                        matched_chapter = chapter_name
                                        break
                                
                                if matched_chapter:
                                    # 这是章节特定内容，添加到对应章节
                                    if chapters[matched_chapter]:
                                        chapters[matched_chapter] += "\n\n【" + section_title + "】\n" + line
                                    else:
                                        chapters[matched_chapter] = "【" + section_title + "】\n" + line
                                else:
                                    # 通用内容
                                    general_content += "\n" + line
                            continue
                        
                        # 跳过空行和一级标题
                        if not line or line.startswith('# '):
                            continue
                        
                        # 检查是否是章节行（以数字开头，如"3.1"）
                        if re.match(r'^\d+\.\d+', line):
                            # 保存上一条记录
                            if current_chapter and current_task:
                                chapters[current_chapter] = current_task.strip()
                            
                            # 开始新记录
                            current_chapter = line.split()[0]  # 提取章节号
                            current_task = line
                        
                        # 检查是否是任务行（以①、②等开头）
                        elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                            current_task += "\n" + line
                        
                        # 其他内容作为教学任务
                        elif current_chapter:
                            current_task += "\n" + line
                    
                    # 保存最后一条章节记录
                    if current_chapter:
                        chapters[current_chapter] = current_task.strip() if current_task else ""
                    
                    # 如果有通用内容且章节没有特定内容，将通用内容添加到章节
                    if general_content.strip():
                        for chapter_name in chapters:
                            if not chapters[chapter_name]:
                                chapters[chapter_name] = general_content.strip()
                    
                    # 转换为列表格式
                    for chapter_name, content in chapters.items():
                        file_data.append({
                            '章节': chapter_name,
                            '教学任务（教学内容）': content
                        })
                
                # 添加资源类型、源文件路径和标题
                for i, item in enumerate(file_data):
                    item['resource_type'] = 'syllabus'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    # 为教学大纲资源创建标题
                    chapter = item.get('章节', '')
                    task = item.get('教学任务（教学内容）', '')
                    title = f"{chapter} - {task[:30]}" if task else f"{chapter}" if chapter else f"教学大纲资源_{i+1}"
                    item['title'] = title
                    # 根据文件名确定板块
                    filename = md_file.name
                    if '函数' in filename:
                        item['board'] = '函数'
                    elif '几何' in filename:
                        item['board'] = '几何'
                    elif '概率' in filename or '统计' in filename:
                        item['board'] = '概率统计'
                    else:
                        item['board'] = '通用'
                
                all_data.extend(file_data)
                logger.info(f"解析教学大纲: {md_file.name}, 共{len(file_data)}条记录")
                
            except Exception as e:
                logger.error(f"解析教学大纲文件失败: {md_file}, 错误: {e}")
        
        # 2. 检查learning_resource/教学大纲目录下的文件
        syllabus_folder = self.learning_resource_path / '教学大纲'
        if syllabus_folder.exists():
            for md_file in syllabus_folder.rglob('*.md'):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试解析所有表格
                    file_data = []
                    
                    # 先尝试标准表格格式（使用|符号）
                    standard_data = self.parse_markdown_table(content)
                    file_data.extend(standard_data)
                    
                    # 尝试解析特殊表格格式（使用+和|符号）
                    lines = content.split('\n')
                    special_data = self._parse_special_table(lines)
                    file_data.extend(special_data)
                    
                    # 尝试解析空格分隔的表格
                    space_data = self._parse_space_separated_table(lines)
                    file_data.extend(space_data)
                    
                    # 如果没有找到任何表格，尝试解析包含章节和教学任务的行
                    if not standard_data and not special_data and not space_data:
                        chapters = {}
                        current_chapter = ""
                        current_task = ""
                        general_content = ""
                        in_general_section = False
                        
                        for line in lines:
                            line = line.strip()
                            
                            # 检查是否是Markdown二级标题（如 ## 三角函数）
                            match = re.match(r'^##\s+(.+)', line)
                            if match:
                                # 如果已经在通用内容部分（【教学提示】等），停止收集章节
                                if in_general_section:
                                    general_content += "\n" + line
                                    continue
                                
                                # 保存上一条记录
                                if current_chapter and current_task:
                                    chapters[current_chapter] = current_task.strip()
                                
                                # 开始新记录
                                current_chapter = match.group(1).strip()
                                current_task = ""
                                continue
                            
                            # 检查是否是通用内容部分（【教学提示】、【学业要求】等）
                            if line.startswith('【'):
                                in_general_section = True
                                section_title = line
                                general_content += line
                                continue
                            
                            # 如果在通用内容部分，尝试匹配章节特定内容
                            if in_general_section:
                                if line:
                                    # 检查该行是否提到某个章节名称
                                    matched_chapter = None
                                    for chapter_name in chapters.keys():
                                        if chapter_name in line:
                                            matched_chapter = chapter_name
                                            break
                                    
                                    if matched_chapter:
                                        # 这是章节特定内容，添加到对应章节
                                        if chapters[matched_chapter]:
                                            chapters[matched_chapter] += "\n\n【" + section_title + "】\n" + line
                                        else:
                                            chapters[matched_chapter] = "【" + section_title + "】\n" + line
                                    else:
                                        # 通用内容
                                        general_content += "\n" + line
                                continue
                            
                            # 跳过空行和一级标题
                            if not line or line.startswith('# '):
                                continue
                            
                            # 检查是否是章节行（以数字开头，如"3.1"）
                            if re.match(r'^\d+\.\d+', line):
                                # 保存上一条记录
                                if current_chapter and current_task:
                                    chapters[current_chapter] = current_task.strip()
                                
                                # 开始新记录
                                current_chapter = line.split()[0]  # 提取章节号
                                current_task = line
                            
                            # 检查是否是任务行（以①、②等开头）
                            elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                                current_task += "\n" + line
                            
                            # 其他内容作为教学任务
                            elif current_chapter:
                                current_task += "\n" + line
                        
                        # 保存最后一条章节记录
                        if current_chapter:
                            chapters[current_chapter] = current_task.strip() if current_task else ""
                        
                        # 如果有通用内容且章节没有特定内容，将通用内容添加到章节
                        if general_content.strip():
                            for chapter_name in chapters:
                                if not chapters[chapter_name]:
                                    chapters[chapter_name] = general_content.strip()
                        
                        # 转换为列表格式
                        for chapter_name, content in chapters.items():
                            file_data.append({
                                '章节': chapter_name,
                                '教学任务（教学内容）': content
                            })
                    
                    # 添加资源类型、源文件路径和标题
                    for i, item in enumerate(file_data):
                        item['resource_type'] = 'syllabus'
                        item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                        # 为教学大纲资源创建标题
                        chapter = item.get('章节', '')
                        task = item.get('教学任务（教学内容）', '')
                        title = f"{chapter} - {task[:30]}" if task else f"{chapter}" if chapter else f"教学大纲资源_{i+1}"
                        item['title'] = title
                    
                    all_data.extend(file_data)
                    logger.info(f"解析教学大纲: {md_file.name}, 共{len(file_data)}条记录")
                    
                except Exception as e:
                    logger.error(f"解析教学大纲文件失败: {md_file}, 错误: {e}")
        
        if not all_data:
            logger.warning("未找到教学大纲文件")
        
        logger.info(f"解析教学大纲完成，共{len(all_data)}条记录")
        return all_data
