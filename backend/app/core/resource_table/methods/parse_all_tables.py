from .._shared import *


class _ParseAllTablesMixin:
    def parse_all_tables(self) -> Dict[str, List[Dict[str, str]]]:
        """
        解析所有资源汇总表
        
        Returns:
            所有资源的字典，按类型分组
        """
        logger.info("开始解析所有资源汇总表...")
        
        all_resources = {
            'ggb': self.parse_ggb_table(),
            'syllabus': self.parse_syllabus_table(),
            'exercise': self.parse_exercise_tables(),
            'lesson_plan': self.parse_lesson_plan_tables(),
            'excellent_case': self.parse_excellent_case_table(),
            'theory': self.parse_theory_cards(),
            'courseware': self.parse_courseware_table(),
            'lesson_case': self.parse_lesson_case_table()
        }
        
        total_count = sum(len(resources) for resources in all_resources.values())
        logger.info(f"解析完成，共{total_count}条记录")
        
        return all_resources
