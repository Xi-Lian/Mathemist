import logging
from pathlib import Path
from .._shared import *
from ..retrieve_helpers.context import (
    apply_loose_mode,
    ensure_collection_ready,
    extract_query_context,
    prepare_runtime_context,
    validate_resource_types,
)
from ..retrieve_helpers.multi_theme import execute_multi_theme_retrieval
from ..retrieve_helpers.postprocess import (
    apply_difficulty_filter,
    apply_courseware_teaching_use_filter,
    enforce_specific_theme_precision,
    apply_quantity_limit,
    apply_question_type_filter,
    prioritize_pure_function_results,
)
from ...knowledge_graph import KnowledgeGraph
from ..retrieve_helpers.single_theme import (
    execute_single_theme_retrieval,
    postprocess_single_theme_results,
)
from ..simple_exercise_retrieval import simple_exercise_retrieval

# 教学大纲检索模块（懒加载）
_syllabus_manager = None

def _get_syllabus_manager():
    """懒加载教学大纲管理器"""
    global _syllabus_manager
    if _syllabus_manager is None:
        from ...syllabus_manager import syllabus_manager
        _syllabus_manager = syllabus_manager
    return _syllabus_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# 宽泛主题定义（四大板块）
# ============================================

# 1. 函数与代数板块
# 注意：具体的函数类型（如指数函数、对数函数等）不应视为宽泛主题
# 只有真正的通用概念（如"函数"、"函数图像"、"函数性质"）才是宽泛主题
BROAD_TOPICS_FUNCTION = {
    "函数", "函数图像", "函数性质", "单调性", "奇偶性",
    "周期性", "最值", "值域", "定义域"
}

# 2. 立体几何板块
BROAD_TOPICS_GEOMETRY = {
    "立体几何", "空间几何", "棱柱", "棱锥", "圆柱", "圆锥",
    "球", "正方体", "长方体", "空间直线", "空间平面",
    "线线垂直", "线面垂直", "面面垂直", "线线平行",
    "线面平行", "面面平行", "表面积", "体积"
}

# 3. 概率统计板块（已添加排列组合、各种事件）
BROAD_TOPICS_STATISTICS = {
    "概率", "统计", "抽样", "分层抽样", "简单随机抽样",
    "系统抽样", "古典概型", "几何概型", "概率分布",
    "期望", "方差", "标准差", "回归分析", "相关系数",
    "排列组合", "排列", "组合", "二项式定理",
    "事件", "互斥事件", "对立事件", "独立事件", "必然事件", "随机事件"
}

# 4. 其他数学板块
BROAD_TOPICS_OTHER = {
    "数列", "等差数列", "等比数列", "递推数列",
    "不等式", "均值不等式", "线性规划",
    "方程", "一元二次方程", "方程组",
    "向量", "平面向量", "空间向量",
    "复数", "导数", "积分", "极限"
}

# 合并所有宽泛主题
BROAD_TOPICS = set().union(
    BROAD_TOPICS_FUNCTION,
    BROAD_TOPICS_GEOMETRY,
    BROAD_TOPICS_STATISTICS,
    BROAD_TOPICS_OTHER
)

def is_broad_topic(theme: str) -> bool:
    """
    判断是否为宽泛主题
    
    Args:
        theme: 主题字符串
        
    Returns:
        True如果是宽泛主题，False否则
    """
    if not theme:
        return False
    
    # 方法1：直接匹配宽泛主题集合
    if theme in BROAD_TOPICS:
        return True
    
    # 方法2：主题长度较短（通常是宽泛概念）
    if len(theme) <= 4:
        return True
    
    return False

def get_scoring_weights(theme: str) -> dict:
    """
    根据主题类型返回不同的评分权重
    
    Args:
        theme: 主题字符串
        
    Returns:
        评分权重字典
    """
    if is_broad_topic(theme):
        # 宽泛主题：平衡评分，适当提高LLM权重
        return {
            'llm': 0.4,
            'kg': 0.35,      # KG权重适中
            'semantic': 0.15, # 语义权重适中
            'quality': 0.1
        }
    else:
        # 具体主题：保持平衡评分
        return {
            'llm': 0.4,
            'kg': 0.3,
            'semantic': 0.2,
            'quality': 0.1
        }

def get_filter_threshold(theme: str) -> dict:
    """
    根据主题类型返回不同的过滤阈值
    
    Args:
        theme: 主题字符串
        
    Returns:
        过滤阈值字典
    """
    if is_broad_topic(theme):
        # 宽泛主题：适度过滤，降低最终分数阈值
        return {
            'kg_threshold': 0.2,           # 降低KG阈值
            'semantic_threshold': 0.25,    # 降低语义阈值
            'final_score_threshold': 0.35  # 【V63.1改进】降低最终分数阈值从0.45到0.35，召回更多相关习题
        }
    else:
        # 具体主题：保持宽松过滤
        return {
            'kg_threshold': 0.1,
            'semantic_threshold': 0.2,
            'final_score_threshold': 0.35  # 【V63.1改进】降低最终分数阈值从0.5到0.35，召回更多相关习题
        }

# ========== 函数类型精确匹配 ==========
# 对于特定函数类型（如正弦函数、余弦函数等），必须精确匹配知识点
FUNCTION_TYPE_MAP = {
    # 三角函数
    "正弦函数": {"正弦", "sin", "正弦函数"},
    "余弦函数": {"余弦", "cos", "余弦函数"},
    "正切函数": {"正切", "tan", "正切函数"},
    "余切函数": {"余切", "cot", "余切函数"},
    "正割函数": {"正割", "sec", "正割函数"},
    "余割函数": {"余割", "csc", "余割函数"},
    "三角函数": {"三角", "trigonometric", "三角函数"},
    
    # 反三角函数
    "反正弦函数": {"反正弦", "arcsin", "反正弦函数"},
    "反余弦函数": {"反余弦", "arccos", "反余弦函数"},
    "反正切函数": {"反正切", "arctan", "反正切函数"},
    "反余切函数": {"反余切", "arccot", "反余切函数"},
    
    # 指数对数函数
    "指数函数": {"指数"},
    "对数函数": {"对数"},
    "幂函数": {"幂函数"},
    
    # 初等函数
    "一次函数": {"一次函数", "线性函数"},
    "二次函数": {"二次函数", "抛物线"},
    "反比例函数": {"反比例函数"},
    "正比例函数": {"正比例函数"},
    
    # 特殊函数
    "分段函数": {"分段函数"},
    "复合函数": {"复合函数"},
    "周期函数": {"周期函数"},
    "奇函数": {"奇函数", "奇性"},
    "偶函数": {"偶函数", "偶性"},
}

# 函数类型层级关系（父类别包含子类别）
FUNCTION_TYPE_HIERARCHY = {
    # 三角函数包含所有三角函数和反三角函数
    "三角函数": ["正弦函数", "余弦函数", "正切函数", "余切函数", "正割函数", "余割函数", 
                "反正弦函数", "反余弦函数", "反正切函数", "反余切函数"],
    
    # 指数对数函数包含指数、对数、幂函数
    "指数对数函数": ["指数函数", "对数函数", "幂函数"],
    
    # 初等函数包含基本初等函数
    "初等函数": ["一次函数", "二次函数", "反比例函数", "正比例函数",
                "指数函数", "对数函数", "幂函数", "三角函数"],
    
    # 特殊函数包含具有特殊性质的函数
    "特殊函数": ["分段函数", "复合函数", "周期函数", "奇函数", "偶函数"],
}

def filter_by_function_type(results: list, core_theme: str) -> list:
    """
    根据函数类型精确过滤结果
    
    Args:
        results: 检索结果列表
        core_theme: 核心主题
        
    Returns:
        过滤后的结果列表
    """
    # 检查是否是特定函数类型查询
    target_function_type = None
    if isinstance(core_theme, str):
        for func_type, keywords in FUNCTION_TYPE_MAP.items():
            if func_type in core_theme:
                target_function_type = func_type
                break
    
    if not target_function_type:
        return results
    
    # 获取期望的关键词（支持层级关系）
    expected_keywords = set(FUNCTION_TYPE_MAP[target_function_type])
    
    # 如果是父类别，添加所有子类别的关键词
    if target_function_type in FUNCTION_TYPE_HIERARCHY:
        for child_type in FUNCTION_TYPE_HIERARCHY[target_function_type]:
            if child_type in FUNCTION_TYPE_MAP:
                expected_keywords.update(FUNCTION_TYPE_MAP[child_type])
    
    filtered_results = []
    excluded_count = 0
    
    for r in results:
        # 根据结果类型获取元数据
        if isinstance(r, dict):
            meta = r.get('metadata', r)
        else:
            # 如果是向量数据库返回的结果格式
            meta = r
        
        # 检查所有可能的匹配字段（知识点 + 标题）
        match_candidates = []
        
        # 字段1: 知识点
        if '知识点' in meta:
            match_candidates.append(str(meta['知识点']))
        
        # 字段2: 知识点标签
        if '知识点标签' in meta:
            match_candidates.append(str(meta['知识点标签']))
        
        # 字段3: analysis 中的知识点
        if 'analysis' in meta and isinstance(meta['analysis'], dict):
            if '知识点' in meta['analysis']:
                match_candidates.append(str(meta['analysis']['知识点']))
        
        # 字段4: 标题（增加标题检查，确保标题中包含函数类型的资源不会被误过滤）
        if 'title' in meta:
            match_candidates.append(str(meta['title']))
        
        # 字段5: 文档内容（作为最后检查）
        if 'document' in meta:
            match_candidates.append(str(meta['document']))
        
        # 合并所有匹配候选
        match_str = ';'.join([k for k in match_candidates if k])
        
        # 必须包含至少一个期望的关键词
        has_match = any(kw in match_str for kw in expected_keywords)
        
        if has_match:
            filtered_results.append(r)
        else:
            excluded_count += 1
    
    logger.warning(
        f"[函数类型过滤] target_function_type='{target_function_type}', "
        f"期望关键词={expected_keywords}, "
        f"原始结果数={len(results)}, 过滤后={len(filtered_results)}, 排除={excluded_count}"
    )
    
    return filtered_results


