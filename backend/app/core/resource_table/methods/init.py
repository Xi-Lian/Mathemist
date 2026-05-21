from .._shared import *


class _InitMixin:
    def __init__(self, learning_resource_path: str):
        """
        初始化解析器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        # 确保learning_resource_path是绝对路径
        self.learning_resource_path = Path(learning_resource_path).resolve()
        # 处理learning_resource或learning-resource文件夹
        self.project_root = self.learning_resource_path.parent if (self.learning_resource_path.name == "learning_resource" or self.learning_resource_path.name == "learning-resource") else self.learning_resource_path
        self.lesson_plan_cache_dir = self.project_root / "backend" / "data" / "cloud_lesson_plan_cache"
        self.lesson_plan_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # V54.0改进：初始化关键词映射表
        self._init_keyword_mappings()
