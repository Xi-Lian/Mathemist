from .._shared import *


class _LoadLatestLessonPlanMixin:
    def _load_latest_lesson_plan(self):
        """
        从文件中加载最新的教案
        """
        if os.path.exists(self.lesson_plan_file):
            try:
                with open(self.lesson_plan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.latest_lesson_plan = data.get('lesson_plan')
                    self.latest_topic = data.get('topic')
                print(f"✅ 从文件加载最新教案: {self.latest_topic}")
            except Exception as e:
                print(f"⚠️ 加载最新教案失败: {e}")
        else:
            print("ℹ️ 最新教案文件不存在")
