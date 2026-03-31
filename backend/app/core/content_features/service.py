"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.is_application_problem import _IsApplicationProblemMixin
from .methods.extract_features import _ExtractFeaturesMixin
from .methods.check_keywords import _CheckKeywordsMixin
from .methods.generate_summary import _GenerateSummaryMixin
from .methods.extract_query_content_features import _ExtractQueryContentFeaturesMixin
from .methods.calculate_content_match_score import _CalculateContentMatchScoreMixin

class ContentFeatureExtractor(_InitMixin, _IsApplicationProblemMixin, _ExtractFeaturesMixin, _CheckKeywordsMixin, _GenerateSummaryMixin, _ExtractQueryContentFeaturesMixin, _CalculateContentMatchScoreMixin):
    """教案内容特征提取器"""
    
    # 教学方法关键词库
    TEACHING_METHODS = {
        '小组讨论': ['小组讨论', '分组讨论', '合作学习', '小组合作', '协作学习'],
        '实验探究': ['实验', '探究', '探究式', '探究性', '发现式', '探索'],
        '案例分析': ['案例', '实例', '实际问题', '应用问题'],
        '翻转课堂': ['翻转课堂', '翻转', '课前预习', '课前学习'],
        '多媒体教学': ['多媒体', 'PPT', '课件', '视频', '动画', '信息化'],
        '情境教学': ['情境', '情景', '实际情境', '问题情境'],
        '启发式教学': ['启发', '引导', '提问', '问题驱动'],
        '讲授法': ['讲授', '讲解', '讲述', '精讲'],
        '练习巩固': ['练习', '课堂练习', '巩固', '训练'],
        '自主探究': ['自主', '自主探究', '自主学习', '独立探究'],
        '项目式学习': ['项目', '项目式', '任务驱动', '任务'],
        '游戏化教学': ['游戏', '游戏化', '趣味', '竞赛']
    }
    
    # 教学环节关键词库
    TEACHING_STAGES = {
        '导入': ['导入', '引入', '新课导入', '情境导入'],
        '新课讲授': ['讲授', '讲解', '新知', '新知识'],
        '例题讲解': ['例题', '示范', '示例'],
        '课堂练习': ['练习', '课堂练习', '随堂练习', '巩固练习'],
        '小组活动': ['小组', '活动', '讨论', '合作'],
        '总结归纳': ['总结', '归纳', '小结', '回顾'],
        '作业布置': ['作业', '课后', '布置'],
        '课堂检测': ['检测', '测试', '评价', '反馈']
    }
    
    # 教学手段关键词库
    TEACHING_TOOLS = {
        '多媒体': ['多媒体', 'PPT', '课件', '投影', '电子白板'],
        '实物教具': ['教具', '实物', '模型', '学具'],
        '几何画板': ['几何画板', 'GGB', 'GeoGebra', '图形软件'],
        '在线资源': ['网络', '在线', '互联网', '微课', '慕课']
    }
    
    # 习题难度关键词库
    EXERCISE_DIFFICULTY = {
        '简单': ['简单', '基础', '入门', '初级', '容易'],
        '中等': ['中等', '一般', '普通', '标准'],
        '困难': ['困难', '难', '高级', '拔高', '培优', '挑战', '综合']
    }
    
    # 习题类型关键词库
    EXERCISE_TYPES = {
        '选择题': ['选择题', '单选', '多选', '单选题', '多选题'],
        '填空题': ['填空题', '填空', '填充题', '填充', '空白题', '空白'],
        '解答题': ['解答题', '解答', '大题', '综合题', '简答题', '问答题', '论述题'],
        '计算题': ['计算题', '计算', '运算题', '算术题'],
        '证明题': ['证明题', '证明', '求证题', '推导题'],
        '应用题': ['应用题', '实际应用', '应用', '实际问题', '生活应用', '工程应用', '经济应用', '对数应用', '指数应用', '函数应用', '实际场景', '生活场景', '经济问题', '工程问题', '物理问题', '化学问题', '生物问题'],
        '作图题': ['作图题', '画图', '作图', '绘图题', '绘制题']
    }
    
    # 应用题场景关键词库
    APPLICATION_SCENES = {
        '生活场景': ['生活', '日常', '家庭', '购物', '消费', '工资', '收入', '支出', '水电费', '电话费', '出租车', '公交车', '地铁', '旅行', '旅游', '住宿', '餐饮', '购物'],
        '经济场景': ['经济', '金融', '投资', '理财', '股票', '债券', '利率', '利息', '利润', '成本', '收益', '价格', '销售', '市场', '需求', '供给'],
        '工程场景': ['工程', '建筑', '施工', '设计', '测量', '机械', '电力', '水利', '交通', '桥梁', '道路', '隧道', '建筑材料', '工程预算'],
        '物理场景': ['物理', '力学', '运动', '速度', '加速度', '力', '功', '能', '功率', '热学', '电学', '光学', '声学'],
        '化学场景': ['化学', '化学反应', '化学方程式', '化学平衡', '溶液', '浓度', 'pH值', '化学计算'],
        '生物场景': ['生物', '生态', '遗传', '进化', '细胞', '代谢', '生态系统', '生物多样性'],
        '天文场景': ['天文', '天体', '星系', '宇宙', '行星', '恒星', '卫星', '黑洞', '宇宙大爆炸'],
        '地理场景': ['地理', '地形', '地貌', '气候', '天气', '温度', '降水', '土壤', '植被', '人口', '城市', '国家', '地区']
    }


_content_extractor = None

def get_content_feature_extractor() -> ContentFeatureExtractor:
    """获取内容特征提取器实例（单例模式）"""
    global _content_extractor
    if _content_extractor is None:
        _content_extractor = ContentFeatureExtractor()
    return _content_extractor
