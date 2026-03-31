from .._shared import *


class _ExtractQuantityLimitMixin:
    def _extract_quantity_limit(self, user_input: str) -> Optional[int]:
        """
        V33.0: 从用户输入中提取数量限制
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            数量限制，如果没有则返回None
        """
        for pattern, extractor in self.V33_NUMBER_PATTERNS:
            match = re.search(pattern, user_input)
            if match:
                return extractor(match)
        return None
