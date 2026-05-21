"""
主题词扩展模块
用于将短的主题词扩展为更具体的同义词和关联词
支持动态扩展，可为任何知识点生成扩展词
"""

from typing import List, Dict, Set, Optional
import re

# 手动定义的同义词和关联词映射（作为基础映射）
SYNONYM_MAPPING = {
    "平面": [
        "空间平面",
        "平面的性质",
        "平面与平面的位置关系",
        "空间点、直线和平面",
        "空间点、直线和平面之间的位置关系",
        "平面的基本性质",
        "平面公理"
    ],
    "直线": [
        "空间直线",
        "直线与平面的位置关系",
        "直线与直线的关系",
        "空间直线与平面",
        "异面直线",
        "空间直线的位置关系"
    ],
    "立体几何": [
        "空间几何体",
        "空间几何",
        "立体几何初步",
        "空间点线面",
        "空间点、直线、平面的位置关系"
    ],
    "向量": [
        "平面向量",
        "空间向量",
        "向量的概念",
        "向量的运算",
        "向量的应用"
    ],
    "圆锥": [
        "圆锥曲线",
        "椭圆",
        "双曲线",
        "抛物线",
        "圆锥的体积",
        "圆锥的表面积"
    ],
    "概率": [
        "概率统计",
        "概率与统计",
        "概率的基本性质",
        "概率计算",
        "概率分布"
    ],
    "函数": [
        "函数概念",
        "函数性质",
        "函数的应用",
        "基本初等函数",
        "函数的单调性",
        "函数的奇偶性"
    ],
    "复数": [
        "复数的概念",
        "复数的几何意义",
        "复数的运算",
        "复数的模",
        "复平面"
    ],
    "抽样": [
        "随机抽样",
        "系统抽样",
        "分层抽样",
        "简单随机抽样"
    ]
}

# 知识层级扩展映射（用于基于层级的扩展）
KNOWLEDGE_HIERARCHY_EXPANSION = {
    "平面": ["立体几何", "空间几何"],
    "直线": ["立体几何", "空间几何"],
    "立体几何": ["几何"],
    "向量": ["几何"],
    "圆锥": ["几何", "解析几何"],
    "概率": ["概率统计"],
    "函数": ["代数"],
    "复数": ["代数"],
    "抽样": ["概率统计"]
}


def _generate_expansion_from_keywords(theme: str, keywords: List[str]) -> List[str]:
    """
    从关键词列表生成扩展词

    Args:
        theme: 原始主题词
        keywords: 关键词列表

    Returns:
        扩展词列表
    """
    if not keywords:
        return []

    expanded = []

    # 检查主题是否包含某个关键词，或某个关键词是否包含主题
    for keyword in keywords:
        # 避免重复添加主题本身
        if keyword != theme and keyword not in theme and theme not in keyword:
            # 检查是否有包含关系
            if len(keyword) >= 2 and len(theme) >= 2:
                expanded.append(keyword)

    return expanded


def _generate_variations(theme: str) -> List[str]:
    """
    生成主题词的变体形式

    Args:
        theme: 原始主题词

    Returns:
        变体列表
    """
    variations = []

    # 添加常见的修饰词前缀
    prefixes = ["", "空间", "平面", "立体", "三维"]
    for prefix in prefixes:
        if prefix and not theme.startswith(prefix):
            variations.append(f"{prefix}{theme}")

    # 如果主题已经以某个前缀开头，尝试去掉前缀
    for prefix in ["空间", "平面", "立体", "三维"]:
        if theme.startswith(prefix):
            variations.append(theme[len(prefix):])
            break

    # 添加常见的修饰词后缀
    suffixes = ["性质", "概念", "运算", "应用", "定理", "公式"]
    for suffix in suffixes:
        if not theme.endswith(suffix):
            variations.append(f"{theme}{suffix}")

    return variations


