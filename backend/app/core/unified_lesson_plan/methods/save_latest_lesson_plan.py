from .._shared import *


class _SaveLatestLessonPlanMixin:
    def _save_latest_lesson_plan(self):
        """
        将最新的教案保存到文件中
        """
        if self.latest_lesson_plan:
            try:
                data = {
                    'lesson_plan': self.latest_lesson_plan,
                    'topic': self.latest_topic,
                    'timestamp': str(uuid.uuid4())  # 用于标识版本
                }
                # 确保目录存在
                os.makedirs(os.path.dirname(self.lesson_plan_file), exist_ok=True)
                with open(self.lesson_plan_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 最新教案已保存到文件: {self.latest_topic}")
            except Exception as e:
                print(f"⚠️ 保存最新教案失败: {e}")
