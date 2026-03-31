from .._shared import *


class _InitMixin:
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化用户系统
        
        Args:
            data_dir: 数据存储目录，默认为 backend/data
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "backend" / "data"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.history_file = self.data_dir / "lesson_plan_history.json"
        
        self._initialize_data_files()
