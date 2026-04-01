from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化响应构建器"""
        self.model_config = model_config
        self.content_processor = None
        self.timeout = 30  # V33.0改进：设置超时时间为30秒
        self.start_time = None  # V33.0改进：记录开始时间
        self.show_debug_scores = os.getenv("SEARCH_RESPONSE_SHOW_SCORES", "0").strip().lower() in {
            "1", "true", "yes", "on", "debug", "verbose"
        }
        try:
            self.max_display_per_group = max(
                3,
                min(10, int(os.getenv("SEARCH_RESPONSE_MAX_ITEMS_PER_GROUP", "5")))
            )
        except ValueError:
            self.max_display_per_group = 5
