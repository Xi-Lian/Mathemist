from .._shared import *


class _InitMixin:
    def __init__(self):
        self.feedback_data = self._load_feedback()
