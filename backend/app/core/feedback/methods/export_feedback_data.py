from .._shared import *


class _ExportFeedbackDataMixin:
    def export_feedback_data(self, export_path: str = None) -> str:
        """导出反馈数据"""
        if export_path is None:
            export_path = FEEDBACK_DATA_DIR / f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 反馈数据已导出到: {export_path}")
            return str(export_path)
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""


# 全局反馈系统实例
_feedback_system = None
