from .._shared import *


class _ParseCoursewareTableMixin:
    def parse_courseware_table(self) -> List[Dict[str, str]]:
        """
        解析课件资源汇总表
        优先从云端汇总表获取，已上传云端的资源从云端下载，未上传的尝试本地读取

        Returns:
            课件资源列表
        """
        # 尝试从云端汇总表解析
        cloud_courseware = self._parse_cloud_courseware_table()
        if cloud_courseware:
            logger.info(f"从云端汇总表解析到{len(cloud_courseware)}条课件资源")
            return cloud_courseware

        # 如果没有云端汇总表，尝试从本地文件夹读取
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

                # 添加资源类型、文件路径和标题
                for i, item in enumerate(data):
                    item['resource_type'] = 'courseware'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    # 为课件资源创建标题
                    content_text = item.get('内容', '')
                    filename = item.get('文件名', '')
                    title_parts = []
                    if filename:
                        title_parts.append(filename)
                    if content_text:
                        title_parts.append(content_text[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课件资源_{i+1}"
                    item['title'] = title

                all_courseware.extend(data)
                logger.info(f"解析课件汇总表: {md_file.name}, 共{len(data)}条记录")

            except Exception as e:
                logger.error(f"解析课件文件失败: {md_file}, 错误: {e}")

        # 遍历课件文件夹中的所有.xlsx文件
        for xlsx_file in courseware_folder.rglob('*.xlsx'):
            try:
                import pandas as pd

                df = pd.read_excel(xlsx_file)
                data = []

                # 遍历DataFrame的每一行
                for i, row in df.iterrows():
                    item = {}
                    # 遍历每一列
                    for col in df.columns:
                        if pd.notna(row[col]):
                            item[col] = str(row[col])
                        else:
                            item[col] = ''

                    # 添加资源类型、文件路径和标题
                    item['resource_type'] = 'courseware'
                    item['source_file'] = str(xlsx_file.relative_to(self.learning_resource_path))
                    # 为课件资源创建标题
                    content_text = item.get('内容', '')
                    filename = item.get('文件名', '')
                    title_parts = []
                    if filename:
                        title_parts.append(filename)
                    if content_text:
                        title_parts.append(content_text[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课件资源_{i+1}"
                    item['title'] = title

                    data.append(item)

                all_courseware.extend(data)
                logger.info(f"解析课件汇总表(xlsx): {xlsx_file.name}, 共{len(data)}条记录")

            except Exception as e:
                logger.error(f"解析课件文件失败: {xlsx_file}, 错误: {e}")

        logger.info(f"解析课件汇总表完成，共{len(all_courseware)}条记录")
        return all_courseware

    def _parse_cloud_courseware_table(self) -> List[Dict[str, str]]:
        """
        从云端汇总表解析课件资源

        Returns:
            课件资源列表
        """
        try:
            import pandas as pd
        except ImportError:
            logger.warning("未安装pandas，跳过云端课件解析")
            return []

        # 查找课件汇总表
        courseware_index_files = list(self.learning_resource_path.glob('*-课件汇总.xlsx'))
        if not courseware_index_files:
            logger.warning("未找到课件汇总表")
            return []

        all_courseware = []

        for index_file in courseware_index_files:
            try:
                df = pd.read_excel(index_file)
                logger.info(f"读取课件汇总表: {index_file.name}, 共{len(df)}条记录")

                for i, row in df.iterrows():
                    item = {}

                    # 遍历每一列
                    for col in df.columns:
                        if pd.notna(row[col]):
                            item[col] = str(row[col])
                        else:
                            item[col] = ''

                    # 添加资源类型和源文件路径
                    item['resource_type'] = 'courseware'
                    item['source_file'] = index_file.name

                    # 为课件资源创建标题
                    content_text = item.get('内容', '')
                    filename = item.get('文件名', '')
                    title_parts = []
                    if filename:
                        title_parts.append(filename)
                    if content_text:
                        title_parts.append(content_text[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课件资源_{i+1}"
                    item['title'] = title

                    all_courseware.append(item)
                    logger.info(f"解析云端课件: {filename}")

            except Exception as e:
                logger.error(f"解析课件汇总表失败: {index_file}, 错误: {e}")

        return all_courseware