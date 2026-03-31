from .._shared import *


class _GetCloudLessonPlanCsvFilesMixin:
    def _get_cloud_lesson_plan_csv_files(self, boards: Optional[List[str]] = None) -> List[Path]:
        """
        获取根目录下的教案资源CSV索引文件
        """
        csv_files = sorted(self.project_root.glob("*教案资源信息汇总表.csv"))
        board_filters = set(self._normalize_board_filters(boards))
        result = [path for path in csv_files if path.is_file()]
        if board_filters:
            result = [
                path for path in result
                if path.stem.replace("-教案资源信息汇总表", "") in board_filters
            ]
        return result
