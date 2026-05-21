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
                min(15, int(os.getenv("SEARCH_RESPONSE_MAX_ITEMS_PER_GROUP", "10")))  # 【V103.0优化】默认值从5增加到10，最大值从10增加到15
            )
        except ValueError:
            self.max_display_per_group = 10