def filter_exercise_by_core_theme_relevance(results: list, core_theme: str) -> list:
    """
    【V63.5改进】习题专用过滤：确保返回的题目与核心主题真正相关
    
    问题背景：查询变体可能包含过于宽泛的术语（如"函数应用"），导致召回与核心主题无关的题目。
    解决方案：
    1. 识别主要关键词（如"指数函数"）和次要关键词（如"函数应用"）
    2. 对于高分题目（>=0.5），要求必须包含主要关键词
    3. 对于低分题目，可以只包含次要关键词
    
    Args:
        results: 检索结果列表
        core_theme: 核心主题（如"指数函数"）
        
    Returns:
        过滤后的结果列表
    """
    if not results or not core_theme:
        return results
    
    # 【V63.5改进】提取主要关键词和次要关键词
    primary_keywords = set()  # 主要关键词（如"指数函数"）
    secondary_keywords = set()  # 次要关键词（如"函数应用"）
    
    if isinstance(core_theme, str):
        # 先按逗号拆分（如"指数函数,函数性质"），再按空格拆分
        parts = []
        for part in core_theme.split(','):
            parts.extend(part.split())
        
        for kw in parts:
            kw = kw.strip()  # 去除前后空格
            if len(kw) >= 2:  # 至少2个字符
                # 【V63.5改进】判断是否为主要关键词
                # 主要关键词特征：
                # 1. 包含具体数学概念（如"指数函数"、"对数函数"等）
                # 2. 或者是查询的第一个关键词（通常是用户最关心的）
                is_primary = False
                
                # 规则1：检查是否包含具体数学概念
                math_concepts = [
                    '指数函数', '对数函数', '幂函数', '三角函数', '二次函数', '一次函数',
                    '正弦函数', '余弦函数', '正切函数', '反比例函数', '等差数列', '等比数列',
                    '向量', '概率', '统计', '导数', '积分', '极限', '集合', '不等式',
                    '方程', '圆', '椭圆', '抛物线', '双曲线', '立体几何', '平面几何'
                ]
                if any(term in kw for term in math_concepts):
                    is_primary = True
                
                # 规则2：如果是第一个关键词，且长度>=4，也视为主要关键词
                if not is_primary and len(parts) > 0 and kw == parts[0].strip() and len(kw) >= 4:
                    is_primary = True
                
                if is_primary:
                    primary_keywords.add(kw)
                else:
                    secondary_keywords.add(kw)
    
    # 如果没有主要关键词，则所有关键词都视为主要关键词
    if not primary_keywords:
        primary_keywords = secondary_keywords.copy()
        secondary_keywords.clear()
    
    all_keywords = primary_keywords | secondary_keywords
    
    if not all_keywords:
        return results
    
    logger.warning(f"[V63.5核心主题相关性过滤] core_theme='{core_theme}', primary_keywords={primary_keywords}, secondary_keywords={secondary_keywords}")
    
    filtered_results = []
    excluded_count = 0
    
    # 【V67.0改进】如果主要关键词数量 >= 2，说明是“A的B”结构（如分段函数的单调性）
    # 此时要求题目必须同时包含所有主要关键词，缺一不可
    is_multi_dimension_query = len(primary_keywords) >= 2
    
    # 【V70.0通用版】多维度语义对齐策略：适用于所有“A的B”类组合查询
    # 定义常见的数学属性及其同义词
    MATH_ATTRIBUTES = {
        "单调性": ["单调", "递增", "递减", "增减", "变化趋势", "上升", "下降"],
        "最值": ["最值", "最大值", "最小值", "极值", "峰值", "谷值"],
        "奇偶性": ["奇偶", "奇函数", "偶函数", "对称", "中心对称", "轴对称"],
        "周期性": ["周期", "重复", "循环"],
        "零点": ["零点", "根", "交点", "解"],
        "定义域": ["定义域", "有意义", "取值范围"],
        "图像": ["图像", "图象", "图形", "形状", "走势"]
    }
    
    # 自动识别查询中的“对象”和“属性”
    query_objects = []
    query_attributes = []
    
    # 【V65.0改进】定义非对象的关键词（任务、操作、场景等），这些不应被视为数学对象
    NON_OBJECT_KEYWORDS = [
        "判断", "计算", "求解", "证明", "分析", "应用", "比较", "选择",
        "区间", "范围", "定义域", "值域", "取值", "存在", "恒成立"
    ]
    
    if isinstance(core_theme, str):
        parts = [p.strip() for p in core_theme.replace(',', ' ').split() if len(p.strip()) >= 2]
        for part in parts:
            # 检查是否是已知属性
            is_attr = False
            for attr_name, synonyms in MATH_ATTRIBUTES.items():
                if part == attr_name or any(syn in part for syn in synonyms):
                    query_attributes.append(part)
                    is_attr = True
                    break
            # 【V65.0改进】如果不是属性，且包含非对象关键词，则跳过（不作为对象）
            if not is_attr:
                is_non_object = any(nok in part for nok in NON_OBJECT_KEYWORDS)
                if not is_non_object:
                    query_objects.append(part)
    
    # 如果识别出了明确的对象和属性组合（至少1个对象+1个属性），启动深度校验
    is_multi_dimension_query_v2 = len(query_objects) > 0 and len(query_attributes) > 0
    
    logger.warning(f"[V70.0-通用] 识别到对象: {query_objects}, 属性: {query_attributes}")
    
    for r in results:
        meta = r.get('metadata', {})
        title = meta.get('title', '')
        
        # 尝试多个可能的知识点字段
        knowledge_points = (
            meta.get('知识点', '') or 
            meta.get('knowledge_points', '') or 
            r.get('知识点', '') or 
            r.get('knowledge_points', '') or
            ''
        )
        
        # 获取分析数据（用于深度校验）
        analysis_json = meta.get('analysis_json', '')
        full_analysis = f"{title};{knowledge_points};{analysis_json}"
        
        # 构建匹配候选字符串（标题 + 知识点 + analysis字段）
        match_str = f"{title};{knowledge_points}"
        
        # 【V65.2改进】对于组合查询，尝试将知识点拆分后分别匹配
        # 例如："函数单调性的区间判断" -> ["函数单调性", "区间判断"]
        expanded_keywords = set()
        for kw in primary_keywords:
            expanded_keywords.add(kw)
            # 如果关键词包含"的"，尝试拆分
            if '的' in kw and len(kw) > 4:
                parts_of_kw = kw.split('的')
                for part in parts_of_kw:
                    if len(part.strip()) >= 2:
                        expanded_keywords.add(part.strip())
        
        # 检查是否包含主要关键词（使用扩展后的关键词集）
        has_primary_keyword = any(kw in match_str for kw in expanded_keywords)
        # V67.0: 检查是否包含**所有**主要关键词
        has_all_primary_keywords = all(kw in match_str for kw in primary_keywords) if is_multi_dimension_query else has_primary_keyword
        # 检查是否包含任何关键词
        has_any_keyword = any(kw in match_str for kw in all_keywords)
        
        final_score = r.get('_final_score', 0)
        
        # V70.0: 通用多维度深度语义对齐
        if is_multi_dimension_query_v2:
            # 必须同时包含“对象”特征和“属性”描述
            has_object_feature = any(obj in full_analysis for obj in query_objects)
            has_attribute_desc = False
            for attr in query_attributes:
                # 查找该属性对应的所有同义词
                attr_synonyms = []
                for attr_name, syns in MATH_ATTRIBUTES.items():
                    if attr == attr_name or any(syn in attr for syn in syns):
                        attr_synonyms.extend(syns)
                        attr_synonyms.append(attr_name)
                if any(syn in full_analysis for syn in attr_synonyms):
                    has_attribute_desc = True
                    break
            
            if not has_object_feature:
                excluded_count += 1
                logger.warning(f"[V70.0-维度] 资源 '{title[:40]}' 缺少对象特征{query_objects}，强制剔除")
                continue
            elif not has_attribute_desc:
                excluded_count += 1
                logger.warning(f"[V70.0-维度] 资源 '{title[:40]}' 虽含对象但未讨论属性{query_attributes}，剔除")
                continue
            # 如果都满足，视为高度相关，直接进入
            filtered_results.append(r)
            continue

        if has_all_primary_keywords:
            # V67.0: 对于多维度查询，必须全部命中才保留
            filtered_results.append(r)
        elif not is_multi_dimension_query and has_primary_keyword:
            # 单维度查询：包含主要关键词，保留
            filtered_results.append(r)
        elif not is_multi_dimension_query and has_any_keyword and final_score < 0.5:
            # 单维度查询：只包含次要关键词且分数较低，保留（可能是边缘相关）
            filtered_results.append(r)
        else:
            # 排除
            excluded_count += 1
            reason = "不包含所有主要关键词" if is_multi_dimension_query else f"不包含主要关键词{primary_keywords}"
            logger.warning(
                f"[V63.5核心主题相关性过滤] 排除不相关题目: title='{title[:40]}', "
                f"kp='{knowledge_points[:40]}', final_score={final_score:.3f}, "
                f"has_primary={has_primary_keyword}, has_all_primary={has_all_primary_keywords}, has_any={has_any_keyword}, "
                f"原因：{reason}"
            )
    
    logger.warning(
        f"[V63.5核心主题相关性过滤] 原始结果数={len(results)}, "
        f"过滤后={len(filtered_results)}, 排除={excluded_count}"
    )
    
    return filtered_results


def sort_exercises_by_title_relevance(results: list, core_theme: str) -> list:
    """
    【V63.5改进】习题专用排序优化：让专门针对核心主题的题目排在前面
    
    问题背景：有些题目虽然与核心主题相关，但不是专门针对该主题的题目（如“不同函数增长的差异”包含指数函数，但主题是多种函数比较）。
    解决方案：
    1. 识别主要关键词（如"指数函数"）和次要关键词（如"函数应用"）
    2. 标题包含主要关键词时给予更高的加分
    3. 知识点包含主要关键词时也给予加分
    
    Args:
        results: 检索结果列表
        core_theme: 核心主题（如"指数函数"）
        
    Returns:
        重新排序后的结果列表
    """
    if not results or not core_theme or len(results) <= 1:
        return results
    
    logger.warning(f"[V63.6排序优化] core_theme='{core_theme}', 原始结果数={len(results)}")
    
    # 【V63.5改进】提取主要关键词和次要关键词
    primary_keywords = set()
    secondary_keywords = set()
    
    if isinstance(core_theme, str):
        parts = []
        for part in core_theme.split(','):
            parts.extend(part.split())
        
        for kw in parts:
            kw = kw.strip()
            if len(kw) >= 2:
                # 【V63.5改进】判断是否为主要关键词（与过滤函数保持一致）
                is_primary = False
                
                # 规则1：检查是否包含具体数学概念
                math_concepts = [
                    '指数函数', '对数函数', '幂函数', '三角函数', '二次函数', '一次函数',
                    '正弦函数', '余弦函数', '正切函数', '反比例函数', '等差数列', '等比数列',
                    '向量', '概率', '统计', '导数', '积分', '极限', '集合', '不等式',
                    '方程', '圆', '椭圆', '抛物线', '双曲线', '立体几何', '平面几何'
                ]
                if any(term in kw for term in math_concepts):
                    is_primary = True
                
                # 规则2：如果是第一个关键词，且长度>=4，也视为主要关键词
                if not is_primary and len(parts) > 0 and kw == parts[0].strip() and len(kw) >= 4:
                    is_primary = True
                
                if is_primary:
                    primary_keywords.add(kw)
                else:
                    secondary_keywords.add(kw)
    
    if not primary_keywords:
        primary_keywords = secondary_keywords.copy()
        secondary_keywords.clear()
    
    all_keywords = list(primary_keywords | secondary_keywords)
    
    logger.warning(f"[V63.6排序优化] primary_keywords={primary_keywords}, secondary_keywords={secondary_keywords}")
    
    # 为每个题目计算标题相关度分数
    scored_results = []
    for r in results:
        meta = r.get('metadata', {})
        title = meta.get('title', '')
        
        # 尝试多个可能的知识点字段
        knowledge_points = (
            meta.get('知识点', '') or 
            meta.get('knowledge_points', '') or 
            r.get('知识点', '') or 
            r.get('knowledge_points', '') or
            ''
        )
        final_score = r.get('_final_score', 0)
        
        # 基础分数：使用原有的final_score
        base_score = final_score
        
        # 【V63.6改进】标题相关度加分
        title_bonus = 0.0
        
        # 策略1：检查标题是否完全包含核心主题（针对单一关键词的情况）
        if core_theme in title and ',' not in core_theme:
            title_bonus += 0.25  # 【V63.6提高权重】从0.20提高到0.25
            logger.warning(f"[V63.6排序优化] title='{title[:40]}' 完全包含'{core_theme}'，+0.25分")
        else:
            # 策略2：检查标题是否包含主要关键词（即使core_theme包含逗号）
            matched_primary = [kw for kw in primary_keywords if kw in title]
            if matched_primary:
                # 【V63.6改进】如果标题包含所有主要关键词，给予更高分
                if len(matched_primary) == len(primary_keywords):
                    title_bonus += 0.20 * len(matched_primary)  # 包含所有主要关键词，+0.20/个
                    logger.warning(f"[V63.6排序优化] title='{title[:40]}' 包含所有主要关键词{matched_primary}，+{0.20 * len(matched_primary):.2f}分")
                else:
                    title_bonus += 0.15 * len(matched_primary)  # 包含部分主要关键词，+0.15/个
                    logger.warning(f"[V63.6排序优化] title='{title[:40]}' 匹配主要关键词{matched_primary}，+{0.15 * len(matched_primary):.2f}分")
            else:
                # 策略3：检查标题是否包含次要关键词
                matched_secondary = [kw for kw in secondary_keywords if kw in title]
                if matched_secondary:
                    title_bonus += 0.05 * len(matched_secondary)  # 次要关键词加分较少
                    logger.warning(f"[V63.6排序优化] title='{title[:40]}' 匹配次要关键词{matched_secondary}，+{0.05 * len(matched_secondary):.2f}分")
        
        # 【V63.6改进】知识点相关度加分
        kp_bonus = 0.0
        matched_kp_primary = [kw for kw in primary_keywords if kw in knowledge_points]
        if matched_kp_primary:
            kp_bonus += 0.10 * len(matched_kp_primary)  # 【V63.6提高权重】从0.08提高到0.10
            logger.warning(f"[V63.6排序优化] kp匹配主要关键词{matched_kp_primary}，+{0.10 * len(matched_kp_primary):.2f}分")
        else:
            matched_kp_secondary = [kw for kw in secondary_keywords if kw in knowledge_points]
            if matched_kp_secondary:
                kp_bonus += 0.03 * len(matched_kp_secondary)  # 次要关键词加分较少
        
        # 最终分数 = 基础分数 + 标题加分 + 知识点加分
        adjusted_score = base_score + title_bonus + kp_bonus
        
        scored_results.append((r, adjusted_score, base_score, title_bonus, kp_bonus))
    
    # 按调整后的分数降序排序
    scored_results.sort(key=lambda x: -x[1])
    
    # 【V70.1改进】取消多样性限制：完全基于相关性排序，允许同一文件的高分题目集中展示
    # 只要题目符合查询意图且分数高，无论来自哪个文件都应优先展示
    
    # 输出排序结果
    logger.warning(f"[V63.6排序优化] ===== 排序结果 =====")
    for i, (r, adjusted_score, base_score, title_bonus, kp_bonus) in enumerate(scored_results):
        meta = r.get('metadata', {})
        title = meta.get('title', '')
        logger.warning(
            f"[V63.6排序优化]   [{i+1}] title='{title[:40]}', "
            f"base_score={base_score:.3f}, title_bonus={title_bonus:.2f}, kp_bonus={kp_bonus:.2f}, "
            f"adjusted_score={adjusted_score:.3f}"
        )
    
    # 返回重新排序后的结果
    sorted_results = [r for r, _, _, _, _ in scored_results]
    
    logger.warning(f"[V63.6排序优化] 排序完成")
    
    return sorted_results


