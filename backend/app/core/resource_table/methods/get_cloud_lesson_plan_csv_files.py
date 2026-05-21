from .._shared import *


class _GetCloudLessonPlanCsvFilesMixin:
    def _get_cloud_lesson_plan_csv_files(self, boards: Optional[List[str]] = None) -> List[Path]:
        """
        获取根目录下的教案资源CSV索引文件
        """
        csv_files = sorted(self.learning_resource_path.glob("*教案资源信息汇总表.csv"))
        board_filters = set(self._normalize_board_filters(boards))
        result = [path for path in csv_files if path.is_file()]
        if board_filters:
            result = [
                path for path in result
                if self._matches_board_filter(path.stem.replace("-教案资源信息汇总表", ""), board_filters)
            ]
        return result

    def _matches_board_filter(self, csv_board_name: str, board_filters: set) -> bool:
        """
        检查CSV文件名中的板块名称是否匹配过滤条件
        支持模糊匹配，例如"概率统计"可以匹配"概率与统计"
        """
        for filter_name in board_filters:
            # 直接字符串包含匹配
            if filter_name in csv_board_name or csv_board_name in filter_name:
                return True
            # 特殊处理概率统计板块
            if '概率' in filter_name and '概率' in csv_board_name:
                return True
            # 特殊处理函数板块
            if '函数' in filter_name and '函数' in csv_board_name:
                return True
            # 特殊处理几何板块
            if '几何' in filter_name and '几何' in csv_board_name:
                return True
        return False
