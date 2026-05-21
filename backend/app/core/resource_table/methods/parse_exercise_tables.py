from .._shared import *


class _ParseExerciseTablesMixin:
    @staticmethod
    def _normalize_exercise_stem(value: str) -> str:
        normalized = str(value or '').strip().lower()
        normalized = normalized.replace('的', '').replace(' ', '')
        normalized = normalized.replace('（', '(').replace('）', ')')
        return normalized

    def _load_cloud_exercise_index_map(self) -> Dict[str, Dict[str, str]]:
        try:
            import pandas as pd
        except ImportError:
            logger.warning("未安装 pandas，跳过云端习题索引映射加载")
            return {}

        index_map: Dict[str, Dict[str, str]] = {}
        index_paths = [p for p in sorted(self.learning_resource_path.glob('*习题_云端资源汇总表.xlsx')) if not p.name.startswith('~$')]
        for index_path in index_paths:
            board_name = index_path.stem.replace('_云端资源汇总表', '')
            try:
                dataframe = pd.read_excel(index_path).fillna('')
            except Exception as e:
                logger.error(f"读取云端习题索引失败: {index_path}, 错误: {e}")
                continue

            markdown_rows = dataframe[dataframe['文件名'].astype(str).str.lower().str.endswith('.md')]
            for _, row in markdown_rows.iterrows():
                filename = str(row.get('文件名', '')).strip()
                if not filename:
                    continue
                stem = Path(filename).stem
                normalized_stem = self._normalize_exercise_stem(stem)
                markdown_url = str(row.get('云端链接', '')).strip()
                linked_xlsx_url = f"{markdown_url[:-3]}.xlsx" if markdown_url.lower().endswith('.md') else ''
                index_map[normalized_stem] = {
                    '云端链接': markdown_url,
                    '原文件云端链接': linked_xlsx_url,
                    '本地完整路径': str(row.get('本地完整路径', '')).strip(),
                    '上传状态': str(row.get('上传状态', '')).strip(),
                    '链接状态': str(row.get('链接状态', '')).strip(),
                    '板块': board_name,
                    '索引文件': index_path.name,
                }
        return index_map

    def _clean_exercise_text(self, text: str) -> str:
        cleaned = str(text or '')
        cleaned = cleaned.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def _build_exercise_signature(self, item: Dict[str, str], fallback_title: str = '') -> str:
        question = self._clean_exercise_text(item.get('题干', ''))
        answer = self._clean_exercise_text(item.get('解析', ''))
        knowledge = self._clean_exercise_text(item.get('知识点', item.get('知识点标签', '')))
        question_type = self._clean_exercise_text(item.get('题目类型', ''))
        title = self._clean_exercise_text(fallback_title)
        return '|'.join([title, question_type, knowledge, question[:200], answer[:120]]).lower()

    def _finalize_exercise_items(
        self,
        data: List[Dict[str, str]],
        source_file: str,
        title: str,
        extra_metadata: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        extra_metadata = extra_metadata or {}

        for item in data:
            item['resource_type'] = 'exercise'
            item['source_file'] = source_file
            item['title'] = title[:50] if len(title) > 50 else title
            item.update({k: v for k, v in extra_metadata.items() if v})

            source_marker = source_file
            knowledge_points = item.get('知识点', item.get('知识点标签', ''))
            if '三角恒等' in source_marker or '恒等变换' in source_marker or '恒等变化' in source_marker:
                if '三角恒等变换' not in knowledge_points:
                    knowledge_points = knowledge_points + ';三角恒等变换' if knowledge_points else '三角恒等变换'
                item['知识点'] = knowledge_points
                if '知识点标签' not in item or not item['知识点标签']:
                    item['知识点标签'] = knowledge_points

            question = item.get('题干', '')
            if question:
                application_keywords = [
                    '实际应用', '应用', '生活', '工程', '经济', '物理', '化学', '生物',
                    '建筑', '施工', '设计', '测量', '机械', '电力', '水利', '交通',
                    '购物', '消费', '工资', '收入', '支出', '成本', '利润', '收益',
                    '价格', '销售', '市场', '需求', '供给', '投资', '理财', '股票',
                    '债券', '利率', '利息', '人口增长', '放射性衰变', '指数增长', '指数衰减',
                    '周期性变化', '波形', '最优化', '最优解', '实际问题', '生活场景',
                    '经济问题', '工程问题', '物理问题', '化学问题', '生物问题'
                ]
                is_application = any(keyword in question for keyword in application_keywords)
                if is_application:
                    original_type = item.get('题目类型', '')
                    if '应用题' not in original_type:
                        item['题目类型'] = f"{original_type},应用题" if original_type else "应用题"

        grade_enricher = get_grade_enricher()
        for item in data:
            grade_enricher.enrich_resource_grade(item)

        return data

    def _parse_local_exercise_tables(self, cloud_index_map: Optional[Dict[str, Dict[str, str]]] = None) -> List[Dict[str, str]]:
        exercise_folder = self.learning_resource_path / '习题'
        if not exercise_folder.exists():
            logger.warning(f"习题文件夹不存在: {exercise_folder}")
            return []

        all_exercises = []
        cloud_index_map = cloud_index_map or {}
        for md_file in exercise_folder.rglob('*.md'):
            if md_file.name in ['题目目录.md', '答案目录.md']:
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                data = self.parse_markdown_table(content)
                title = md_file.stem
                if title.isdigit():
                    path_parts = md_file.relative_to(self.learning_resource_path).parts
                    for part in path_parts:
                        if '二次函数' in part or '函数' in part or '三角函数' in part or '指数函数' in part or '对数函数' in part or '幂函数' in part or '三角恒等' in part:
                            title = part
                            break

                source_file = str(md_file.relative_to(self.learning_resource_path))
                normalized_stem = self._normalize_exercise_stem(md_file.stem)
                extra_metadata = cloud_index_map.get(normalized_stem, {})
                data = self._finalize_exercise_items(data, source_file, title, extra_metadata)
                all_exercises.extend(data)
                logger.info(f"解析本地习题: {md_file.name}, 共{len(data)}条记录")

            except Exception as e:
                logger.error(f"解析习题文件失败: {md_file}, 错误: {e}")

        return all_exercises

    def _parse_cloud_exercise_tables(self, local_stems: set[str]) -> List[Dict[str, str]]:
        try:
            import pandas as pd
        except ImportError:
            logger.warning("未安装 pandas，跳过根目录云端习题索引导入")
            return []

        index_paths = [p for p in sorted(self.learning_resource_path.glob('*习题_云端资源汇总表.xlsx')) if not p.name.startswith('~$')]
        if not index_paths:
            return []

        all_exercises = []
        for index_path in index_paths:
            board_name = index_path.stem.replace('_云端资源汇总表', '')
            logger.info(f"读取云端习题索引: {index_path.name}")

            try:
                dataframe = pd.read_excel(index_path).fillna('')
            except Exception as e:
                logger.error(f"读取云端习题索引失败: {index_path}, 错误: {e}")
                continue

            markdown_rows = dataframe[dataframe['文件名'].astype(str).str.lower().str.endswith('.md')]
            for _, row in markdown_rows.iterrows():
                filename = str(row.get('文件名', '')).strip()
                if not filename:
                    continue

                stem = Path(filename).stem.lower()
                if stem in local_stems:
                    logger.info(f"跳过已存在的本地习题云端索引: {filename}")
                    continue

                markdown_url = str(row.get('云端链接', '')).strip()
                if not markdown_url:
                    continue

                content = self._download_cloud_markdown(markdown_url)
                if not content:
                    logger.warning(f"云端习题下载失败，跳过: {markdown_url}")
                    continue

                data = self.parse_markdown_table(content)
                if not data:
                    logger.warning(f"云端习题内容未解析出题目，跳过: {filename}")
                    continue

                source_file = f"云端习题/{board_name}/{filename}"
                linked_xlsx_url = f"{markdown_url[:-3]}.xlsx" if markdown_url.lower().endswith('.md') else ''
                extra_metadata = {
                    '云端链接': markdown_url,
                    '原文件云端链接': linked_xlsx_url,
                    '本地完整路径': str(row.get('本地完整路径', '')).strip(),
                    '上传状态': str(row.get('上传状态', '')).strip(),
                    '链接状态': str(row.get('链接状态', '')).strip(),
                    '板块': board_name,
                    '索引文件': index_path.name,
                }
                data = self._finalize_exercise_items(data, source_file, Path(filename).stem, extra_metadata)
                all_exercises.extend(data)
                logger.info(f"解析云端习题: {filename}, 共{len(data)}条记录")

        return all_exercises

    def parse_exercise_tables(self) -> List[Dict[str, str]]:
        """
        解析习题资源汇总表
        
        Returns:
            习题资源列表
        """
        cloud_index_map = self._load_cloud_exercise_index_map()
        local_exercises = self._parse_local_exercise_tables(cloud_index_map)
        local_stems = {
            Path(item.get('title', '')).stem.lower()
            for item in local_exercises
            if item.get('title')
        }
        cloud_exercises = self._parse_cloud_exercise_tables(local_stems)

        all_exercises = []
        seen_signatures = set()
        for item in local_exercises + cloud_exercises:
            signature = self._build_exercise_signature(item, item.get('title', ''))
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            all_exercises.append(item)

        if all_exercises:
            grade_stats = get_grade_enricher().get_grade_statistics(all_exercises)
            logger.info(f"习题年级分布: {grade_stats}")

        logger.info(
            f"解析习题汇总表完成，共{len(all_exercises)}条记录"
            f"（本地{len(local_exercises)}，云端新增{len(cloud_exercises)}，去重后{len(all_exercises)}）"
        )
        return all_exercises
