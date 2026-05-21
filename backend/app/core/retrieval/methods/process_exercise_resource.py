from .._shared import *
from .derive_exercise_image_url import derive_exercise_image_url


class _ProcessExerciseResourceMixin:
    def _get_exercise_index_root(self) -> Path:
        candidates = []

        learning_resource_path = getattr(self, 'learning_resource_path', None)
        if isinstance(learning_resource_path, Path):
            if learning_resource_path.name == 'learning_resource':
                candidates.append(learning_resource_path)  # 返回 learning_resource 目录本身
            candidates.extend(learning_resource_path.parents)

        parser = getattr(self, 'parser', None)
        parser_root = getattr(parser, 'project_root', None)
        if isinstance(parser_root, Path):
            candidates.append(parser_root)

        candidates.extend([Path.cwd(), Path(__file__).resolve().parents[5]])

        seen = set()
        for candidate in candidates:
            candidate = Path(candidate).resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if any(candidate.glob('*习题_云端资源汇总表.xlsx')):
                return candidate

        return Path.cwd()

    @staticmethod
    def _normalize_exercise_stem(value: str) -> str:
        normalized = str(value or '').strip().lower()
        normalized = normalized.replace('的', '').replace(' ', '')
        normalized = normalized.replace('（', '(').replace('）', ')')
        return normalized

    def _get_exercise_cloud_index_map(self) -> Dict[str, Dict[str, str]]:
        cache = getattr(self, "_exercise_cloud_index_map", None)
        if cache is not None:
            return cache

        try:
            import pandas as pd
        except ImportError:
            self._exercise_cloud_index_map = {}
            self._exercise_cloud_asset_map = {}
            return {}

        index_map: Dict[str, Dict[str, str]] = {}
        asset_map: Dict[str, str] = {}
        project_root = self._get_exercise_index_root()
        for index_path in sorted(project_root.glob('*习题_云端资源汇总表.xlsx')):
            if index_path.name.startswith('~$'):
                continue
            board_name = index_path.stem.replace('_云端资源汇总表', '')
            try:
                dataframe = pd.read_excel(index_path).fillna('')
            except Exception:
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
                    '板块': board_name,
                    '本地完整路径': str(row.get('本地完整路径', '')).strip(),
                }

            image_rows = dataframe[dataframe['文件名'].astype(str).str.lower().str.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
            for _, row in image_rows.iterrows():
                filename = str(row.get('文件名', '')).strip()
                cloud_url = str(row.get('云端链接', '')).strip()
                if filename and cloud_url:
                    asset_map[filename] = cloud_url

        self._exercise_cloud_index_map = index_map
        self._exercise_cloud_asset_map = asset_map
        return index_map

    def _resolve_exercise_asset_url(self, filename: str, cloud_source: str, image_kind: str) -> str:
        normalized_filename = (filename or '').strip()
        if not normalized_filename:
            return ''

        asset_map = getattr(self, '_exercise_cloud_asset_map', None)
        if asset_map is None:
            self._get_exercise_cloud_index_map()
            asset_map = getattr(self, '_exercise_cloud_asset_map', {})

        exact_url = asset_map.get(normalized_filename, '')
        if exact_url:
            return exact_url

        return derive_exercise_image_url(normalized_filename, cloud_source, image_kind)

    def _resolve_exercise_cloud_source(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        resolved = {
            '云端链接': (metadata.get('云端链接', '') or '').strip(),
            '原文件云端链接': (metadata.get('原文件云端链接', '') or '').strip(),
        }
        if resolved['云端链接'] or resolved['原文件云端链接']:
            return resolved

        source_file = (metadata.get('source_file', '') or '').strip()
        title = (metadata.get('title', '') or '').strip()
        stem_candidates = [
            self._normalize_exercise_stem(Path(source_file).stem),
            self._normalize_exercise_stem(title),
        ]
        index_map = self._get_exercise_cloud_index_map()
        for stem in stem_candidates:
            if not stem:
                continue
            matched = index_map.get(stem)
            if matched:
                return {
                    '云端链接': matched.get('云端链接', ''),
                    '原文件云端链接': matched.get('原文件云端链接', ''),
                }
        return resolved

    def _process_exercise_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理习题资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        # 获取题目文件名
        filename = (metadata.get('题目文件名', '') or '').strip()
        source_file = metadata.get('source_file', '')
        question = (metadata.get('题干', '') or '').strip()
        answer = (metadata.get('解析', '') or '').strip()
        difficulty = metadata.get('难度（1-5）', '') or metadata.get('难度', '')
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        usage_scene = metadata.get('适用场景', '')
        question_type = metadata.get('题目类型', '')
        resolved_cloud = self._resolve_exercise_cloud_source(metadata)
        cloud_source = resolved_cloud.get('原文件云端链接', '') or resolved_cloud.get('云端链接', '') or source_file

        is_question_image = self._is_exercise_image_filename(filename)
        is_answer_image = self._is_exercise_image_filename(answer)
        question_image_url = self._resolve_exercise_asset_url(filename, cloud_source, 'question') if is_question_image else ''
        answer_image_url = self._resolve_exercise_asset_url(answer, cloud_source, 'answer') if is_answer_image else ''

        resource['source'] = cloud_source
        resource['cloud_url'] = resolved_cloud.get('云端链接', '') or metadata.get('云端链接', '')
        resource['original_file_url'] = resolved_cloud.get('原文件云端链接', '') or metadata.get('原文件云端链接', '')
        resource['filename'] = filename
        resource['question'] = question
        resource['answer'] = answer
        resource['difficulty'] = difficulty
        resource['knowledge_tags'] = knowledge_tags
        resource['usage_scene'] = usage_scene
        resource['question_type'] = question_type
        resource['question_format'] = 'image' if is_question_image else 'text'
        resource['answer_format'] = self._get_exercise_answer_format(answer)
        resource['question_image_url'] = question_image_url
        resource['answer_image_url'] = answer_image_url
        resource['has_question_image'] = bool(question_image_url)
        resource['has_answer_image'] = bool(answer_image_url)
        resource['is_image_exercise'] = is_question_image

        if is_question_image:
            # 有文件名，说明是图片题目
            resource['title'] = f"习题（图片）: {filename}"
            resource['content'] = f"题目类型：{question_type}\n题目描述：{question}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}\n解析：{answer}"
        else:
            # 文字题目，显示完整题目
            resource['title'] = f"习题: {question_type}"
            resource['content'] = f"题目：{question}\n\n解析：{answer}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}"

    @staticmethod
    def _is_exercise_image_filename(value: str) -> bool:
        value = (value or '').strip().lower()
        return value.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))

    def _get_exercise_answer_format(self, answer: str) -> str:
        if self._is_exercise_image_filename(answer):
            return 'image'
        if not answer:
            return 'text'
        if any(marker in answer for marker in ('$', '\\(', '\\[', '\\frac', '\\begin{')):
            return 'latex'
        return 'text'
