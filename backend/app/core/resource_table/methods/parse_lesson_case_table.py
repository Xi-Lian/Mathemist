from .._shared import *
import pandas as pd


class _ParseLessonCaseTableMixin:
    def parse_lesson_case_table(self) -> List[Dict[str, str]]:
        """
        解析课例资源汇总表
        优先从云端汇总表获取，已上传云端的资源从云端下载，未上传的尝试本地读取

        Returns:
            课例资源列表
        """
        # 尝试从云端汇总表解析
        cloud_lesson_cases = self._parse_cloud_lesson_case_table()
        if cloud_lesson_cases:
            logger.info(f"从云端汇总表解析到{len(cloud_lesson_cases)}条课例资源")
            return cloud_lesson_cases

        # 如果没有云端汇总表，尝试从本地文件夹读取
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
                    # V45.1修复：为课例资源创建标题，优先使用"课程名称"字段
                    course_name = item.get('课程名称', '')
                    chapter = item.get('章节', '')
                    filename = item.get('视频文件名/网址', '')
                    
                    if course_name:
                        # 优先使用课程名称作为标题
                        title = course_name
                    else:
                        # 如果没有课程名称，再使用章节+文件名的组合
                        title_parts = []
                        if chapter:
                            title_parts.append(chapter)
                        if filename and not filename.startswith('http'):
                            title_parts.append(filename)
                        title = ' - '.join(title_parts) if title_parts else f"课例资源_{i+1}"
                    
                    item['title'] = title

                all_lesson_cases.extend(data)
                logger.info(f"解析课例视频汇总表: {md_file.name}, 共{len(data)}条记录")

            except Exception as e:
                logger.error(f"解析课例视频文件失败: {md_file}, 错误: {e}")

        logger.info(f"解析课例视频汇总表完成，共{len(all_lesson_cases)}条记录")
        return all_lesson_cases

    def _parse_cloud_lesson_case_table(self) -> List[Dict[str, str]]:
        """
        从云端汇总表解析课例资源

        Returns:
            课例资源列表
        """
        # 查找课例视频汇总表
        lesson_case_index_files = list(self.learning_resource_path.glob('*-课例视频.xlsx'))
        if not lesson_case_index_files:
            logger.warning("未找到课例视频汇总表")
            return []

        all_lesson_cases = []

        for index_file in lesson_case_index_files:
            try:
                df = pd.read_excel(index_file)
                logger.info(f"读取课例视频汇总表: {index_file.name}, 共{len(df)}条记录")

                for i, row in df.iterrows():
                    item = {}

                    # 遍历每一列
                    for col in df.columns:
                        if pd.notna(row[col]):
                            item[col] = str(row[col])
                        else:
                            item[col] = ''

                    # 添加资源类型和源文件路径
                    item['resource_type'] = 'lesson_case'
                    item['source_file'] = index_file.name

                    # V45.1修复：为课例资源创建标题，优先使用"课程名称"字段
                    course_name = item.get('课程名称', '')
                    chapter = item.get('章节', '')
                    filename = item.get('视频文件名/网址', '')
                    
                    if course_name:
                        # 优先使用课程名称作为标题
                        title = course_name
                    else:
                        # 如果没有课程名称，再使用章节+文件名的组合
                        title_parts = []
                        if chapter:
                            title_parts.append(chapter)
                        if filename and not filename.startswith('http'):
                            title_parts.append(filename)
                        title = ' - '.join(title_parts) if title_parts else f"课例资源_{i+1}"
                    
                    item['title'] = title

                    all_lesson_cases.append(item)
                    logger.info(f"解析云端课例: {chapter} - {filename}")

            except Exception as e:
                logger.error(f"解析课例视频汇总表失败: {index_file}, 错误: {e}")

        return all_lesson_cases
