from .._shared import *


class _SaveFeedbackMixin:
    def _save_feedback(self):
        """保存反馈数据"""
        FEEDBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存反馈数据失败: {e}")
