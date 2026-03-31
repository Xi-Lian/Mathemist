from .._shared import *


class _ParseLessonCaseTableMixin:
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
                
                # 添加资源类型、文件路径和标题
                for i, item in enumerate(data):
                    item['resource_type'] = 'lesson_case'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    # 为课例资源创建标题
                    chapter = item.get('章节', '')
                    filename = item.get('视频文件名/网址', '')
                    analysis = item.get('分析', '')
                    title_parts = []
                    if chapter:
                        title_parts.append(chapter)
                    if filename and not filename.startswith('http'):
                        title_parts.append(filename)
                    if analysis:
                        title_parts.append(analysis[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课例资源_{i+1}"
                    item['title'] = title
                
                all_lesson_cases.extend(data)
                logger.info(f"解析课例视频汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课例视频文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析课例视频汇总表完成，共{len(all_lesson_cases)}条记录")
        return all_lesson_cases
