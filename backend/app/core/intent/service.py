"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.analyze import _AnalyzeMixin
from .methods.analyze_context import _AnalyzeContextMixin
from .methods.update_context_history import _UpdateContextHistoryMixin
from .methods.clear_context import _ClearContextMixin
from .methods.extract_quantity_limit import _ExtractQuantityLimitMixin
from .methods.extract_grade_info import _ExtractGradeInfoMixin
from .methods.extract_difficulty_info import _ExtractDifficultyInfoMixin
from .methods.clarify_math_topic import _ClarifyMathTopicMixin
from .methods.analyze_with_llm import _AnalyzeWithLlmMixin
from .methods.parse_llm_response import _ParseLlmResponseMixin
from .methods.clean_json_response import _CleanJsonResponseMixin
from .methods.analyze_with_keywords import _AnalyzeWithKeywordsMixin
from .methods.extract_resource_types import _ExtractResourceTypesMixin
from .methods.generate_user_needs import _GenerateUserNeedsMixin
from .methods.has_keywords import _HasKeywordsMixin
from .methods.get_single_intent_result import _GetSingleIntentResultMixin
from .methods.get_multi_intent_result import _GetMultiIntentResultMixin
from .methods.get_default_intent import _GetDefaultIntentMixin
from .methods.create_prompt_template import _CreatePromptTemplateMixin

class IntentAnalyzer(_InitMixin, _AnalyzeMixin, _AnalyzeContextMixin, _UpdateContextHistoryMixin, _ClearContextMixin, _ExtractQuantityLimitMixin, _ExtractGradeInfoMixin, _ExtractDifficultyInfoMixin, _ClarifyMathTopicMixin, _AnalyzeWithLlmMixin, _ParseLlmResponseMixin, _CleanJsonResponseMixin, _AnalyzeWithKeywordsMixin, _ExtractResourceTypesMixin, _GenerateUserNeedsMixin, _HasKeywordsMixin, _GetSingleIntentResultMixin, _GetMultiIntentResultMixin, _GetDefaultIntentMixin, _CreatePromptTemplateMixin):
    """意图分析器"""
    
    INTENT_SEARCH = "search"
    INTENT_LESSON_PLAN = "generate_lesson_plan"
    INTENT_VISUALIZATION = "visualization"
    INTENT_CONVERSATION = "conversation"
    
    INSTRUCTION_KEYWORDS = {
        "resource_retrieval": ["推送", "给", "找", "搜", "搜索", "查", "查找", "检索", "推荐", "有没有", "我要", "帮我找", "帮我搜", "想要", "需要"],
        "content_generation": ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
    }
    
    KEYWORDS = {
        INTENT_LESSON_PLAN: [
            "教案", "教学设计", "教学计划", "备课"
        ],
        INTENT_VISUALIZATION: [
            "ggb", "可视化", "动态数学", "几何画板", "图形设计"
        ]
    }
    
    V33_NUMBER_PATTERNS = [
        (r'(\d+)\s*[道个条]', lambda m: int(m.group(1))),
        (r'[给找推荐].*?(\d+)', lambda m: int(m.group(1))),
        (r'(\d+)\s*[题个道]', lambda m: int(m.group(1))),
        (r'几[道个条]', lambda m: 5),
        (r'一些', lambda m: 10),
        (r'一点', lambda m: 5),
        (r'多一点', lambda m: 15),
        (r'很多', lambda m: 20),
    ]
    
    V33_DIFFICULTY_PATTERNS = {
        '基础': ['基础', '简单', '容易', '入门', '初级'],
        '中等': ['中等', '一般', '普通', '适中'],
        '困难': ['困难', '难', '挑战', '拔高', '培优', '提高', '高级'],
        '综合': ['综合', '应用', '实际', '综合应用']
    }
    
    V33_GRADE_PATTERNS = {
        '高一上学期': ['高一上', '高一上学期', '必修一', '必修第一册'],
        '高一下学期': ['高一下', '高一下学期', '必修二', '必修第二册'],
        '高二上学期': ['高二上', '高二上学期', '选择性必修一'],
        '高二下学期': ['高二下', '高二下学期', '选择性必修二'],
        '高三': ['高三', '高考', '选择性必修三', '高三学生', '高考复习', '高考备考', '高三数学', '毕业班'],
        '高一': ['高一', '高中一年级', '高一学生'],
        '高二': ['高二', '高中二年级', '高二学生'],
    }
    
    V33_MATH_TOPIC_CLARIFICATION = {
        "幂函数": {
            "core_keywords": ["幂函数", "y=x^a", "y = x^a", "x的幂", "x的a次方"],
            "exclude_keywords": ["指数运算", "指数幂", "分数指数幂", "根式运算", "8^", "2^", "a^x", "指数函数"],
            "description": "幂函数是形如 y = x^a 的函数，底数是变量x，指数是常数a",
            "focus": "函数性质和图像"
        },
        "指数运算": {
            "core_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂", "8^(2/3)", "2^(1/2)"],
            "related_keywords": ["8^", "2^", "a^(2/3)", "分数指数", "根式"],
            "description": "指数运算是计算 a^b 形式的值，底数是常数，指数可以是分数",
            "focus": "计算技巧和化简"
        },
        "指数函数": {
            "core_keywords": ["指数函数", "y=a^x", "y=2^x", "y=e^x"],
            "exclude_keywords": ["幂函数", "对数函数"],
            "description": "指数函数是形如 y = a^x 的函数，底数是常数a，指数是变量x",
            "focus": "函数性质和图像"
        },
        "三角恒等变换": {
            "core_keywords": ["三角恒等变换", "三角恒等式", "恒等变换", "和差化积", "积化和差", "二倍角"],
            "related_keywords": ["sin", "cos", "tan", "诱导公式"],
            "description": "三角恒等变换涉及三角函数之间的恒等式变换",
            "focus": "公式变换和化简"
        },
    }
    
    # 上下文意图模式
    CONTEXT_INTENT_PATTERNS = {
        "continue": ["还要", "再来", "继续", "多一点", "再给", "还有"],
        "refine": ["更", "调整", "修改", "换", "重新", "不同"],
        "specific": ["具体", "详细", "详细一点", "具体一点"],
        "difficulty": ["难", "简单", "基础", "中等", "困难", "挑战"],
        "quantity": ["道", "个", "题", "道题", "个题"]
    }

def intent_understanding_node(state) -> Dict[str, Any]:
    """
    意图理解节点（向后兼容接口）

    Args:
        state: 状态对象

    Returns:
        意图分析结果
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')

    # 确保是字符串
    user_input = str(user_input) if user_input else ''

    # 从 state.chat_history 获取对话历史（优先）
    chat_history = []
    if hasattr(state, 'chat_history') and state.chat_history:
        chat_history = state.chat_history
    # 兼容：从 context 中获取 chat_history（备用）
    elif hasattr(state, 'context') and state.context:
        chat_history = state.context.get('chat_history', [])
    elif isinstance(state, dict):
        chat_history = state.get('chat_history', []) or state.get('context', {}).get('chat_history', [])

    # 分析意图，传递对话历史
    analyzer = IntentAnalyzer()
    return analyzer.analyze(user_input, chat_history=chat_history)
