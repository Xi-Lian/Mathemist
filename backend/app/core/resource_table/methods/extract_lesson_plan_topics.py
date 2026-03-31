from .._shared import *


class _ExtractLessonPlanTopicsMixin:
    def _extract_lesson_plan_topics(self, text: str) -> List[str]:
        """
        从文件名或目录中提取教案主题关键词
        """
        topic_keywords = [
            '单调性', '奇偶性', '周期性', '对称性', '最值', '最大值', '最小值',
            '概念', '表示法', '性质', '应用', '图像', '图象',
            '幂函数', '指数函数', '对数函数', '三角函数', '二次函数', '一次函数',
            '诱导公式', '三角恒等变换', '零点', '二分法',
            '任意角', '弧度制', '同角三角函数',
            '抛物线', '顶点', '对称轴', '开口',
            '方程', '方程求解', '解方程',
            '实际应用', '生活应用', '数学建模',
            '放射性衰变', '指数增长', '指数衰减',
            '周期性变化', '波形', '正弦', '余弦', '正切',
            '概率', '统计', '抽样', '频率', '分布', '复数', '空间向量', '立体几何'
        ]
        return [keyword for keyword in topic_keywords if keyword in text]
