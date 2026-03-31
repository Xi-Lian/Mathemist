from .._shared import *


class _LoadCloudLessonPlanIndexMixin:
    def _load_cloud_lesson_plan_index(self, boards: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        读取教案资源CSV索引
        """
        rows: List[Dict[str, str]] = []
        for csv_path in self._get_cloud_lesson_plan_csv_files(boards=boards):
            encoding = self._detect_csv_encoding(csv_path)
            domain_name = csv_path.stem.replace("-教案资源信息汇总表", "")
            try:
                with open(csv_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        normalized = {str(k).strip(): (str(v).strip() if v is not None else "") for k, v in row.items() if k}
                        if not normalized.get("文件名"):
                            continue
                        normalized["索引文件"] = csv_path.name
                        normalized["板块"] = domain_name
                        rows.append(normalized)
                logger.info(f"读取云端教案索引: {csv_path.name}, 编码={encoding}, 记录数={sum(1 for row in rows if row.get('索引文件') == csv_path.name)}")
            except Exception as e:
                logger.error(f"读取云端教案索引失败: {csv_path}, 错误: {e}")
        return rows
