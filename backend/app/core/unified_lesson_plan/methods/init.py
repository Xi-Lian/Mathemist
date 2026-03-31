from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化统一教案系统"""
        self.lesson_plan_generator = LessonPlanGenerator()
        self.resource_retriever = ResourceRetriever()
        self.model_config = model_config
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.latest_lesson_plan = None  # 存储最新生成的教案
        self.latest_topic = None  # 存储最新生成的教案的课题
        self.lesson_plan_file = os.path.join(os.path.dirname(__file__), "..", "..", "latest_lesson_plan.json")
        self.session_timeout = config_manager.get_session_timeout()  # 从配置获取会话超时时间
        
        # 加载最新教案
        self._load_latest_lesson_plan()
        # 清理过期会话
        self._clean_expired_sessions()