from .check_theme_relevance_with_llm import _CheckThemeRelevanceWithLlmMixin


class _RetrieveMixin(_CheckThemeRelevanceWithLlmMixin):
    def __init__(self):
        super().__init__()
        self.kg = KnowledgeGraph()  # 知识图谱实例
    
    def _execute_syllabus_retrieval(self, query):
        """
        执行简化的教学大纲检索
        """
        try:
            logger.info(f"🔍 教学大纲检索: {query}")
            
            # 使用教学大纲管理器检索
            syllabus_manager = _get_syllabus_manager()
            
            # 获取带分数的匹配结果（用于保持正确排序）
            scored_candidates = syllabus_manager._keyword_match(query)
            
            if scored_candidates:
                # 获取最高分用于归一化
                max_score = max(score for _, score in scored_candidates)
                # 获取按分数排序的章节键（复合键）
                candidates = [chapter_key for chapter_key, _ in scored_candidates]
                results = []
                for chapter_key in candidates[:5]:
                    if chapter_key in syllabus_manager.chapters:
                        data = syllabus_manager.chapters[chapter_key]
                        # 使用存储的章节名称（而不是复合键）
                        chapter_name = data.get('chapter', chapter_key)
                        results.append({
                            'chapter': chapter_name,
                            'content': data['content'],
                            'filename': data['filename'],
                            'topic': data['topic'],
                            'score': next(s for c, s in scored_candidates if c == chapter_key)
                        })
            else:
                # 如果没有匹配，返回所有章节（按名称排序）
                candidates = sorted(list(syllabus_manager.chapters.keys()))[:5]
                results = []
                for chapter_key in candidates:
                    data = syllabus_manager.chapters[chapter_key]
                    # 使用存储的章节名称（而不是复合键）
                    chapter_name = data.get('chapter', chapter_key)
                    results.append({
                        'chapter': chapter_name,
                        'content': data['content'],
                        'filename': data['filename'],
                        'topic': data['topic'],
                        'score': 0
                    })
            
            logger.info(f"✅ 教学大纲检索完成，找到 {len(results)} 条结果")
            
            # 获取最高分用于归一化
            max_score = max(item['score'] for item in results) if results else 1
            
            # 转换为统一的资源格式（与 _get_empty_result 格式一致）
            formatted_results = []
            for idx, item in enumerate(results):
                chapter_name = item['chapter']
                topic_name = item['topic']
                # 根据匹配分数设置相关性（保留原始排序）
                relevance = item['score'] / max_score if max_score > 0 else 0.0
                
                # 检查是否是最高分（并列第一）
                is_top_score = item['score'] == max_score if max_score > 0 else idx == 0
                
                # 对于教学大纲资源，使用查询词作为匹配主题，确保同一主题的资源被分到同一组
                # 这样在 filter_by_relevance 中，相关的教学大纲资源能获得公平的展示机会
                matched_themes_for_syllabus = [query] if query else [chapter_name]
                
                formatted_results.append({
                    'id': f"syllabus_{topic_name}_{chapter_name}",  # 添加唯一ID，用于去重和分组
                    'resource_type': 'syllabus',
                    'title': f"教学大纲: {chapter_name}",
                    'content': item['content'],
                    'filename': item['filename'],
                    'source': item['filename'],  # 添加source字段用于显示文件路径
                    'matched_keywords': [chapter_name],
                    'score': item['score'],  # 保留原始匹配分数
                    'is_core_match': is_top_score,  # 最高分的都是核心匹配
                    'core_theme': f"{topic_name}_{chapter_name}",  # 使用主题+章节作为核心主题
                    'topic': topic_name,  # 添加主题字段
                    'chapter': chapter_name,  # 添加章节字段
                    'matched_themes': matched_themes_for_syllabus,  # 使用查询词作为匹配主题，确保相关资源分到同一组
                    'match_level': 'exact' if is_top_score else 'related',  # 最高分的是精确匹配
                    'priority_level': 4 if is_top_score else 3,  # 最高分的是核心匹配(4)
                    'priority_name': '核心主题匹配' if is_top_score else '相关主题匹配',
                    'relevance': relevance,  # 根据匹配分数设置相关性
                    'overall_score': relevance,  # 根据匹配分数设置综合得分
                    'final_score': relevance,  # 添加最终得分，避免被统一决策中心重新计算
                    'resource_quality': 1.0,  # 添加资源质量评分
                    'content_completeness': 1.0,  # 添加内容完整性评分
                    'teaching_value': 1.0,  # 添加教学价值评分
                    'matched_theme_count': 1,  # 添加匹配主题数
                    'meta': {'title': f"教学大纲: {chapter_name}", 'topic': topic_name},  # 添加meta字段用于调试输出
                })
            
            # 构建返回结果（与 _get_empty_result 格式一致）
            return {
                "theory_resources": [],
                "lesson_plan_patterns": [],
                "exercise_resources": [],
                "visualization_examples": [],
                "general_resources": [],
                "courseware_resources": [],
                "lesson_case_resources": [],
                "ggb_resources": [],
                "syllabus_resources": formatted_results,
                "_hidden_resources": [],
                "_hidden_count": 0,
                "_total_count": len(formatted_results)
            }
        
        except Exception as e:
            logger.error(f"教学大纲检索失败: {e}")
            return self._get_empty_result()
    
    def _execute_simple_exercise_retrieval(self, query, core_theme, n_results, resource_types, difficulty, question_type):
        """
        执行简化的习题检索
        """
        try:
            from app.core.model_config import model_config
            
            # 使用服务器已有的ChromaDB客户端实例，避免重复创建
            vector_db = model_config.get_chroma_client()
            
            # 设置默认返回数量
            if n_results is None:
                n_results = 50  # 【V102.0优化】从10增加到50，提高召回率
            
            # 执行简化检索
            results = simple_exercise_retrieval(
                query=query,
                core_theme=core_theme,
                vector_db=vector_db,
                n_results=n_results,
                resource_types=resource_types,
                difficulty=difficulty,
                question_type=question_type
            )
            
            # 【V65.2新增】为习题结果添加图片URL字段
            from app.core.retrieval.methods.process_exercise_resource import _ProcessExerciseResourceMixin
            
            logger.info(f"[V65.2图片调试] 开始处理 {len(results)} 条习题结果的图片URL")
            
            # 创建临时对象来调用图片URL解析方法
            class TempProcessor(_ProcessExerciseResourceMixin):
                def __init__(self):
                    pass
            
            processor = TempProcessor()
            
            for idx, result in enumerate(results):
                metadata = result.get('metadata', {})
                if metadata:
                    # 创建一个临时的resource字典
                    temp_resource = {}
                    try:
                        processor._process_exercise_resource(temp_resource, metadata)
                        
                        # 将结构化字段添加到 result 中（供前端 ExerciseCard 渲染）
                        result['question'] = temp_resource.get('question', '')
                        result['answer'] = temp_resource.get('answer', '')
                        result['question_type'] = temp_resource.get('question_type', '')
                        result['knowledge_tags'] = temp_resource.get('knowledge_tags', '')
                        result['difficulty'] = temp_resource.get('difficulty', '')
                        result['usage_scene'] = temp_resource.get('usage_scene', '')
                        result['question_image_url'] = temp_resource.get('question_image_url', '')
                        result['answer_image_url'] = temp_resource.get('answer_image_url', '')
                        result['has_question_image'] = temp_resource.get('has_question_image', False)
                        result['has_answer_image'] = temp_resource.get('has_answer_image', False)
                        result['question_format'] = temp_resource.get('question_format', 'text')
                        result['answer_format'] = temp_resource.get('answer_format', 'text')
                        result['is_image_exercise'] = temp_resource.get('is_image_exercise', False)
                        
                        # 【V65.2调试】记录图片URL信息
                        title = metadata.get('title', '')
                        filename = metadata.get('题目文件名', '')
                        question_img = result.get('question_image_url', '')
                        answer_img = result.get('answer_image_url', '')
                        
                        # 【V65.3调试】记录question字段
                        question = result.get('question', '')
                        logger.info(f"[V65.3调试] [{idx+1}] title='{title}', question_length={len(question)}, question_preview='{question[:50] if question else '空'}'")
                        
                        if filename or question_img or answer_img:
                            logger.info(f"[V65.2图片调试] [{idx+1}] 习题: {title}, 文件名: {filename}, 题目图片: {question_img[:80] if question_img else '无'}, 答案图片: {answer_img[:80] if answer_img else '无'}")
                    except Exception as e:
                        logger.error(f"[V65.2图片调试] 处理第{idx+1}条习题时出错: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"简化习题检索失败: {e}")
            return []
    
    def retrieve(
        self,
        query: str,
        intent: str = "search",
        n_results: int = None,
        resource_types: List[str] = None,
        quantity_limit: Optional[int] = None,
        grade_info: Optional[Dict[str, Any]] = None,
        clarified_topic: Optional[Dict[str, Any]] = None,
        difficulty_info: Optional[Dict[str, Any]] = None,
        courseware_teaching_use: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        根据查询和意图检索相关资源

        Args:
            query: 用户查询
            intent: 用户意图
            n_results: 返回结果数量，默认为50
            resource_types: 用户明确提到的资源类型列表（用于精准检索）
            quantity_limit: V33.0 数量限制
            grade_info: V33.0 年级信息
            clarified_topic: V33.0 澄清后的主题信息
            difficulty_info: V33.0 难度信息

        Returns:
            检索结果字典，包含各类资源
        """
        try:
            # ========== 语义匹配调试 - 方法入口 ==========
            logger.info("=" * 70)
            logger.info("=== 知识图谱增强检索 ===")
            # 使用知识图谱扩展查询
            expanded_query = self.kg.expand_query(query)
            related_concepts = self.kg.get_related_nodes(query)
            logger.info(f"原始查询: {query}")
            logger.info(f"扩展查询: {expanded_query}")
            logger.info(f"相关概念: {related_concepts}")
            # 使用扩展查询进行检索
            self._current_query = expanded_query
            logger.info("=== 语义匹配调试 - retrieve() 方法被调用 ===")
            logger.info("=" * 70)
            logger.info(f"查询: {query}")
            logger.info(f"意图: {intent}")
            logger.info(f"资源类型: {resource_types}")
            logger.info(f"数量限制: {quantity_limit}")
            logger.info(f"年级信息: {grade_info}")
            logger.info(f"主题澄清: {clarified_topic}")
            logger.info(f"难度信息: {difficulty_info}")
            logger.info("=" * 70)

            self._current_query = query
            resource_types, early_result = validate_resource_types(self, resource_types)
            logger.info(f"V100.0调试 - validate_resource_types返回: resource_types={resource_types}, early_result={early_result}")
            if early_result is not None:
                logger.info("V100.0调试 - 从validate_resource_types返回early_result")
                return early_result

            # ========== 教学大纲特殊处理 ==========
            # 如果是教学大纲检索，使用简化的检索流程
            is_syllabus_query = False
            if resource_types:
                resource_types_lower = [rt.lower() for rt in resource_types]
                if any(rt in ["syllabus", "教学大纲", "课程标准", "教学计划"] for rt in resource_types_lower):
                    is_syllabus_query = True
            
            # 也通过查询词判断
            if not is_syllabus_query:
                syllabus_keywords = ["教学大纲", "课程标准", "教学计划", "教学要求", "学业要求"]
                if any(kw in query for kw in syllabus_keywords):
                    is_syllabus_query = True
            
            if is_syllabus_query:
                logger.info("V100.1调试 - 检测到教学大纲检索，使用简化检索方法")
                return self._execute_syllabus_retrieval(query)

            quantity_limit = apply_loose_mode(self, query, quantity_limit)
            prepare_runtime_context(
                self,
                query,
                quantity_limit,
                grade_info,
                clarified_topic,
                difficulty_info,
            )

            # 先提取查询上下文，获取core_theme
            query_context, early_result = extract_query_context(self, query, quantity_limit)
            if early_result is not None:
                return early_result

            core_theme = query_context["core_theme"]
            core_themes = query_context.get("core_themes", [])

            # 调试：打印 core_theme 和 core_themes 的类型和值
            logger.info(f"V101.0调试 - core_theme类型: {type(core_theme)}, 值: {core_theme}")
            logger.info(f"V101.1调试 - core_themes类型: {type(core_themes)}, 值: {core_themes}")

            # 如果 core_theme 是元组（来自 _extract_core_theme），需要处理
            if isinstance(core_theme, tuple) and len(core_theme) == 2:
                theme_str, board_from_tuple = core_theme
                logger.info(f"V101.2调试 - 检测到 core_theme 是元组，theme_str: {theme_str}, board_from_tuple: {board_from_tuple}")
                # 将逗号分隔的主题字符串拆分为列表
                if isinstance(theme_str, str) and "," in theme_str:
                    core_themes = [t.strip() for t in theme_str.split(",") if t.strip()]
                    logger.info(f"V101.3调试 - 拆分后的 core_themes: {core_themes}")
                elif isinstance(theme_str, str):
                    core_themes = [theme_str]
                    logger.info(f"V101.4调试 - 单个主题的 core_themes: {core_themes}")

            question_type = query_context["question_type"]
            difficulty = query_context["difficulty"]
            grade = query_context["grade"]
            exam_form = query_context["exam_form"]
            quantity_limit = query_context["quantity_limit"]
            board = query_context.get("board")
            content_requirement = query_context.get("content_requirement", False)

            # 【V107.0调试】打印LLM识别的难度
            logger.info(f"[V107.0] LLM识别结果 - difficulty: '{difficulty}', core_themes: {core_themes}, board: {board}")
            print(f"[V107.0调试] difficulty = '{difficulty}'")

            # 将content_requirement设置到_current_query_features中，供collect.py使用
            self._current_query_features["content_requirement"] = content_requirement
            logger.info(f"V200.0调试 - content_requirement: {content_requirement}")

            logger.info(f"V102.0调试 - 最终 core_themes: {core_themes}, len(core_themes): {len(core_themes)}, board: '{board}'")

            # 现在使用core_theme和board调用ensure_collection_ready
            collection, early_result = ensure_collection_ready(self, core_theme, board)
            if early_result is not None:
                return early_result

            # 提取查询条件
            query_conditions = {}
            if hasattr(self, '_extract_query_conditions'):
                logger.info(f"[语义匹配调试] 调用 _extract_query_conditions，查询: '{query}'")
                query_conditions = self._extract_query_conditions(query)
                requirements = query_conditions.get("requirements", [])
                logger.info(f"[语义匹配调试] 提取到的语义要求: {requirements}")
            else:
                logger.error("[语义匹配调试] _extract_query_conditions 方法不存在")

            logger.info(f"V103.0调试 - 进入判断: len(core_themes) = {len(core_themes)} > 1 = {len(core_themes) > 1}")
            
            # 判断是否是习题检索，如果是则使用简化检索
            is_exercise_query = False
            if resource_types:
                resource_types_lower = [rt.lower() for rt in resource_types]
                if all(rt in ["exercise", "习题", "题目"] for rt in resource_types_lower):
                    is_exercise_query = True
                    logger.info("V103.05调试 - 检测到纯习题检索，使用简化检索方法")
            
            # 【V65.2新增】如果是习题检索，重新提取主题（使用组合查询识别）
            if is_exercise_query and core_theme:
                logger.info("V65.2调试 - 习题检索，重新提取主题以识别组合查询")
                try:
                    re_extracted = self._extract_core_theme(query, is_exercise=True)
                    if isinstance(re_extracted, tuple) and len(re_extracted) == 2:
                        new_theme_str, new_board = re_extracted
                        if new_theme_str and new_theme_str.strip():
                            logger.info(f"V65.2调试 - 重新提取的主题: '{new_theme_str}'")
                            # 更新 core_theme 和 core_themes
                            core_theme = new_theme_str
                            if isinstance(new_theme_str, str) and "," in new_theme_str:
                                core_themes = [t.strip() for t in new_theme_str.split(",") if t.strip()]
                            else:
                                core_themes = [new_theme_str]
                except Exception as e:
                    logger.warning(f"V65.2调试 - 重新提取主题失败: {e}，使用原有主题")
            
            if is_exercise_query:
                # 使用简化的习题检索
                logger.info("V103.06调试 - 调用simple_exercise_retrieval")
                simple_results = self._execute_simple_exercise_retrieval(
                    query,
                    core_theme,
                    n_results,
                    resource_types,
                    difficulty,
                    question_type
                )
                logger.info(f"V103.07调试 - simple_exercise_retrieval返回: {len(simple_results)}条结果")

                # ── 方案A：习题检索跳过 _classify_results，加轻量级知识图谱过滤 ──
                # 用知识图谱扩展 core_theme 的所有后代关键词，
                # 检查习题的 knowledge_points 是否命中其中任意一个。
                # 未命中的习题根据 relevance 降级为隐藏资源，而非直接丢弃。

                # ========== 习题专用辅助函数 ==========
                
                # 定义具体函数类型集合
                SPECIFIC_FUNCTION_TYPES = {
                    "指数函数", "对数函数", "幂函数", 
                    "正弦函数", "余弦函数", "正切函数", "余切函数", "正割函数", "余割函数",
                    "反正弦函数", "反余弦函数", "反正切函数", "反余切函数",
                    "一次函数", "二次函数", "反比例函数", "正比例函数",
                    "分段函数", "复合函数", "周期函数", "奇函数", "偶函数"
                }
                
                # 定义函数性质/应用等通用概念
                FUNCTION_PROPERTIES_AND_APPS = {
                    "单调性", "奇偶性", "周期性", "最值", "值域", "定义域",
                    "函数图像", "函数性质", "函数应用", "函数模型",
                    "指数运算", "对数运算", "三角恒等变换"
                }
                
                def _is_specific_function_query(theme):
                    """判断是否是具体函数类型查询"""
                    if not theme or not isinstance(theme, str):
                        return False
                    # 检查第一个主题（主要主题）
                    first_theme = theme.split(',')[0].strip()
                    return first_theme in SPECIFIC_FUNCTION_TYPES
                
                def _extract_exercise_kg_keywords(core_theme, kg_data):
                    """
                    习题专用的KG关键词提取 - 针对函数板块优化
                    
                    策略：
                    1. 如果是具体函数类型（如"指数函数"），只使用该类型的keywords和直接子节点
                    2. 排除父节点的其他子节点（避免"指数函数"扩展到"对数函数"、"分段函数"等）
                    3. 如果是通用概念（如"函数应用"），可以使用更宽的扩展
                    
                    Args:
                        core_theme: 核心主题
                        kg_data: 知识图谱数据
                    
                    Returns:
                        set: 精简后的关键词集合
                    """
                    if not core_theme or not kg_data:
                        return set()
                    
                    nodes = kg_data.get('nodes', [])
                    is_specific = _is_specific_function_query(core_theme)
                    
                    # 将 core_theme 拆分为独立的子主题列表
                    if isinstance(core_theme, list):
                        theme_parts = core_theme
                    elif isinstance(core_theme, str):
                        theme_parts = [p.strip() for p in core_theme.split(",") if p.strip()]
                    else:
                        theme_parts = []
                    
                    kg_keywords = set()
                    matched_node_ids = set()
                    
                    for theme in theme_parts:
                        if not theme:
                            continue
                        
                        # 查找匹配的节点
                        matched_nodes = []
                        for node in nodes:
                            label = node.get('label', '')
                            keywords = node.get('keywords', [])
                            
                            # 精确匹配label或keyword
                            if theme == label or theme in keywords:
                                matched_nodes.append(node)
                            # 包含匹配（theme在label中或label在theme中）
                            elif theme in label or label in theme:
                                matched_nodes.append(node)
                        
                        for node in matched_nodes:
                            node_id = node['id']
                            if node_id in matched_node_ids:
                                continue
                            matched_node_ids.add(node_id)
                            
                            # 添加当前节点的keywords
                            for kw in node.get('keywords', []):
                                kg_keywords.add(kw)
                            kg_keywords.add(node.get('label', ''))
                            
                            # 如果是具体函数类型，只添加直接子节点，不递归
                            if is_specific:
                                for child in nodes:
                                    if child.get('parent') == node_id:
                                        child_id = child['id']
                                        if child_id not in matched_node_ids:
                                            matched_node_ids.add(child_id)
                                            for kw in child.get('keywords', []):
                                                kg_keywords.add(kw)
                                            kg_keywords.add(child.get('label', ''))
                            else:
                                # 对于通用概念，可以添加所有后代节点
                                def collect_descendants(parent_id, visited):
                                    for child in nodes:
                                        if child.get('parent') == parent_id and child['id'] not in visited:
                                            visited.add(child['id'])
                                            for kw in child.get('keywords', []):
                                                kg_keywords.add(kw)
                                            kg_keywords.add(child.get('label', ''))
                                            collect_descendants(child['id'], visited)
                                
                                visited = {node_id}
                                collect_descendants(node_id, visited)
                    
                    # 添加原始主题
                    for part in theme_parts:
                        if part:
                            kg_keywords.add(part)
                    
                    # 针对具体函数类型，额外添加常见相关术语
                    if is_specific and core_theme:
                        first_theme = core_theme.split(',')[0].strip()
                        additional_terms_map = {
                            "指数函数": [
                                "指数函数模型", "指数增长", "指数衰减",
                                "底数", "指数方程", "指数不等式"
                            ],
                            "对数函数": [
                                "对数函数模型", "对数运算", "换底公式",
                                "对数方程", "对数不等式"
                            ],
                            "幂函数": [
                                "幂函数图像", "幂运算", "幂的性质"
                            ],
                            "三角函数": [
                                "三角函数图像", "诱导公式", "三角恒等变换",
                                "正弦定理", "余弦定理"
                            ],
                            "二次函数": [
                                "二次函数图像", "抛物线", "顶点坐标",
                                "对称轴", "判别式"
                            ]
                        }
                        
                        additional_terms = additional_terms_map.get(first_theme, [])
                        if additional_terms:
                            kg_keywords.update(additional_terms)
                            logger.warning(
                                f"[习题KG优化] 为'{first_theme}'添加了{len(additional_terms)}个额外术语: {additional_terms[:5]}"
                            )
                    
                    logger.warning(
                        f"[习题KG优化] core_theme='{core_theme}', "
                        f"是否具体函数={is_specific}, "
                        f"匹配节点数={len(matched_node_ids)}, "
                        f"关键词数={len(kg_keywords)}, "
                        f"关键词样例={list(kg_keywords)[:10]}"
                    )
                    
                    return kg_keywords, len(matched_node_ids)
                
                def _word_match_enhanced(kp, kw, core_theme, is_specific_function):
                    """
                    增强的知识点匹配 - 考虑函数板块的特殊性
                    
                    Args:
                        kp: 习题的知识点
                        kw: KG扩展的关键词
                        core_theme: 查询的核心主题
                        is_specific_function: 是否是具体函数类型查询
                    
                    Returns:
                        bool: 是否匹配
                    """
                    if not kp or not kw:
                        return False
                    
                    # 1. 精确相等 → 直接匹配
                    if kp == kw:
                        return True
                    
                    # 2. 短词保护：至少3个字符
                    if len(kp) < 3 or len(kw) < 3:
                        return False
                    
                    # 3. 如果是具体函数类型查询，需要额外检查同级函数类型
                    if is_specific_function:
                        # 提取当前查询的函数类型名称（去掉"函数"后缀）
                        base_function = core_theme.replace("函数", "").strip()
                        
                        # 定义其他函数类型关键词
                        other_function_keywords = [
                            "对数", "幂", "正弦", "余弦", "正切", "余切", "正割", "余割",
                            "分段", "一次", "二次", "反比例", "正比例",
                            "复合", "周期", "奇函数", "偶函数"
                        ]
                        # 排除当前查询的函数类型
                        other_function_keywords = [k for k in other_function_keywords if k != base_function]
                        
                        # 检查kp或kw是否包含其他函数类型
                        kp_has_other = any(other in kp for other in other_function_keywords)
                        kw_has_other = any(other in kw for other in other_function_keywords)
                        
                        # 检查kp或kw是否包含当前查询的函数类型
                        kp_has_current = core_theme in kp or base_function in kp
                        kw_has_current = core_theme in kw or base_function in kw
                        
                        # 【关键改进】如果习题知识点同时包含当前函数类型和其他函数类型
                        # 说明这是综合题或跨章节复习题，应该允许通过
                        if kp_has_current and kp_has_other:
                            # 例如：kp="对数运算;指数运算", core_theme="指数函数"
                            # 虽然包含"对数"，但也包含"指数"，应该允许
                            pass  # 继续后续检查
                        
                        # 如果习题的知识点只包含其他函数类型，完全不包含当前查询的函数类型
                        # 需要进一步检查是否包含通用词（如"函数应用"、"函数模型"等）
                        elif kp_has_other and not kp_has_current:
                            # 检查是否包含通用词（扩展列表）
                            generic_terms = [
                                "函数应用", "函数模型", "函数的应用", "模型选择", "数据拟合",
                                "运算", "公式", "性质", "图像", "定义", "定理",
                                "方程", "不等式", "实际问题", "实际应用"
                            ]
                            has_generic_term = any(term in kp for term in generic_terms)
                            
                            if has_generic_term:
                                # 包含通用词，允许通过，由语义分数决定
                                # 例如：kp="对数运算;指数运算", core_theme="指数函数"
                                # 例如：kp="正弦函数的实际应用", core_theme="指数函数"
                                pass  # 继续后续检查
                            else:
                                # 不包含通用词，确实是其他函数类型，拒绝
                                # 例如：kp="分段函数", core_theme="指数函数"
                                return False
                        
                        # 如果KG关键词包含其他函数类型，但习题知识点不包含
                        # 也需要检查
                        elif kw_has_other and not kp_has_other:
                            return core_theme in kp or core_theme in kw
                        
                        # 如果不包含其他函数类型，但包含通用词如"函数"、"应用"等
                        # 需要更严格的检查：要求kp和kw有明显的词汇重叠或子串关系
                        if not kp_has_other and not kw_has_other:
                            # 检查是否有明显的词汇重叠
                            if kw in kp or kp in kw:
                                # kw是kp的子串或kp是kw的子串
                                # 例如：kp="函数图像", kw="函数"
                                # 例如：kp="指数函数模型", kw="指数函数"
                                return True
                            else:
                                # 没有子串关系，拒绝
                                # 例如：kp="散点图与函数拟合", kw="函数性质" → False
                                return False
                    
                    # 4. 常规前缀匹配
                    # kp是kw的前缀（如kp="二倍角"匹配kw="二倍角公式"）
                    if kw.startswith(kp):
                        return True
                    
                    # kw是kp的前缀（如kp="正弦二倍角"匹配kw="正弦"）
                    if kp.startswith(kw):
                        return True
                    
                    return False

                # ========== V104.4 函数类型软过滤（基于KG keywords） ==========
                # 策略：从知识图谱中读取函数类型的keywords，进行精确匹配
                # 对于命中函数类型的资源，使用更低语义阈值
                # 对于未命中的资源，需要更高语义分数才能展示
                function_type_matched_ids = set()
                if core_theme and isinstance(core_theme, str):
                    # 提取核心主题（如"指数函数,函数图像" -> "指数函数"）
                    first_theme = core_theme.split(',')[0].strip()
                    
                    # V104.4: 尝试从知识图谱中获取该主题的keywords
                    kg_function_keywords = []
                    try:
                        # 直接加载KG数据（不依赖后面的kg_data变量）
                        import json
                        import os
                        _file_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_file_dir)))))
                        kg_path = os.path.join(project_root, 'knowledge_graph.json')
                        with open(kg_path, 'r', encoding='utf-8') as f:
                            kg_data_temp = json.load(f)
                        kg_nodes = kg_data_temp.get('nodes', [])
                        
                        # 查找匹配的节点（通过label或id）
                        for node in kg_nodes:
                            node_label = node.get('label', '')
                            node_id = node.get('id', '')
                            # 匹配条件：label包含主题 或 id包含主题
                            if first_theme in node_label or first_theme.replace('函数', '') in node_label or \
                               first_theme.lower().replace('_', ' ') in node_id or \
                               first_theme.replace('函数', '_').lower() in node_id:
                                # 找到匹配节点，提取keywords
                                if 'keywords' in node and node['keywords']:
                                    kg_function_keywords = node['keywords']
                                    logger.warning(f"[V104.4] 从KG获取{first_theme}的keywords: {kg_function_keywords}")
                                break
                    except Exception as e:
                        logger.warning(f"[V104.4] 从KG获取keywords失败: {e}，使用默认策略")
                    
                    # 生成匹配关键词列表
                    if kg_function_keywords:
                        # 优先使用KG的keywords
                        theme_keywords = kg_function_keywords
                    else:
                        # 回退策略：手动生成关键词
                        theme_keywords = [first_theme]
                        if '函数' in first_theme and len(first_theme) > 2:
                            base_keyword = first_theme.replace('函数', '').strip()
                            if base_keyword:
                                theme_keywords.append(base_keyword)
                        logger.warning(f"[V104.4] KG无keywords，使用默认关键词: {theme_keywords}")
                    
                    # 检查哪些资源命中了函数类型关键词
                    for r in simple_results:
                        meta = r.get('metadata', r) if isinstance(r, dict) else r
                        match_candidates = []
                        if '知识点标签' in meta:
                            match_candidates.append(str(meta['知识点标签']))
                        if 'title' in meta:
                            match_candidates.append(str(meta['title']))
                        match_str = ';'.join([k for k in match_candidates if k])
                        
                        # 检查是否包含任意一个关键词
                        is_matched = any(kw in match_str for kw in theme_keywords)
                        if is_matched:
                            function_type_matched_ids.add(id(r))

                # 1. 用知识图谱扩展主题关键词（直接读取 JSON，避免模块导入问题）
                kg_keywords = set()
                kg_data = []  # 初始化，确保后续可访问
                try:
                    import json
                    import os
                    # 确保解析到项目根目录（knowledge_graph.json 所在位置）
                    # retrieve.py 位置: backend/app/core/retrieval/methods/retrieve.py
                    # knowledge_graph.json 位置: 项目根目录/
                    _file_dir = os.path.dirname(os.path.abspath(__file__))
                    # methods -> retrieval -> core -> app -> backend -> 项目根
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_file_dir)))))
                    kg_path = os.path.join(project_root, 'knowledge_graph.json')
                    logger.warning(f"[方案A] 知识图谱路径: {kg_path}, 文件存在: {os.path.exists(kg_path)}")
                    with open(kg_path, 'r', encoding='utf-8') as f:
                        kg_data = json.load(f)
                    nodes = kg_data.get('nodes', [])
                    node_id_index = {n['id']: n for n in nodes}

                    # ========== 使用习题专用的KG关键词提取 ==========
                    # 将 core_theme 拆分为独立的子主题列表（兼容字符串/列表两种输入）
                    if isinstance(core_theme, list):
                        _theme_parts = core_theme
                    elif isinstance(core_theme, str):
                        _theme_parts = [p.strip() for p in core_theme.split(",") if p.strip()]
                    else:
                        _theme_parts = []

                    # 使用习题专用的KG关键词提取函数
                    kg_keywords, num_matched_nodes = _extract_exercise_kg_keywords(core_theme, kg_data)
                    
                    # 调试日志
                    logger.warning(
                        f"[通用KG引擎] core_theme='{core_theme}', "
                        f"子主题={_theme_parts}, "
                        f"匹配节点数={num_matched_nodes}, "
                        f"匹配词数={len(kg_keywords)}, "
                        f"关键词样例={list(kg_keywords)[:8]}"
                    )
                    
                except Exception as e:
                    logger.warning(f"[方案A] 知识图谱加载失败，不做知识点过滤: {e}")
                    kg_keywords = set()  # 空集 → not kg_keywords 为 True → 全部直接展示
                    num_matched_nodes = 0

                # 2. 向量语义二次过滤：计算每条结果与 core_theme 的语义相似度
                #    避免向量检索返回的不相关习题（如"幂函数""二分法"混入"三角恒等变换"）
                _semantic_scores = {}
                try:
                    _emb_model = model_config.get_embedding_model()
                    _theme_vec = _emb_model.encode(
                        [core_theme], normalize_embeddings=True
                    )  # shape: (1, dim)

                    # 批量构建候选文本：标题 + 知识点标签
                    _candidate_texts = []
                    for r in simple_results:
                        _meta = r['metadata']
                        _title = _meta.get('title', '') or ''
                        _kp = _meta.get('知识点', '') or _meta.get('知识点标签', '') or ''
                        _candidate_texts.append(f"{_title} {_kp}")

                    _candidate_vecs = _emb_model.encode(
                        _candidate_texts, normalize_embeddings=True
                    )  # shape: (N, dim)

                    # 点积 = 余弦相似度（已归一化）
                    import numpy as _np
                    _sim = _np.dot(_candidate_vecs, _theme_vec.T).flatten()
                    for _i, _r in enumerate(simple_results):
                        _semantic_scores[id(_r)] = float(_sim[_i])

                    # P1: V104.1 动态语义过滤阈值 - 习题专用差异化策略
                    # 策略：根据KG匹配情况和相似度分布，使用更灵活的阈值
                    # - KG匹配良好：使用第5百分位（非常宽松，保留95%的习题）
                    # - KG部分匹配：使用第10百分位（宽松，保留90%的习题）
                    # - KG未匹配：使用第15百分位（中等，保留85%的习题）
                    num_themes = len(_theme_parts)
                    
                    # 基础百分位设置 - 习题检索更宽松
                    if num_matched_nodes == 0:
                        base_percentile = 15  # KG未匹配 → 第15百分位（更宽松）
                    elif num_matched_nodes < num_themes:
                        base_percentile = 10  # KG部分匹配 → 第10百分位
                    else:
                        base_percentile = 5   # KG完全匹配 → 第5百分位（最宽松）
                    
                    _semantic_threshold = float(_np.percentile(_sim, base_percentile))
                    
                    # V104.1习题专用：最低保障阈值0.10（进一步降低）
                    _semantic_threshold = max(_semantic_threshold, 0.10)

                    logger.warning(
                        f"[方案A] 语义二次过滤: core_theme='{core_theme}', "
                        f"相似度范围=[{_sim.min():.3f}, {_sim.max():.3f}], "
                        f"KG匹配节点数={num_matched_nodes}, 子主题数={num_themes}, "
                        f"动态阈值(第{base_percentile}百分位)={_semantic_threshold:.3f}"
                    )
                except Exception as e:
                    logger.warning(f"[方案A] 语义二次过滤失败，跳过: {e}")

                # 3. 遍历结果，做知识图谱匹配 + 语义过滤
                exercise_resources = []
                hidden_resources = []
                import re as _re

                for r in simple_results:
                    meta = r['metadata']
                    distance = r['distance']
                    relevance = max(0.0, 1.0 / (1.0 + distance))

                    # 获取习题的知识点标签（合并多个字段）
                    kp_from_meta = meta.get("知识点", "")
                    kp_from_tag = meta.get("知识点标签", "")
                    
                    # 从 analysis_json 获取更多信息
                    analysis_data = meta.get("analysis_json", {})
                    if isinstance(analysis_data, str):
                        try:
                            import json as _json
                            analysis_data = _json.loads(analysis_data)
                        except:
                            analysis_data = {}
                    
                    # 收集所有知识点来源
                    all_kp_texts = []
                    
                    # 1. 知识点标签
                    if kp_from_tag:
                        all_kp_texts.append(kp_from_tag)
                    
                    # 2. 知识点（metadata）
                    if kp_from_meta:
                        all_kp_texts.append(kp_from_meta)
                    
                    # 3-6. analysis中的字段
                    if isinstance(analysis_data, dict):
                        # analysis.知识点（列表转字符串）
                        analysis_kp = analysis_data.get("知识点", [])
                        if isinstance(analysis_kp, list):
                            all_kp_texts.extend(analysis_kp)
                        
                        # analysis.核心考点
                        core_point = analysis_data.get("核心考点", "")
                        if core_point:
                            all_kp_texts.append(core_point)
                        
                        # analysis.涉及公式
                        formulas = analysis_data.get("涉及公式", [])
                        if isinstance(formulas, list):
                            all_kp_texts.extend(formulas)
                        
                        # analysis.解题思路（限制长度，避免过长）
                        solution_idea = analysis_data.get("解题思路", "")
                        if solution_idea and len(solution_idea) < 200:
                            all_kp_texts.append(solution_idea)
                    
                    # 去重并构建kp_list
                    kp_set = set()
                    for text in all_kp_texts:
                        if isinstance(text, str) and text.strip():
                            # 按分号分割（兼容旧格式）
                            parts = [p.strip() for p in text.replace("；", ";").split(";") if p.strip()]
                            kp_set.update(parts)
                        elif isinstance(text, list):
                            for item in text:
                                if isinstance(item, str) and item.strip():
                                    kp_set.add(item.strip())
                    
                    kp_list = list(kp_set)

                    # ========== V64.4 意图识别与智能联合校验 ==========
                    # 1. 意图识别：根据查询语句判断是“综合题”还是“分别的题”
                    is_comprehensive_intent = False
                    is_separate_intent = False
                    
                    # 获取原始查询字符串（兼容不同调用路径）
                    _query_str = query if isinstance(query, str) else ""
                    
                    # 显式关键词检测
                    if any(kw in _query_str for kw in ["综合", "结合", "一起", "融合"]):
                        is_comprehensive_intent = True
                    elif any(kw in _query_str for kw in ["分别", "各自", "分开", "单独"]):
                        is_separate_intent = True
                    else:
                        # 隐式结构检测：
                        # - “A的B” (如分段函数的单调性) -> 倾向于综合
                        # - “A和B” (如分段函数和单调性) -> 倾向于分别
                        if "的" in core_theme and len(core_theme.split("的")) >= 2:
                            is_comprehensive_intent = True
                        elif any(conn in core_theme for conn in ["和", "与", "、"]):
                            is_separate_intent = True

                    # 2. 执行过滤逻辑
                    if is_comprehensive_intent:
                        import re
                        # V64.5 优化拆分：确保“分段函数”等专有名词不被拆散
                        parts = []
                        
                        # 策略 1：按“的”字拆分（最优先）
                        if "的" in core_theme:
                            parts = [p.strip() for p in core_theme.split("的") if p.strip()]
                        
                        # 策略 2：如果没拆出两个词，尝试在“函数”后断开（针对“分段函数单调性”）
                        if len(parts) < 2:
                            # 使用更精准的正则：匹配“XX函数” + “剩余部分”
                            match = re.search(r'([\u4e00-\u9fa5]*?函数)([\u4e00-\u9fa5]+)', core_theme)
                            if match:
                                part1 = match.group(1).strip()
                                part2 = match.group(2).strip()
                                if part1 and part2 and part1 != core_theme:
                                    parts = [part1, part2]
                        
                        # 策略 3：如果还是只有一个词，尝试按常见数学概念边界拆分（如“单调性”、“奇偶性”）
                        if len(parts) < 2:
                            common_props = ["单调性", "奇偶性", "周期性", "对称性", "零点", "最值", "应用"]
                            for prop in common_props:
                                if prop in core_theme and core_theme.index(prop) > 0:
                                    idx = core_theme.index(prop)
                                    part1 = core_theme[:idx].strip()
                                    part2 = core_theme[idx:].strip()
                                    if part1 and part2:
                                        parts = [part1, part2]
                                        break
                        
                        keywords_to_check = [kw for kw in parts if len(kw) > 1] # 过滤掉单字
                        
                        if len(keywords_to_check) >= 2:
                            # V66.0 维度对齐校验：确保多个知识点是在讨论同一个对象，而非简单的关键词堆砌
                            synonym_map = {
                                "单调性": ["单调性", "增减性", "递增", "递减", "增函数", "减函数", "变化趋势", "变化规律"],
                                "奇偶性": ["奇偶性", "奇函数", "偶函数", "对称性", "关于原点对称", "关于y轴对称"],
                                "周期性": ["周期性", "周期", "重复出现"],
                                "分段函数": ["分段函数", "分段"],
                                "函数图像": ["函数图像", "图象", "图像", "图形"],
                            }
                            
                            # 1. 优化关键词列表：如果存在包含关系（如“分段函数”和“函数”），只保留长词
                            filtered_kws = []
                            for i, kw1 in enumerate(keywords_to_check):
                                is_subset = False
                                for j, kw2 in enumerate(keywords_to_check):
                                    if i != j and kw1 in kw2:
                                        is_subset = True
                                        break
                                if not is_subset:
                                    filtered_kws.append(kw1)
                            
                            # 2. 准备不同权重的校验文本
                            core_text = str(analysis_data.get("核心考点", "")) + str(meta.get("知识点标签", ""))
                            deep_text = str(analysis_data.get("解题思路", "")) + str(analysis_data.get("分析详情", ""))
                            full_analysis = core_text + deep_text
                            
                            match_score = 0.0
                            total_possible_score = len(filtered_kws) * 1.0
                            has_core_dimension = False
                            
                            for kw in filtered_kws:
                                candidates = synonym_map.get(kw, [kw])
                                kw_matched = False
                                
                                for candidate in candidates:
                                    # 核心命中 (+1.0)
                                    if any(candidate in kp for kp in kp_list) or candidate in core_text:
                                        match_score += 1.0
                                        kw_matched = True
                                        if kw == "分段函数" or kw == "单调性":
                                            has_core_dimension = True
                                        break
                                    # 深度命中 (+0.7)
                                    elif candidate in deep_text:
                                        match_score += 0.7
                                        kw_matched = True
                                        break
                                
                                if not kw_matched:
                                    pass
                            
                            # 3. 判定逻辑：V68.0 语义宽容度提升
                            coverage_ratio = match_score / total_possible_score if total_possible_score > 0 else 0
                            
                            # 逻辑 A: 针对“分段函数单调性”的专项优化
                            is_segment_monotonicity_query = ("分段函数" in keywords_to_check and "单调性" in keywords_to_check)
                            
                            if is_segment_monotonicity_query:
                                # V68.0 改进：只要分析文本里同时出现了“分段”和“变化/增减”的描述，就视为命中
                                has_segment_feature = "分段" in full_analysis or "分段函数" in meta.get("title", "")
                                has_monotonicity_desc = any(syn in full_analysis for syn in synonym_map.get("单调性", []))
                                
                                if has_segment_feature and has_monotonicity_desc:
                                    # 即使关键词没完全对上，但语义对上了，给个基础分让它留下来
                                    if coverage_ratio < 0.5:
                                        coverage_ratio = 0.5
                                elif not has_segment_feature:
                                    logger.warning(f"[V68.0-维度] 资源 '{meta.get('title', '未知')}' 缺少分段特征，剔除")
                                    continue
                            
                            if coverage_ratio < 0.5:
                                logger.warning(f"[V68.0-综合] 资源 '{meta.get('title', '未知')}' 综合匹配度仅 {coverage_ratio:.1f}，已剔除")
                                continue
                            
                            # 将匹配度加成到相关性分数上，让真正的综合题排前面
                            relevance += (coverage_ratio * 0.15) 
                    # =============================================
                    
                    # 检查是否有任意一个知识点命中知识图谱扩展词
                    # 使用增强的匹配逻辑，考虑函数板块的特殊性
                    is_specific_function = _is_specific_function_query(core_theme)
                                        
                    has_kg_match = False
                    matched_keywords = []
                    for kp in kp_list:
                        for kw in kg_keywords:
                            if _word_match_enhanced(kp, kw, core_theme, is_specific_function):
                                has_kg_match = True
                                matched_keywords.append(f"{kp}←{kw}")
                                break
                        if has_kg_match:
                            break
                    
                    logger.warning(
                        f"[方案A-调试] title='{meta.get('title', '')[:40]}', "
                        f"kp_meta='{kp_from_meta[:40]}', kp_tag='{kp_from_tag[:40]}', "
                        f"kp_count={len(kp_list)}, relevance={relevance:.3f}, "
                        f"has_kg_match={has_kg_match}, matched={matched_keywords[:2] if matched_keywords else 'None'}"
                    )
                    if not has_kg_match and kp_list:
                        logger.debug(f"[方案A] 知识点未命中: title='{meta.get('title', '')[:30]}', kp={kp_list[:3]}, relevance={relevance:.3f}")

                    resource = {
                        "title": meta.get("title", "未知"),
                        "content": r['document'],
                        "source": meta.get("原文件云端链接", "") or meta.get("云端链接", "") or meta.get("source_file", ""),
                        "relevance": relevance,
                        "metadata": meta,
                        "base_relevance": relevance,
                        "matched_themes": [core_theme] if has_kg_match else [],
                        "is_core_match": has_kg_match,
                        "resource_type": "exercise",
                        "难度": meta.get("难度", "") or meta.get("difficulty", "") or meta.get("难度（1-5）", ""),
                        "题目类型": meta.get("题目类型", ""),
                        "知识点": "; ".join(kp_list) if kp_list else "",
                    }

                    # 获取语义相似度分数（二次过滤）
                    semantic_score = _semantic_scores.get(id(r), 0.0)

                    # V104.1 差异化展示逻辑
                    is_function_matched = id(r) in function_type_matched_ids
                    
                    if has_kg_match or not kg_keywords:
                        # 命中知识图谱 或 知识图谱不可用 → 正常展示
                        exercise_resources.append(resource)
                    elif is_function_matched and relevance >= 0.15 and semantic_score >= _semantic_threshold:
                        # V104.1：函数类型匹配 + 低门槛 → 展示
                        resource["_kg_mismatch"] = True
                        resource["matched_themes"] = []
                        resource["_semantic_score"] = semantic_score
                        resource["_function_type_matched"] = True
                        exercise_resources.append(resource)
                        logger.info(
                            f"[方案A-V104.1] 函数类型匹配，低门槛展示: title='{meta.get('title', '未知')[:40]}', "
                            f"kp='{('; '.join(kp_list))[:60]}', relevance={relevance:.3f}, semantic={semantic_score:.3f}"
                        )
                    elif relevance >= 0.15 and semantic_score >= (_semantic_threshold + 0.05):  # V104.2: 未匹配函数类型需要稍高分数（+0.05）
                        # V104.1：未匹配函数类型，需要稍高语义分数 → 展示
                        resource["_kg_mismatch"] = True
                        resource["matched_themes"] = []
                        resource["_semantic_score"] = semantic_score
                        resource["_function_type_matched"] = False
                        exercise_resources.append(resource)
                        logger.info(
                            f"[方案A-V104.1] 函数类型未匹配但语义分达标，仍展示: title='{meta.get('title', '未知')[:40]}', "
                            f"kp='{('; '.join(kp_list))[:60]}', relevance={relevance:.3f}, semantic={semantic_score:.3f} (阈值={_semantic_threshold + 0.05:.3f})"
                        )
                    else:
                        # relevance 或 语义不够 → 隐藏或丢弃
                        hide_reason_parts = []
                        if not has_kg_match:
                            hide_reason_parts.append(f"知识点不匹配: {('; '.join(kp_list))[:50]}")
                        if semantic_score < _semantic_threshold:
                            hide_reason_parts.append(f"语义不相关({semantic_score:.2f} < 阈值{_semantic_threshold:.2f})")
                        if relevance < 0.15:
                            # V104.0习题专用：降低relevance丢弃门槛从0.25到0.15
                            # relevance 太低 → 直接丢弃
                            logger.warning(
                                f"[方案A] 丢弃低相关习题: title='{meta.get('title', '未知')[:40]}', "
                                f"relevance={relevance:.3f}, semantic={semantic_score:.3f}, kp='{('; '.join(kp_list))[:60]}'"
                            )
                        else:
                            # 隐藏
                            resource["_hidden_reason"] = "; ".join(hide_reason_parts)
                            hidden_resources.append(resource)
                            logger.info(
                                f"[方案A] 隐藏习题: title='{meta.get('title', '未知')[:40]}', "
                                f"kp='{('; '.join(kp_list))[:60]}', relevance={relevance:.3f}, semantic={semantic_score:.3f}"
                            )

                # 文件级去重过滤（上游已改为每文件只出1条，本段作为兜底）
                _hidden_sources = set()
                for _h in hidden_resources:
                    _src = _h.get("source", "")
                    if _src:
                        _hidden_sources.add(_src)

                if _hidden_sources:
                    _before = len(exercise_resources)
                    exercise_resources = [
                        _r for _r in exercise_resources
                        if _r.get("is_core_match", True) or _r.get("source", "") not in _hidden_sources
                    ]
                    _removed = _before - len(exercise_resources)
                    if _removed > 0:
                        logger.warning(
                            f"[方案A] 文件级去重(兜底): 移除 {_removed} 条"
                        )

                # ========== 多维度融合评分校验 ==========
                # 对所有候选资源进行多维度综合评分，过滤低相关资源
                logger.warning(f"[方案A-调试] 检查多维度融合评分校验条件: exercise_resources={len(exercise_resources)}, core_theme='{core_theme}', bool(exercise_resources)={bool(exercise_resources)}, bool(core_theme)={bool(core_theme)}")
                if exercise_resources and core_theme:
                    logger.warning(f"🔍 开始多维度融合评分校验，候选资源数: {len(exercise_resources)}")
                    print(f"🔍 开始多维度融合评分校验，候选资源数: {len(exercise_resources)}")
                    
                    try:
                        # 合并所有候选资源（包括隐藏的）进行评分
                        all_candidates = exercise_resources + hidden_resources
                        logger.warning(f"[方案A-调试] 合并候选资源: {len(all_candidates)}条")
                        
                        # 获取KG匹配结果（用于KG维度评分）
                        logger.warning(f"[方案A-调试] 开始获取KG匹配结果")
                        kg_result = self.kg.universal_match([core_theme]) if hasattr(self, 'kg') else None
                        logger.warning(f"[方案A-调试] KG匹配结果获取成功: {kg_result is not None}")
                        
                        # ========== 获取差异化评分配置 ==========
                        # 根据主题类型获取不同的评分权重和过滤阈值
                        logger.warning(f"[方案A-调试] 开始获取评分配置")
                        weights = get_scoring_weights(core_theme)
                        thresholds = get_filter_threshold(core_theme)
                        logger.warning(f"[方案A-调试] 评分配置获取成功: weights={weights}, thresholds={thresholds}")
                        
                        logger.warning(f"[方案A-调试] 开始执行print语句")
                        print(f"🎯 主题类型: {'宽泛主题' if is_broad_topic(core_theme) else '具体主题'}")
                        print(f"   评分权重: LLM={weights['llm']}, KG={weights['kg']}, 语义={weights['semantic']}, 质量={weights['quality']}")
                        print(f"   过滤阈值: KG={thresholds['kg_threshold']}, 语义={thresholds['semantic_threshold']}, 最终分数={thresholds['final_score_threshold']}")
                        logger.warning(f"[方案A-调试] print语句执行完成")
                        
                        # ========== 预计算所有维度分数并应用混合评分策略 ==========
                        # 混合评分策略：高置信度资源跳过LLM调用，低置信度资源直接过滤
                        logger.warning(f"[方案A-调试] 开始预计算维度分数")
                        candidates_with_scores = []
                        resources_requiring_llm = []  # 需要LLM评分的资源
                        llm_candidate_indices = []   # 需要LLM评分的资源索引
                        
                        for idx, resource in enumerate(all_candidates):
                            logger.warning(f"[方案A-调试] 开始处理第{idx}个资源: {resource.get('title', '')[:30]}")
                            # 计算语义相似度
                            logger.warning(f"[方案A-调试] 开始计算语义相似度")
                            semantic_score = self._calculate_semantic_similarity(core_theme, resource)
                            logger.warning(f"[方案A-调试] 语义相似度计算完成: {semantic_score}")
                            
                            # 计算KG匹配分数
                            kg_score = self._calculate_kg_match_score(resource, kg_result)
                            
                            # 计算资源质量分数
                            quality_score = self._calculate_resource_quality(resource)
                            
                            # ========== 混合评分策略（差异化处理） ==========
                            # 策略1: 如果KG匹配度很高，直接返回高分，跳过LLM调用
                            kg_high_threshold = 0.75 if not is_broad_topic(core_theme) else 0.70
                            if kg_score > kg_high_threshold:
                                llm_score = 0.95
                                final_score = (
                                    llm_score * weights['llm'] +
                                    kg_score * weights['kg'] +
                                    semantic_score * weights['semantic'] +
                                    quality_score * weights['quality']
                                )
                                final_score = max(0.0, min(1.0, final_score))
                                
                                # 保存分数
                                resource["_final_score"] = final_score
                                resource["_llm_score"] = llm_score
                                resource["_kg_score"] = kg_score
                                resource["_semantic_score"] = semantic_score
                                resource["_quality_score"] = quality_score
                                candidates_with_scores.append((resource, final_score))
                                continue
                            
                            # 策略2: 如果语义相似度很低，直接返回低分，跳过LLM调用
                            semantic_low_threshold = thresholds['semantic_threshold']
                            if semantic_score < semantic_low_threshold:
                                llm_score = 0.15
                                final_score = (
                                    llm_score * weights['llm'] +
                                    kg_score * weights['kg'] +
                                    semantic_score * weights['semantic'] +
                                    quality_score * weights['quality']
                                )
                                final_score = max(0.0, min(1.0, final_score))
                                
                                # 保存分数
                                resource["_final_score"] = final_score
                                resource["_llm_score"] = llm_score
                                resource["_kg_score"] = kg_score
                                resource["_semantic_score"] = semantic_score
                                resource["_quality_score"] = quality_score
                                candidates_with_scores.append((resource, final_score))
                                continue
                            
                            # 策略3: 如果KG匹配度很低，即使语义相似度高，也不调用LLM
                            kg_low_threshold = thresholds['kg_threshold']
                            if kg_score < kg_low_threshold and semantic_score < 0.5:
                                # KG和语义都不匹配，直接过滤
                                llm_score = 0.1
                                final_score = (
                                    llm_score * weights['llm'] +
                                    kg_score * weights['kg'] +
                                    semantic_score * weights['semantic'] +
                                    quality_score * weights['quality']
                                )
                                final_score = max(0.0, min(1.0, final_score))
                                
                                # 保存分数
                                resource["_final_score"] = final_score
                                resource["_llm_score"] = llm_score
                                resource["_kg_score"] = kg_score
                                resource["_semantic_score"] = semantic_score
                                resource["_quality_score"] = quality_score
                                candidates_with_scores.append((resource, final_score))
                                continue
                            
                            resources_requiring_llm.append((resource, semantic_score, kg_score, quality_score))
                            llm_candidate_indices.append(idx)
                        
                        # ========== 限制LLM调用数量（只对前12个最相关资源调用LLM） ==========
                        llm_top_n = 12
                        
                        # 按语义相似度排序需要LLM评分的资源
                        resources_requiring_llm.sort(key=lambda x: -x[1])
                        top_llm_candidates = resources_requiring_llm[:llm_top_n]
                        remaining_llm_candidates = resources_requiring_llm[llm_top_n:]
                        
                        # 准备批量评分的资源列表（只包含top资源）
                        resources_for_batch = []
                        for resource, _, _, _ in top_llm_candidates:
                            content = resource.get('content', '')
                            meta_info = {
                                "title": resource.get('title', ''),
                                "知识点": resource.get('知识点', '')
                            }
                            resources_for_batch.append((content, meta_info))
                        
                        # 批量调用LLM评分（一次调用处理所有top资源）
                        llm_scores = []
                        if resources_for_batch:
                            print(f"🚀 开始批量LLM评分，仅对前{llm_top_n}个需要精细评分的资源评分")
                            llm_scores = self._calculate_batch_theme_relevance_scores(core_theme, resources_for_batch)
                            print(f"✅ 批量LLM评分完成")
                        
                        # ========== 处理需要LLM评分的资源 ==========
                        # 处理top LLM资源（有LLM评分）
                        for i, (resource, semantic_score, kg_score, quality_score) in enumerate(top_llm_candidates):
                            # 获取批量计算的LLM分数
                            llm_score = llm_scores[i] if i < len(llm_scores) else 0.3
                            
                            # 综合评分
                            final_score = (
                                llm_score * weights['llm'] +
                                kg_score * weights['kg'] +
                                semantic_score * weights['semantic'] +
                                quality_score * weights['quality']
                            )
                            final_score = max(0.0, min(1.0, final_score))
                            
                            # 保存分数
                            resource["_final_score"] = final_score
                            resource["_llm_score"] = llm_score
                            resource["_kg_score"] = kg_score
                            resource["_semantic_score"] = semantic_score
                            resource["_quality_score"] = quality_score
                            candidates_with_scores.append((resource, final_score))
                        
                        # 处理剩余需要LLM评分的资源（不调用LLM，使用语义相似度作为默认分数）
                        for resource, semantic_score, kg_score, quality_score in remaining_llm_candidates:
                            # 不调用LLM，使用语义相似度作为默认分数（限制在0.3-0.7之间）
                            llm_score = max(0.3, min(0.7, semantic_score))
                            
                            # 综合评分（使用差异化权重）
                            final_score = (
                                llm_score * weights['llm'] +
                                kg_score * weights['kg'] +
                                semantic_score * weights['semantic'] +
                                quality_score * weights['quality']
                            )
                            final_score = max(0.0, min(1.0, final_score))
                            
                            # 保存分数
                            resource["_final_score"] = final_score
                            resource["_llm_score"] = llm_score
                            resource["_kg_score"] = kg_score
                            resource["_semantic_score"] = semantic_score
                            resource["_quality_score"] = quality_score
                            candidates_with_scores.append((resource, final_score))
                        
                        # 按综合分数排序
                        candidates_with_scores.sort(key=lambda x: -x[1])
                        
                        logger.warning(f"[方案A-调试] 所有候选资源评分完成，共{len(candidates_with_scores)}条")
                        for i, (resource, score) in enumerate(candidates_with_scores[:5]):
                            logger.warning(f"[方案A-调试] 第{i+1}名: title='{resource.get('title', '')[:30]}', score={score:.3f}")
                        
                        # 过滤：使用差异化阈值保留资源
                        multi_threshold = thresholds['final_score_threshold']
                        filtered_exercise = [r[0] for r in candidates_with_scores if r[1] >= multi_threshold]
                        filtered_hidden = [r[0] for r in candidates_with_scores if r[1] < multi_threshold]
                        
                        logger.warning(f"[方案A-调试] 过滤结果: {len(filtered_exercise)}条通过(阈值={multi_threshold}), {len(filtered_hidden)}条被过滤")
                        print(f"✅ 多维度校验完成: {len(filtered_exercise)}条通过, {len(filtered_hidden)}条被过滤")
                        
                        # 输出通过过滤的资源详情
                        if filtered_exercise:
                            logger.warning(f"[方案A-调试] ===== 通过过滤的资源详情 =====")
                            for i, resource in enumerate(filtered_exercise):
                                logger.warning(f"[方案A-调试]   [{i+1}] title='{resource.get('title', '')}', kp='{resource.get('知识点', '')}', final_score={resource.get('_final_score', 0):.3f}")
                        else:
                            logger.warning(f"[方案A-调试] ⚠️  没有资源通过过滤！")
                        
                        # 更新结果
                        exercise_resources = filtered_exercise
                        hidden_resources = filtered_hidden
                    
                    except Exception as e:
                        logger.error(f"[方案A-调试] 多维度融合评分校验失败: {e}", exc_info=True)
                        print(f"❌ 多维度融合评分校验失败: {e}")
                        # 如果多维度评分失败，保持原有结果不变
                
                # ========== 为习题资源补充前端需要的字段 ==========
                logger.warning(f"[方案A-调试] 开始为{len(exercise_resources)}条习题资源补充前端字段")
                for i, resource in enumerate(exercise_resources):
                    # 确保资源包含前端需要的所有字段
                    if 'priority_level' not in resource:
                        resource['priority_level'] = 4  # 核心主题匹配
                    
                    # 【关键修复】设置 relevance 字段，否则 _filter_by_relevance 会将其过滤掉
                    if 'relevance' not in resource or resource.get('relevance', 0) == 0:
                        resource['relevance'] = resource.get('_final_score', resource.get('overall_score', 0.5))
                    
                    if 'overall_score' not in resource:
                        resource['overall_score'] = resource.get('_final_score', resource.get('relevance', 0))
                    if 'resource_quality' not in resource:
                        resource['resource_quality'] = 0.5
                    if 'content_completeness' not in resource:
                        resource['content_completeness'] = 0.3
                    if 'teaching_value' not in resource:
                        resource['teaching_value'] = 0.15
                    if 'comprehensiveness' not in resource:
                        resource['comprehensiveness'] = 0.2
                    if 'matched_themes' not in resource:
                        resource['matched_themes'] = [core_theme]
                    if 'is_core_match' not in resource:
                        resource['is_core_match'] = True
                    if 'match_level' not in resource:
                        resource['match_level'] = 'exact'
                    if 'match_explanation' not in resource:
                        resource['match_explanation'] = f'与查询主题"{core_theme}"高度相关'
                    
                    # 确保source字段存在（用于文件路径显示）
                    if 'source' not in resource or not resource['source']:
                        meta = resource.get('metadata', {})
                        resource['source'] = meta.get('原文件云端链接', '') or meta.get('云端链接', '') or meta.get('source_file', '')
                    
                    # ========== 为 ExerciseCard 补充结构化字段 ==========
                    # 方案A路径创建的 raw resource 没有 question/answer/question_type 等字段，
                    # 但这些字段存在于 metadata 中，此处提取出来供前端卡片渲染。
                    if not resource.get('question'):
                        meta = resource.get('metadata', {})
                        resource['question'] = str(meta.get('题干', '')).strip()
                        resource['answer'] = str(meta.get('解析', '')).strip()
                        resource['question_type'] = str(meta.get('题目类型', '')).strip()
                        resource['knowledge_tags'] = str(meta.get('知识点', '') or meta.get('知识点标签', '')).strip()
                        resource['difficulty'] = str(meta.get('难度（1-5）', '') or meta.get('难度', '')).strip()
                        resource['usage_scene'] = str(meta.get('适用场景', '')).strip()
                        # 注意：图片相关字段已在上游通过其他代码路径处理，这里仅补充文本字段
                    
                    logger.warning(f"[方案A-调试]   [{i+1}] 补充字段完成: title='{resource.get('title', '')[:30]}', relevance={resource.get('relevance', 0):.3f}, priority_level={resource.get('priority_level')}, overall_score={resource.get('overall_score', 0):.3f}")
                
                # 【V63.5改进】习题专用过滤：确保返回的题目与核心主题真正相关
                logger.warning(f"[方案A-调试] 开始执行V63.5核心主题相关性过滤")
                exercise_resources = filter_exercise_by_core_theme_relevance(exercise_resources, core_theme)
                logger.warning(f"[方案A-调试] V63.5过滤完成，剩余{len(exercise_resources)}条习题资源")
                        
                # 【V63.6改进】习题专用排序优化：让专门针对核心主题的题目排在前面
                logger.warning(f"[方案A-调试] 开始执行V63.6排序优化")
                exercise_resources = sort_exercises_by_title_relevance(exercise_resources, core_theme)
                logger.warning(f"[方案A-调试] V63.6排序优化完成")
                
                # 【V107.0修复】方案A也需要应用难度过滤
                logger.warning(f"[方案A-调试] 开始执行V107.0难度过滤")
                if difficulty:
                    from ..methods.classify_results import DIFFICULTY_KEYWORD_POLICY
                    filtered_exercise_with_difficulty = []
                    for resource in exercise_resources:
                        resource_difficulty = resource.get("难度（1-5）", "") or resource.get("difficulty", "") or resource.get("难度", "")
                        if not resource_difficulty:
                            # 如果没有难度信息，保留
                            filtered_exercise_with_difficulty.append(resource)
                            continue
                        
                        keywords = DIFFICULTY_KEYWORD_POLICY.get(difficulty, [])
                        if any(str(keyword) in str(resource_difficulty) for keyword in keywords):
                            filtered_exercise_with_difficulty.append(resource)
                        else:
                            logger.warning(f"[V107.0难度过滤] 排除难度'{resource_difficulty}'的习题: {resource.get('title', '')[:50]}")
                    
                    logger.warning(f"[方案A-调试] V107.0难度过滤完成: {len(exercise_resources)} -> {len(filtered_exercise_with_difficulty)}")
                    exercise_resources = filtered_exercise_with_difficulty
                else:
                    logger.warning(f"[方案A-调试] 无难度要求，跳过难度过滤")
                
                classified_resources = {
                    "exercise_resources": exercise_resources,
                    "_ai_decision": {"enabled": False, "reason": "exercise_direct_return"},
                    "_precision_skipped": True,
                    "_hidden_resources": hidden_resources,
                    "_hidden_count": len(hidden_resources),
                    "_total_count": len(exercise_resources) + len(hidden_resources),
                }
                logger.warning(
                    f"[方案A] 习题返回: {len(exercise_resources)}条展示, "
                    f"{len(hidden_resources)}条隐藏, 跳过classify_results"
                )
                print(f"✅ 检索完成（习题直接返回）: {len(exercise_resources)} 条习题, {len(hidden_resources)} 条已隐藏")
                return classified_resources
                # ── 方案A 结束 ──

            elif len(core_themes) > 1:
                logger.info("V103.1调试 - 调用execute_multi_theme_retrieval")
                results = execute_multi_theme_retrieval(
                    self,
                    collection,
                    query,
                    (core_themes, board),  # 传递正确的元组格式 (主题列表, 板块名称)
                    n_results,
                    resource_types,
                    question_type,
                    requirements=query_conditions.get("requirements", []),
                )
            else:
                logger.info("V103.2调试 - 调用execute_single_theme_retrieval")
                _, core_theme, results = execute_single_theme_retrieval(
                    self,
                    collection,
                    query,
                    core_theme,
                    n_results,
                    resource_types,
                    question_type,
                    exclude_keywords=query_conditions.get("exclude_keywords", []),
                    requirements=query_conditions.get("requirements", []),
                )
                results = postprocess_single_theme_results(
                    self, query, results, resource_types, core_theme,
                    exclude_keywords=query_conditions.get("exclude_keywords", []),
                    requirements=query_conditions.get("requirements", [])
                )
                logger.info(f"V103.3调试 - postprocess_single_theme_results返回: {type(results)}, documents数量: {len(results['documents'][0]) if results and results.get('documents') and results['documents'] else 'None'}")

            if not (results and results.get("documents") and results["documents"][0]):
                logger.info("查询完成，但未命中任何资源")
                return self._get_empty_result()

            # ========== 函数类型精确过滤（非习题检索路径）==========
            # 将向量数据库格式的结果转换为列表格式进行过滤
            if results.get("documents") and results.get("metadatas"):
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0] if results.get("distances") else [1.0] * len(docs)
                
                # 转换为列表格式
                result_list = []
                for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
                    result_list.append({
                        'document': doc,
                        'metadata': meta,
                        'distance': dist
                    })
                
                # 应用函数类型过滤
                filtered_list = filter_by_function_type(result_list, core_theme)
                
                # 转换回向量数据库格式
                if filtered_list:
                    results["documents"] = [[r['document'] for r in filtered_list]]
                    results["metadatas"] = [[r['metadata'] for r in filtered_list]]
                    results["distances"] = [[r['distance'] for r in filtered_list]]
                else:
                    results["documents"] = [[]]
                    results["metadatas"] = [[]]
                    results["distances"] = [[]]
            
            results = apply_courseware_teaching_use_filter(results, courseware_teaching_use)
            results = apply_difficulty_filter(results, difficulty_info, self._current_quantity_limit)
            results = apply_question_type_filter(results, question_type, self._current_quantity_limit)
            results = prioritize_pure_function_results(self, query, results, quantity_limit)
            results = apply_quantity_limit(results, quantity_limit, core_theme, query, resource_types)

            # ========== 高效知识图谱过滤（临时禁用）==========
            logger.info(f"V103.4调试 - 知识图谱过滤前: {len(results['documents'][0])} 条结果")
            # 临时禁用知识图谱过滤，直接保留所有结果
            # if results.get("documents") and results["documents"][0]:
            #     docs = results["documents"][0]
            #     metas = results["metadatas"][0]
            #     distances = results["distances"][0] if results.get("distances") else [1.0] * len(docs)
            #     
            #     filtered_docs = []
            #     filtered_metas = []
            #     filtered_distances = []
            #     
            #     for i, doc in enumerate(docs):
            #         kg_score = self.kg.validate_concept_match(query, doc)
            #         
            #         if kg_score >= 0.35:
            #             metas[i]["kg_score"] = kg_score
            #             filtered_docs.append(doc)
            #             filtered_metas.append(metas[i])
            #             filtered_distances.append(distances[i])
            #     
            #     logger.info(f"V103.5调试 - 知识图谱过滤后: {len(filtered_docs)} 条结果")
            #     results["documents"] = [filtered_docs]
            #     results["metadatas"] = [filtered_metas]
            #     if results.get("distances"):
            #         results["distances"] = [filtered_distances]
            logger.info(f"V103.5调试 - 知识图谱过滤已禁用，保留所有结果")

            if results.get("documents") and results["documents"][0]:
                print(f"     ✅ 找到 {len(results['documents'][0])} 条结果")
                for i in range(min(3, len(results["documents"][0]))):
                    meta = results["metadatas"][0][i]
                    print(f"       - 结果{i + 1}: 题目类型={meta.get('题目类型', '未知')}, 来源={meta.get('source_file', '未知')}")
            else:
                print("     ❌ 未找到结果")

            print(f"📊 查询返回 {len(results['documents'][0])} 条结果")
            question_type = self._extract_question_type(query)
            if question_type:
                print(f"🔍 V43.0提取到题目类型: {question_type}")

            classified_resources = self._classify_results(
                results,
                resource_types,
                core_theme,
                query,
                question_type,
                grade,
                difficulty,
                exam_form,
            )
            
            # 调试：_classify_results 结果数量
            total_after_classify = sum(len(v) for v in classified_resources.values() if isinstance(v, list))
            logger.warning(f"[调试] _classify_results 后总数: {total_after_classify}, 类别: {list(classified_resources.keys())}")

            if core_theme:
                print(f"\n🔍 V8.2主题精准匹配（核心主题: {core_theme}）...")
                all_resources = []
                for category in classified_resources:
                    if isinstance(classified_resources[category], list):
                        for resource in classified_resources[category]:
                            if isinstance(resource, dict):
                                resource["_category"] = category
                                all_resources.append(resource)
                            else:
                                print(f"   ⚠️ 跳过非字典资源: {type(resource)}")

                core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                broad_themes = {"数学", "代数", "几何", "统计", "概率"}
                filtered_themes = [t for t in core_themes if t not in broad_themes]
                if len(filtered_themes) < len(core_themes):
                    print(f"   ⚠️ 过滤过于宽泛的主题: {set(core_themes) - set(filtered_themes)}")
                    core_theme = ",".join(filtered_themes) if filtered_themes else core_themes[0]
                    print(f"   ✅ 过滤后的核心主题: {core_theme}")

                visible_resources = [r for r in all_resources if r.get("should_show", True)]
                hidden_resources = [r for r in all_resources if not r.get("should_show", True)]
                print(f"   🔍 V31.0 DEBUG: visible_resources数量={len(visible_resources)}, hidden_resources数量={len(hidden_resources)}")

                balanced_resources = self._balance_resource_distribution(visible_resources, core_theme, query)
                logger.warning(f"[调试] _balance_resource_distribution 后数量: {len(balanced_resources)}")
                classified_resources = self._reclassify_by_relevance(balanced_resources, core_theme)
                total_after_reclassify = sum(len(v) for v in classified_resources.values() if isinstance(v, list))
                logger.warning(f"[调试] _reclassify_by_relevance 后总数: {total_after_reclassify}, 类别: {list(classified_resources.keys())}")
                classified_resources["_hidden_resources"] = hidden_resources
                classified_resources["_hidden_count"] = len(hidden_resources)
                classified_resources["_total_count"] = len(all_resources)
                print(
                    f"   ✅ V8.3排序完成：核心主题优先，共{len(balanced_resources)}个可见资源（隐藏{len(hidden_resources)}个，总计{len(all_resources)}个）"
                )
            else:
                query_features = getattr(self, "_current_query_features", {})
                if query_features.get("has_content_requirement"):
                    print("\n🔍 V9.1应用内容匹配评分（无核心主题）...")
                    for category in classified_resources:
                        for resource in classified_resources[category]:
                            if "content_features" in resource:
                                content_score = self.content_extractor.calculate_content_match_score(
                                    resource["content_features"], query_features
                                )
                                original_relevance = resource.get("relevance", 0)
                                resource["relevance"] = original_relevance * 0.7 + content_score * 0.3
                                resource["content_match_score"] = content_score

                for category in classified_resources:
                    if classified_resources[category]:
                        classified_resources[category].sort(key=lambda x: -x.get("relevance", 0))

                classified_resources["_hidden_resources"] = []
                classified_resources["_hidden_count"] = 0
                classified_resources["_total_count"] = sum(
                    len(resources) for resources in classified_resources.values() if isinstance(resources, list)
                )

            classified_resources = self._apply_ai_rerank_stage(
                classified_resources,
                query,
                intent,
                resource_types,
                core_theme,
            )

            classified_resources = self._apply_unified_ranking(
                classified_resources,
                quantity_limit,
                query=query,
                resource_types=resource_types,
            )

            # 方案A：习题检索跳过主题精度守卫（知识点标签匹配已足够准确）
            _is_exercise_only = (
                resource_types
                and all(rt in ("exercise", "习题", "练习", "题目") for rt in resource_types)
            )
            if not _is_exercise_only:
                classified_resources = enforce_specific_theme_precision(classified_resources, core_theme)
            else:
                logger.warning(f"[方案A] 主题精度守卫已跳过: resource_types={resource_types}")
                classified_resources["_precision_skipped"] = True

            scope_notice = getattr(self, "_current_scope_notice", None)
            if scope_notice:
                classified_resources["_scope_notice"] = scope_notice

            print(f"✅ 检索完成: {self._get_summary(classified_resources)}")
            return classified_resources

        except Exception as e:
            print(f"❌ 资源检索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_empty_result()
