"""
主题匹配服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.match_theme import _MatchThemeMixin
from .methods.check_keywords_in_text import _CheckKeywordsInTextMixin
from .methods.print_match_info import _PrintMatchInfoMixin
from .methods.get_all_themes import _GetAllThemesMixin
from .methods.add_theme_keywords import _AddThemeKeywordsMixin
from .methods.dynamic_theme_detection import _DynamicThemeDetectionMixin
from .methods.detect_formula_themes import _DetectFormulaThemesMixin
from .methods.detect_context_themes import _DetectContextThemesMixin
from .methods.update_theme_weights import _UpdateThemeWeightsMixin
from .methods.process_feedback import _ProcessFeedbackMixin

class ThemeMatcher(_InitMixin, _MatchThemeMixin, _CheckKeywordsInTextMixin, _PrintMatchInfoMixin, _GetAllThemesMixin, _AddThemeKeywordsMixin, _DynamicThemeDetectionMixin, _DetectFormulaThemesMixin, _DetectContextThemesMixin, _UpdateThemeWeightsMixin, _ProcessFeedbackMixin):
    """主题匹配器"""
    
    # 主题-关键词映射库（通用版）
    # 结构: {
    #     "主题名": {
    #         "core_keywords": ["核心关键词（一级证据）"],
    #         "related_keywords": ["相关关键词（三级证据）"],
    #         "chapter_indicators": ["章节标识（二级证据）"],
    #         "conflict_themes": ["冲突主题"],
    #         "path_keywords": ["路径关键词（二级证据）"]
    #     }
    # }
    THEME_KEYWORD_MAP = {
        "函数的单调性": {
            "core_keywords": ["函数的单调性", "单调性", "单调递增", "单调递减", "增函数", "减函数"],
            "related_keywords": ["单调区间", "最值", "最大值", "最小值", "极值", "单调性与最值"],
            "chapter_indicators": ["3.2.1", "3-2-1"],
            "conflict_themes": ["函数的奇偶性", "函数的周期性", "函数的概念", "函数的表示法", "函数的应用"],
            "path_keywords": ["单调性", "单调"]
        },
        "函数的奇偶性": {
            "core_keywords": ["函数的奇偶性", "奇偶性", "奇函数", "偶函数"],
            "related_keywords": ["对称性", "关于原点对称", "关于y轴对称", "f(-x)"],
            "chapter_indicators": ["3.2.2", "3-2-2"],
            "conflict_themes": ["函数的单调性", "函数的周期性", "函数的概念", "函数的表示法"],
            "path_keywords": ["奇偶性", "奇偶"]
        },
        "函数的周期性": {
            "core_keywords": ["函数的周期性", "周期性", "周期函数", "最小正周期"],
            "related_keywords": ["周期", "T", "f(x+T)", "正弦周期", "余弦周期"],
            "chapter_indicators": ["5.4"],
            "conflict_themes": ["函数的单调性", "函数的奇偶性", "函数的概念"],
            "path_keywords": ["周期性", "周期"]
        },
        "函数的概念": {
            "core_keywords": ["函数的概念", "函数概念", "函数定义"],
            "related_keywords": ["什么是函数", "函数意义", "函数本质"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["函数的应用", "函数的性质", "函数的表示法", "函数的单调性", "函数的奇偶性"],
            "path_keywords": ["概念", "定义"]
        },
        "指数函数的概念": {
            "core_keywords": ["指数函数的概念", "指数函数概念"],
            "related_keywords": ["指数函数", "指数"],
            "chapter_indicators": ["4.2.1"],
            "conflict_themes": ["对数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["指数函数"]
        },
        "对数函数的概念": {
            "core_keywords": ["对数函数的概念", "对数函数概念"],
            "related_keywords": ["对数函数", "对数"],
            "chapter_indicators": ["4.4.1"],
            "conflict_themes": ["指数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["对数函数"]
        },
        "函数的应用": {
            "core_keywords": ["函数应用", "函数的应用"],
            "related_keywords": ["应用", "建模", "实际问题", "数学建模"],
            "chapter_indicators": ["4.5"],
            "conflict_themes": ["函数的概念", "函数的性质", "函数的表示法", "函数的单调性", "函数的奇偶性"],
            "path_keywords": ["应用"]
        },
        "函数的性质": {
            "core_keywords": ["函数的性质", "函数性质"],
            "related_keywords": ["单调性", "奇偶性", "周期性", "对称性"],
            "chapter_indicators": ["3.2", "3.3"],
            "conflict_themes": ["函数的概念", "函数的应用", "函数的表示法"],
            "path_keywords": ["性质"]
        },
        "函数的表示法": {
            "core_keywords": ["函数的表示法", "函数表示法"],
            "related_keywords": ["解析法", "图像法", "列表法", "映射"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["函数的概念", "函数的应用", "函数的性质"],
            "path_keywords": ["表示法"]
        },
        "指数函数": {
            "core_keywords": ["指数函数", "指数与指数函数"],
            "related_keywords": ["2^x", "a^x", "e^", "指数增长", "指数衰减"],
            "chapter_indicators": ["4.2", "4.1"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["指数函数"]
        },
        "指数运算": {
            "core_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂"],
            "related_keywords": ["8^", "2^(", "a^(2/3)", "分数指数", "有理指数幂", "n次根式"],
            "chapter_indicators": ["4.1", "4-1"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数"],
            "path_keywords": ["指数", "4-1"],
            "description": "指数运算是计算 a^b 形式的值，底数是常数，指数可以是分数"
        },
        "对数函数": {
            "core_keywords": ["对数函数", "对数与对数函数"],
            "related_keywords": ["log", "ln", "对数增长", "对数衰减", "对数运算", "对数方程", "换底公式", "对数性质"],
            "chapter_indicators": ["4.3", "4.4"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["对数"]
        },
        "对数函数运算": {
            "core_keywords": ["对数函数运算", "对数运算", "换底公式"],
            "related_keywords": ["log", "ln", "对数性质", "对数方程"],
            "chapter_indicators": ["4.3.2", "4-3-2"],
            "conflict_themes": ["指数函数", "幂函数", "三角函数", "二次函数"],
            "path_keywords": ["对数运算", "换底公式"]
        },
        "指数与对数函数综合": {
            "core_keywords": ["指数与对数函数综合", "指数对数综合", "综合应用"],
            "related_keywords": ["指数函数", "对数函数", "综合题", "实际应用", "函数模型"],
            "chapter_indicators": ["4.4", "4.5"],
            "conflict_themes": ["三角函数", "二次函数", "幂函数"],
            "path_keywords": ["综合", "应用"]
        },
        "幂函数": {
            "core_keywords": ["幂函数", "y=x^a", "y = x^a", "幂函数的图像", "幂函数的性质"],
            "related_keywords": ["x^a", "x的幂", "幂运算", "幂函数图像"],
            "chapter_indicators": ["3.3", "3-3"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "二次函数", "一次函数", "分段函数", "指数运算"],
            "path_keywords": ["幂函数", "3-3幂函数", "3.3幂函数"],
            "exclude_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂", "8^", "2^(", "a^x", "a^(2/3)", "分数指数"]
        },
        "二次函数": {
            "core_keywords": ["二次函数"],
            "related_keywords": ["二次", "x²", "x^2", "一元二次", "抛物线", "顶点式", "一般式"],
            "chapter_indicators": ["3.1", "3.2", "3.3"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "一次函数", "分段函数"],
            "path_keywords": ["二次"]
        },
        "一次函数": {
            "core_keywords": ["一次函数", "线性函数"],
            "related_keywords": ["一次", "y=kx+b", "斜率", "截距", "直线"],
            "chapter_indicators": ["3.1"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "分段函数"],
            "path_keywords": ["一次"]
        },
        "三角函数": {
            "core_keywords": ["三角函数", "正弦", "余弦", "正切"],
            "related_keywords": ["三角", "sin", "cos", "tan", "cot", "sec", "csc", "任意角", "诱导公式"],
            "chapter_indicators": ["5.1", "5.2", "5.3", "5.4", "5.6"],
            "conflict_themes": ["指数函数", "对数函数", "二次函数", "幂函数", "一次函数", "分段函数"],
            "path_keywords": ["三角"]
        },
        "三角恒等变换": {
            "core_keywords": ["三角恒等变换", "三角恒等式", "恒等变换", "和差化积", "积化和差", "二倍角", "半角公式"],
            "related_keywords": ["sin", "cos", "tan", "诱导公式", "两角和与差", "三角公式"],
            "chapter_indicators": ["5.5", "5-5"],
            "conflict_themes": ["指数函数", "对数函数", "二次函数", "幂函数", "一次函数"],
            "path_keywords": ["三角恒等变换", "5-5", "恒等变换"]
        },
        "分段函数": {
            "core_keywords": ["分段函数"],
            "related_keywords": ["分段", "绝对值函数", "取整函数", "符号函数"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["分段"]
        },
        "导数": {
            "core_keywords": ["导数", "导函数", "微分", "求导"],
            "related_keywords": ["f'", "y'", "dy/dx", "导数的几何意义", "切线方程", "瞬时变化率"],
            "chapter_indicators": ["6.1", "6.2", "6-1", "6-2"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["导数", "微分", "求导"]
        },
        "导数的应用": {
            "core_keywords": ["导数的应用", "导数应用"],
            "related_keywords": ["单调性", "极值", "最值", "优化问题", "切线", "曲率"],
            "chapter_indicators": ["6.3", "6.4", "6-3", "6-4"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["导数应用", "应用"]
        }
    }
    
    # 加分配置（提高主题匹配的权重）
    BOOST_CONFIG = {
        "filename_core_keyword_match": 0.80,  # 文件名包含核心关键词（最高优先级）
        "title_core_keyword_match": 0.75,  # 标题包含核心关键词
        "core_keyword_match": 0.70,  # 其他地方核心关键词匹配
        "chapter_indicator_match": 0.65,  # 章节标识匹配
        "path_keyword_match": 0.60,  # 路径关键词匹配
        "related_keyword_match": 0.55,  # 相关关键词匹配
        "weak_match": 0.50  # 弱匹配
    }
    
    # 减分配置
    PENALTY_CONFIG = {
        "conflict_theme": 0.35  # 冲突主题
    }


_theme_matcher = None

def get_theme_matcher() -> ThemeMatcher:
    """
    获取主题匹配器实例（单例模式）
    
    Returns:
        主题匹配器
    """
    global _theme_matcher
    if _theme_matcher is None:
        _theme_matcher = ThemeMatcher()
    return _theme_matcher