def expand_theme_with_synonyms(theme: str, knowledge_hierarchy: Dict = None) -> List[str]:
    """
    使用同义词和关联词扩展主题词（包含动态扩展逻辑）

    Args:
        theme: 原始主题词
        knowledge_hierarchy: 知识层级结构字典（可选）

    Returns:
        扩展后的主题词列表（包含原始主题词和扩展词）
    """
    expanded = [theme]

    # 1. 先使用预定义的同义词映射
    if theme in SYNONYM_MAPPING:
        expanded.extend(SYNONYM_MAPPING[theme])

    # 2. 检查主题词是否包含在某个预定义的键中
    for key, synonyms in SYNONYM_MAPPING.items():
        if key in theme:
            expanded.extend(synonyms)
        # 也检查同义词是否包含主题词
        for syn in synonyms:
            if syn in theme:
                expanded.append(key)
                expanded.extend([s for s in synonyms if s != syn])

    # 3. 动态扩展：从knowledge_hierarchy中获取相关信息
    if knowledge_hierarchy:
        theme_info = knowledge_hierarchy.get(theme, {})
        if theme_info:
            # 获取关键词列表并生成扩展
            keywords = theme_info.get('keywords', [])
            if keywords:
                keyword_expansions = _generate_expansion_from_keywords(theme, keywords)
                expanded.extend(keyword_expansions)

            # 获取相关主题
            related = theme_info.get('related_topics', [])
            if related:
                expanded.extend(related)

            # 获取父主题
            parent_topic = theme_info.get('parent_topic', '')
            if parent_topic:
                expanded.append(parent_topic)

    # 4. 生成变体形式
    variations = _generate_variations(theme)
    expanded.extend(variations)

    # 去重并保持顺序
    seen = set()
    result = []
    for item in expanded:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def expand_theme_with_hierarchy(theme: str, knowledge_hierarchy: Dict = None) -> List[str]:
    """
    使用知识层级结构扩展主题词

    Args:
        theme: 原始主题词
        knowledge_hierarchy: 知识层级结构字典（可选）

    Returns:
        扩展后的主题词列表（包含原始主题词和层级相关词）
    """
    expanded = [theme]

    # 使用预定义的层级映射
    if theme in KNOWLEDGE_HIERARCHY_EXPANSION:
        expanded.extend(KNOWLEDGE_HIERARCHY_EXPANSION[theme])

    # 如果提供了knowledge_hierarchy，尝试动态获取
    if knowledge_hierarchy:
        # 获取主题信息
        theme_info = knowledge_hierarchy.get(theme, {})
        if theme_info:
            # 获取父主题
            parent_topic = theme_info.get("parent_topic", "")
            if parent_topic:
                expanded.append(parent_topic)

            # 获取相关主题
            related = theme_info.get("related_topics", [])
            if related:
                expanded.extend(related)

            # 获取章节信息
            chapter = theme_info.get("chapter", "")
            if chapter:
                expanded.append(chapter)

    # 去重并保持顺序
    seen = set()
    result = []
    for item in expanded:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def expand_theme(theme: str, knowledge_hierarchy: Dict = None) -> List[str]:
    """
    综合使用多种策略扩展主题词

    Args:
        theme: 原始主题词
        knowledge_hierarchy: 知识层级结构字典（可选）

    Returns:
        扩展后的主题词列表
    """
    # 确保原始主题词始终在列表的第一位
    result = [theme]

    # 第一步：使用同义词和关联词扩展（包含动态扩展）
    expanded = expand_theme_with_synonyms(theme, knowledge_hierarchy)
    # 去掉第一个元素（原始主题词），因为我们已经在result中包含了
    for item in expanded[1:]:
        if item not in result:
            result.append(item)

    # 第二步：使用知识层级扩展
    expanded = expand_theme_with_hierarchy(theme, knowledge_hierarchy)
    # 去掉第一个元素（原始主题词），因为我们已经在result中包含了
    for item in expanded[1:]:
        if item not in result:
            result.append(item)

    # 第三步：再次使用同义词扩展，确保层级扩展的词也被扩展
    further_expanded = []
    for item in result[1:]:  # 跳过原始主题词本身
        further = expand_theme_with_synonyms(item, knowledge_hierarchy)
        for syn in further:
            if syn not in result:
                further_expanded.append(syn)

    # 合并新发现的扩展词
    for item in further_expanded:
        if item not in result:
            result.append(item)

    return result


def expand_themes_for_retrieval(
    themes: List[str],
    knowledge_hierarchy: Dict = None
) -> List[str]:
    """
    为检索扩展多个主题词

    Args:
        themes: 原始主题词列表
        knowledge_hierarchy: 知识层级结构字典（可选）

    Returns:
        扩展后的主题词列表
    """
    all_expanded = []

    for theme in themes:
        expanded = expand_theme(theme, knowledge_hierarchy)
        all_expanded.extend(expanded)

    # 去重并保持顺序
    seen = set()
    result = []
    for item in all_expanded:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


class ThemeExpander:
    """主题词扩展器"""

    def __init__(self, knowledge_hierarchy: Dict = None):
        """
        初始化主题词扩展器

        Args:
            knowledge_hierarchy: 知识层级结构字典（可选）
        """
        self.knowledge_hierarchy = knowledge_hierarchy

    def expand(self, theme: str) -> List[str]:
        """
        扩展单个主题词

        Args:
            theme: 原始主题词

        Returns:
            扩展后的主题词列表
        """
        return expand_theme(theme, self.knowledge_hierarchy)

    def expand_multiple(self, themes: List[str]) -> List[str]:
        """
        扩展多个主题词

        Args:
            themes: 原始主题词列表

        Returns:
            扩展后的主题词列表
        """
        return expand_themes_for_retrieval(themes, self.knowledge_hierarchy)


if __name__ == "__main__":
    # 测试代码
    test_themes = ["平面", "直线", "立体几何", "椭圆", "函数的单调性"]

    print("=== 主题词扩展测试 ===\n")

    for theme in test_themes:
        expanded = expand_theme(theme)
        print(f"主题: {theme}")
        print(f"扩展后: {expanded}")
        print()

    print("=== 多主题扩展测试 ===\n")
    multi_expanded = expand_themes_for_retrieval(test_themes)
    print(f"输入主题: {test_themes}")
    print(f"扩展后: {multi_expanded}")