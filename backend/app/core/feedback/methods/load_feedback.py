from .._shared import *


class _LoadFeedbackMixin:
    def _load_feedback(self) -> Dict[str, Any]:
        """加载反馈数据"""
        if FEEDBACK_FILE.exists():
            try:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保数据结构完整
                    return self._ensure_data_structure(data)
            except Exception as e:
                print(f"⚠️  加载反馈数据失败: {e}")
                return self._get_default_structure()
        return self._get_default_structure()
