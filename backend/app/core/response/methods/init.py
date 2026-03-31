from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化响应构建器"""
        self.model_config = model_config
        self.content_processor = None
        self.timeout = 30  # V33.0改进：设置超时时间为30秒
        self.start_time = None  # V33.0改进：记录开始时间
