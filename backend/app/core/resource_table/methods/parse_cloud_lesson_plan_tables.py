from .._shared import *


class _ParseCloudLessonPlanTablesMixin:
    def _parse_cloud_lesson_plan_tables(
        self,
        limit: Optional[int] = None,
        boards: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        基于根目录CSV索引解析云端教案资源
        仅使用Markdown文件建索引，并关联原始文件与图片资源
        """
        index_rows = self._load_cloud_lesson_plan_index(boards=self._normalize_board_filters(boards))
        if not index_rows:
            return []

        rows_by_filename: Dict[str, Dict[str, str]] = {}
        rows_by_name: Dict[str, List[Dict[str, str]]] = {}
        for row in index_rows:
            logical_path = self._build_logical_lesson_plan_path(row)
            rows_by_filename[logical_path.lower()] = row
            rows_by_name.setdefault(self._normalize_filename_key(row.get("文件名", "")), []).append(row)

        markdown_rows = [
            row for row in index_rows
            if row.get("扩展名", "").lower() == ".md" or row.get("文件类型", "") == "Markdown文件"
        ]
        if limit is not None:
            markdown_rows = markdown_rows[:limit]

        all_lesson_plans = []
        grade_enricher = get_grade_enricher()

        for row in markdown_rows:
            filename = row.get("文件名", "")
            logical_path = self._build_logical_lesson_plan_path(row)
            logger.info(f"处理云端教案: {len(all_lesson_plans) + 1}/{len(markdown_rows)} | {logical_path}")
            title = Path(filename).stem
            directory = row.get("目录", "")
            full_text = f"{title} {directory} {logical_path}"

            chapter_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', full_text)
            chapter = chapter_match.group(1) if chapter_match else ''

            extracted_topics = self._extract_lesson_plan_topics(full_text)
            linked_filename = row.get("关联文件", "").strip()
            linked_row = self._find_linked_lesson_plan_row(row, rows_by_filename, rows_by_name)

            markdown_url = row.get("云端链接", "").strip()
            if not markdown_url:
                markdown_url = self._derive_markdown_url(filename, linked_row)

            content = self._download_cloud_markdown(markdown_url)
            content_source = "cloud_markdown"
            if not content:
                logger.warning(f"云端教案Markdown缺失，使用索引摘要降级: {logical_path}")
                content = self._build_lesson_plan_fallback_content(row, logical_path, linked_row, extracted_topics)
                content_source = "index_fallback"

            item = {
                'resource_type': 'lesson_plan',
                'source_file': logical_path,
                'title': title,
                'content': content,
                '章节': chapter,
                '知识点标签': ', '.join(dict.fromkeys(extracted_topics)),
                '文件名主题': extracted_topics[0] if extracted_topics else '',
                '文件名': filename,
                '目录': directory,
                '云端链接': markdown_url,
                '完整路径': row.get("完整路径", ""),
                '关联文件': linked_filename,
                '原文件云端链接': linked_row.get("云端链接", "") if linked_row else "",
                '原文件名': linked_row.get("文件名", "") if linked_row else linked_filename,
                '图片数量': row.get("图片数量", ""),
                '备注': row.get("备注", ""),
                '板块': row.get("板块", ""),
                '索引文件': row.get("索引文件", ""),
                'content_source': content_source
            }

            grade_enricher.enrich_resource_grade(item)
            all_lesson_plans.append(item)

        if all_lesson_plans:
            grade_stats = grade_enricher.get_grade_statistics(all_lesson_plans)
            logger.info(f"云端教案年级分布: {grade_stats}")

        logger.info(f"解析云端教案资源完成，共{len(all_lesson_plans)}条记录")
        return all_lesson_plans
