from .._shared import *


class _CheckTimeoutMixin:
    def _check_timeout(self) -> bool:
        """
        V33.0改进：检查是否超时
        
        Returns:
            是否超时
        """
        if self.start_time is None:
            return False
        
        elapsed = time.time() - self.start_time
        return elapsed > self.timeout
