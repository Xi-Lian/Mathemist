from .._shared import *


class _ParseTheoryCardsMixin:
    def parse_theory_cards(self) -> List[Dict[str, str]]:
        """
        解析理论卡片
        优先从云端汇总表获取，已上传云端的资源从云端下载，未上传的尝试本地读取

        Returns:
            理论卡片列表
        """
        theory_cards = []

        # 尝试从云端汇总表解析
        cloud_theory_cards = self._parse_cloud_theory_cards()
        if cloud_theory_cards:
            theory_cards.extend(cloud_theory_cards)
            logger.info(f"从云端汇总表解析到{len(cloud_theory_cards)}条理论卡片")
            return theory_cards

        # 如果没有云端汇总表，尝试从本地文件夹读取
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
        theory_file = self.learning_resource_path / '优秀教案共性整合.md'
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

        # 解析根目录下的理论卡片.md文件
        root_theory_file = self.learning_resource_path / '理论卡片.md'
        if root_theory_file.exists():
            try:
                with open(root_theory_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                item = {
                    'resource_type': 'theory',
                    'source_file': str(root_theory_file.relative_to(self.learning_resource_path)),
                    'title': root_theory_file.stem,
                    'content': content
                }
                theory_cards.append(item)

                logger.info(f"解析根目录下的理论卡片.md文件")

            except Exception as e:
                logger.error(f"解析根目录下的理论卡片.md文件失败: {e}")

        logger.info(f"解析理论卡片完成，共{len(theory_cards)}条记录")
        return theory_cards

    def _parse_cloud_theory_cards(self) -> List[Dict[str, str]]:
        """
        从云端汇总表解析理论卡片

        Returns:
            理论卡片列表
        """
        try:
            import pandas as pd
        except ImportError:
            logger.warning("未安装pandas，跳过云端理论卡片解析")
            return []

        # 查找理论卡片信息汇总表
        theory_card_index_files = list(self.learning_resource_path.glob('*理论卡片*汇总表.csv'))
        if not theory_card_index_files:
            logger.warning("未找到理论卡片信息汇总表")
            return []

        all_theory_cards = []

        for index_file in theory_card_index_files:
            try:
                df = pd.read_csv(index_file, encoding='utf-8-sig')
                logger.info(f"读取理论卡片汇总表: {index_file.name}, 共{len(df)}条记录")

                for _, row in df.iterrows():
                    filename = str(row.get('文件名', '')).strip()
                    cloud_url = str(row.get('云端链接', '')).strip()

                    if not filename:
                        continue

                    # 只处理.md文件
                    if not filename.lower().endswith('.md'):
                        continue

                    title = Path(filename).stem
                    relative_path = str(row.get('相对路径', '')).strip()
                    folder = str(row.get('所属文件夹', '')).strip()

                    # 尝试从云端下载内容
                    content = ''
                    content_source = 'none'
                    if cloud_url:
                        content = self._download_cloud_markdown(cloud_url)
                        if content:
                            content_source = 'cloud'

                    # 构建资源项
                    item = {
                        'resource_type': 'theory',
                        'source_file': relative_path or filename,
                        'title': title,
                        'content': content if content else f"理论卡片：{title}",
                        '文件名': filename,
                        '云端链接': cloud_url,
                        '所属文件夹': folder,
                        'content_source': content_source
                    }

                    all_theory_cards.append(item)
                    logger.info(f"解析云端理论卡片: {filename}")

            except Exception as e:
                logger.error(f"解析理论卡片汇总表失败: {index_file}, 错误: {e}")

        return all_theory_cards