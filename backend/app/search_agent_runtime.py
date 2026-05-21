import json
import asyncio
import concurrent.futures
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from langchain_core.messages import HumanMessage

from .core import ResponseBuilder

# V316.0 缓存机制：缓存热门主题的检索结果
# 缓存结构: {cache_key: {'results': retrieved_resources, 'timestamp': timestamp}}
_search_cache = {}
_CACHE_EXPIRE_SECONDS = 300  # 缓存有效期5分钟


def _get_cache_key(theme: str, resource_types: List[str]) -> str:
    """生成缓存键"""
    types_str = "_".join(sorted(resource_types)) if resource_types else "all"
    return f"{theme}_{types_str}"


def _get_cached_results(theme: str, resource_types: List[str]) -> Dict[str, Any] | None:
    """获取缓存结果"""
    cache_key = _get_cache_key(theme, resource_types)
    if cache_key in _search_cache:
        entry = _search_cache[cache_key]
        # 检查缓存是否过期
        if time.time() - entry['timestamp'] < _CACHE_EXPIRE_SECONDS:
            print(f"V316.0 命中缓存: '{theme}'")
            return entry['results']
        else:
            print(f"V316.0 缓存过期: '{theme}'")
            del _search_cache[cache_key]
    return None


def _set_cache_results(theme: str, resource_types: List[str], results: Dict[str, Any]) -> None:
    """设置缓存结果"""
    cache_key = _get_cache_key(theme, resource_types)
    _search_cache[cache_key] = {
        'results': results,
        'timestamp': time.time()
    }
    print(f"V316.0 缓存已更新: '{theme}'")


def get_empty_retrieved_resources() -> Dict[str, Any]:
    return {
        "theory_resources": [],
        "lesson_plan_patterns": [],
        "exercise_resources": [],
        "visualization_examples": [],
        "general_resources": [],
        "courseware_resources": [],
        "lesson_case_resources": [],
        "ggb_resources": [],
        "syllabus_resources": [],
    }


def has_any_retrieved_resources(retrieved_resources: Dict[str, Any]) -> bool:
    if not isinstance(retrieved_resources, dict):
        return False
    for value in retrieved_resources.values():
        if isinstance(value, list) and value:
            return True
    return False


def count_retrieved_resources(retrieved_resources: Dict[str, Any]) -> int:
    if not isinstance(retrieved_resources, dict):
        return 0
    total = 0
    for value in retrieved_resources.values():
        if isinstance(value, list):
            total += len(value)
    return total


def normalize_query_inputs(query: str, queries: List[str] | None = None) -> List[str]:
    merged_queries: List[str] = []
    for item in [query, *(queries or [])]:
        cleaned = str(item or "").strip().strip("，,。；；！!？？ ")
        if cleaned and cleaned not in merged_queries:
            merged_queries.append(cleaned)
    return merged_queries


def resource_identity(resource: Dict[str, Any]) -> str:
    if not isinstance(resource, dict):
        return ""
    
    resource_type = resource.get('resource_type', '')
    is_syllabus = resource_type == 'syllabus' or 'syllabus' in str(resource_type).lower()
    
    if is_syllabus:
        topic = resource.get('topic', '')
        chapter = resource.get('chapter', '')
        if topic and chapter:
            return f"syllabus | {topic} | {chapter}"
        elif chapter:
            return f"syllabus | {chapter}"
    
    # 【V65.3改进】优先使用顶层question字段，如果不存在则从metadata中提取
    question = resource.get('question', '')
    if not question:
        # 尝试从metadata中提取题干
        metadata = resource.get('metadata', {})
        if isinstance(metadata, dict):
            question = metadata.get('题干', '')
    
    return " | ".join(
        str(resource.get(key, "") or "")
        for key in ("title", "source", "filename")
    ) + " | " + str(question or "") + " | " + str(resource.get("answer", "") or "")


def merge_retrieved_resources(resource_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = get_empty_retrieved_resources()
    if not resource_groups:
        return merged

    print(f"[DEBUG] merge_retrieved_resources: 合并 {len(resource_groups)} 个资源组")

    # 为每个资源类别创建全局的去重集合，存储资源标识到资源索引的映射
    seen_per_category = {}
    for group_idx, group in enumerate(resource_groups):
        if not isinstance(group, dict):
            continue
        for key, value in group.items():
            if key not in merged or not isinstance(value, list):
                continue
            # 为每个类别初始化去重集合
            if key not in seen_per_category:
                seen_per_category[key] = {}
                # 将已存在的资源添加到去重集合
                for idx, item in enumerate(merged[key]):
                    if isinstance(item, dict):
                        identity = resource_identity(item)
                        if identity:
                            seen_per_category[key][identity] = idx
            
            existing = merged[key]
            seen = seen_per_category[key]
            for item in value:
                if not isinstance(item, dict):
                    continue
                identity = resource_identity(item)
                title = item.get('title', item.get('meta', {}).get('title', '未知'))[:30]
                matched_themes = item.get('matched_themes', [])
                print(f"[DEBUG] 处理资源: {title}, matched_themes={matched_themes}, identity={identity[:50]}")
                
                if identity and identity in seen:
                    # 资源已存在，合并matched_themes字段
                    existing_idx = seen[identity]
                    existing_item = existing[existing_idx]
                    
                    # 【V63.8改进】保留最高的overall_score（方案A的V63.6排序结果）
                    existing_overall_score = existing_item.get('overall_score', 0)
                    new_overall_score = item.get('overall_score', 0)
                    if new_overall_score > existing_overall_score:
                        existing_item['overall_score'] = new_overall_score
                        # 同时更新relevance以保持一致性
                        if 'relevance' in item:
                            existing_item['relevance'] = item['relevance']
                    
                    # 合并matched_themes
                    existing_themes = existing_item.get('matched_themes', [])
                    new_themes = item.get('matched_themes', [])
                    print(f"[DEBUG] 合并主题: 现有主题={existing_themes}, 新主题={new_themes}")
                    for theme in new_themes:
                        if theme not in existing_themes:
                            existing_themes.append(theme)
                    existing_item['matched_themes'] = existing_themes
                    
                    # 合并theme_distances
                    existing_distances = existing_item.get('theme_distances', {})
                    new_distances = item.get('theme_distances', {})
                    existing_distances.update(new_distances)
                    existing_item['theme_distances'] = existing_distances
                    
                    # 更新matched_theme_count
                    existing_item['matched_theme_count'] = len(existing_themes)
                    print(f"[DEBUG] 合并后主题={existing_item['matched_themes']}")
                    
                    continue
                
                if identity:
                    seen[identity] = len(existing)
                existing.append(item)
    
    # 统计合并结果
    for key, items in merged.items():
        if isinstance(items, list) and items:
            themes_found = set()
            for item in items:
                for theme in item.get('matched_themes', []):
                    themes_found.add(theme)
            print(f"[DEBUG] 合并结果: {key} 类别有 {len(items)} 个资源，包含主题: {themes_found}")
    
    return merged


def build_search_response_payload(
    query: str,
    resource_types: List[str] | None,
    retrieved_resources: Dict[str, Any],
) -> str:
    builder = ResponseBuilder()
    return builder._build_search_response(
        {
            "intent": "search",
            "user_input": query,
            "resource_types": resource_types or [],
            "retrieved_resources": retrieved_resources,
        }
    )


def _extract_resource_types_from_query(query: str) -> List[str]:
    """从查询中自动提取资源类型"""
    resource_type_keywords = {
        "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案"],
        "教学大纲": ["教学大纲", "大纲", "课程标准"],
        "课件": ["课件", "PPT", "幻灯片", "演示文稿"],
        "课例": ["课例", "教学视频", "课堂实录", "视频", "微课", "优质课"],
        "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "几何画板"],
        "习题": ["习题", "题目", "练习题", "练习", "试题", "测试题"],
    }

    resource_types = []
    for resource_type, keywords in resource_type_keywords.items():
        if any(kw in query for kw in keywords):
            resource_types.append(resource_type)

    return resource_types


def _generate_query_variants_with_llm(query: str, llm: Any) -> List[str]:
    """使用大模型生成查询变体"""
    try:
        from langchain_core.messages import HumanMessage

        prompt = f"""请分析以下查询，生成适合搜索引擎检索的查询变体。

原始查询: {query}

## 任务

1. **识别所有知识点**：查询中可能包含多个知识点（如"指数函数和分层抽样"包含"指数函数"和"分层抽样"两个知识点）
   - **重要**：必须识别出所有数学知识点，包括但不限于：
     - 函数类：指数函数、对数函数、二次函数、三角函数等
     - 概率统计类：分层抽样、简单随机抽样、概率、统计等
     - 向量类：空间向量、平面向量等
     - 立体几何：直线与平面、平面与平面垂直等
     - 数列类：数列、等差数列、等比数列等
     - 复数类：复数、复数的运算等
     - 集合类：集合、集合的运算等
     - 不等式类：不等式、解不等式等

2. **识别内容要求**：如"教案"、"课件"、"习题"、"教学设计"等资源类型要求

3. **判断用户意图类型**：
   - **综合意图**：用户想要的是多个知识点**综合在一起**的资源（如"指数函数和分层抽样的教案"可能是综合这两部分的教案）
   - **分别意图**：用户想要的是每个知识点**分别**的资源（如"找指数函数的教案和分层抽样的课件"）

4. **区分要求类型**：
   - **共同要求**：所有知识点共用的要求（如"找A和B的教案"中"教案"是共同要求）
   - **分别要求**：每个知识点分别有不同的要求（如"找A的教案和B的课件"中"教案"和"课件"是分别要求）

## 示例

### 示例 1
输入："分别找一下指数函数和分层抽样的教案"
输出：
```json
{
  "knowledge_points": ["指数函数", "分层抽样"],
  "content_requirements": ["教案"],
  "intent_type": "separate",
  "per_point_requirements": {
    "指数函数": ["教案"],
    "分层抽样": ["教案"]
  },
  "shared_requirements": ["教案"],
  "query_variants": [
    "指数函数和分层抽样教案",
    "指数函数教案",
    "分层抽样教案",
    "指数函数和分层抽样的教学设计",
    "指数函数教学设计",
    "分层抽样教学设计"
  ]
}
```

### 示例 2
输入："找指数函数的教案和分层抽样的课件"
输出：
```json
{
  "knowledge_points": ["指数函数", "分层抽样"],
  "content_requirements": ["教案", "课件"],
  "intent_type": "separate",
  "per_point_requirements": {
    "指数函数": ["教案"],
    "分层抽样": ["课件"]
  },
  "shared_requirements": [],
  "query_variants": [
    "指数函数教案",
    "分层抽样课件",
    "指数函数的教案",
    "分层抽样的课件"
  ]
}
```

## 输出要求

请严格按照以下JSON格式输出，不要包含任何解释性文字：
```json
{
  "knowledge_points": ["知识点1", "知识点2"],
  "content_requirements": ["资源类型"],
  "intent_type": "combined"或"separate",
  "per_point_requirements": {
    "知识点1": ["要求1"],
    "知识点2": ["要求2"]
  },
  "shared_requirements": ["共同要求"],
  "query_variants": [
    "综合查询变体1（如：指数函数和分层抽样教案）",
    "分别查询变体1（如：指数函数教案）",
    "分别查询变体2（如：分层抽样教案）",
    "其他相关变体"
  ]
}
```

**重要**：
- 必须生成包含**所有知识点**的综合变体
- 必须为**每个知识点**生成分别变体
- query_variants数组中至少包含3个变体
- 不要包含任何解释性文字，只返回JSON格式
- 请确保JSON格式正确，否则会导致解析失败
"""

        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)

        # 解析响应（支持新的JSON格式）
        variants = []
        if hasattr(response, 'content'):
            content = response.content.strip()

            # 尝试解析JSON格式
            try:
                import json
                # 提取JSON部分（可能在```json...```之间）
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                parsed = json.loads(content)
                variants = parsed.get("query_variants", [])

                # 打印分析结果（用于调试）
                knowledge_points = parsed.get("knowledge_points", [])
                intent_type = parsed.get("intent_type", "unknown")
                print(f"🔍 LLM分析结果：知识点={knowledge_points}, 意图类型={intent_type}")
                print(f"🔍 LLM生成变体: {variants}")

            except (json.JSONDecodeError, KeyError) as e:
                # JSON解析失败，回退到旧的行解析方式
                print(f"⚠️ JSON解析失败，回退到行解析: {e}")
                for line in content.split('\n'):
                    line = line.strip()
                    if line and line not in variants:
                        # 移除可能的编号
                        if line and len(line) > 1 and line[0].isdigit() and (line[1] == '.' or line[1] == '、'):
                            line = line[2:].strip()
                        if line:
                            variants.append(line)

        # 确保包含原始查询
        if query not in variants:
            variants.insert(0, query)

        # 确保包含与"概率的基本性质"相关的变体
        if "概率" in query:
            prob_variants = ["概率的基本性质", "概率基本性质", "概率性质"]
            for variant in prob_variants:
                if variant not in variants:
                    variants.append(variant)
                # 确保包含带资源类型的变体
                if "教案" in query and f"{variant} 教案" not in variants:
                    variants.append(f"{variant} 教案")
                if "教学设计" in query and f"{variant} 教学设计" not in variants:
                    variants.append(f"{variant} 教学设计")

        # 限制变体数量（优化速度：从8减少到3）
        max_variants = 3
        return variants[:max_variants]
    except Exception as e:
        print(f"使用大模型生成查询变体失败: {e}")
        # 回退到硬编码方式
        return _generate_query_variants_fallback(query)


def _generate_query_variants_fallback(query: str) -> List[str]:
    """硬编码的查询变体生成（作为回退）"""
    variants = []

    # 提取核心主题
    core_topic = query
    resource_type = ""

    # 移除资源类型关键词
    resource_type_keywords = {
        "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课"],
        "课件": ["课件", "PPT", "幻灯片"],
        "习题": ["习题", "练习题", "试题"],
        "课例": ["课例", "教学视频", "视频"],
        "GGB": ["GGB", "GeoGebra"],
        "教学大纲": ["教学大纲", "大纲"]
    }

    # 识别并提取资源类型
    for rt, keywords in resource_type_keywords.items():
        for kw in keywords:
            if kw in query:
                resource_type = rt
                core_topic = core_topic.replace(kw, "").strip()
                break
        if resource_type:
            break

    # 生成变体
    if core_topic:
        # 基本变体
        variants.append(core_topic)

        # 添加资源类型
        if resource_type:
            variants.append(f"{core_topic} {resource_type}")

        # 同义词和不同表述
        synonym_map = {
            "概率的基本性质": ["概率性质", "概率的性质", "概率基本性质"],
            "面面垂直的判定定理": ["面面垂直判定定理", "面面垂直定理"],
            "分层抽样": ["分层随机抽样", "分层抽样方法"],
            "函数的奇偶性": ["函数奇偶性", "奇偶函数"],
            "三角函数": ["三角学", "三角函數"],
            "等差数列": ["等差序列", "等差数列公式"],
            "等比数列": ["等比序列", "等比数列公式"],
            "立体几何": ["空间几何", "立体几何学"],
            "解析几何": ["坐标几何", "解析几何学"],
            "导数": ["微分", "导函数"],
            "积分": ["积分学", "定积分"],
            "概率统计": ["概率与统计", "统计概率"],
            "线性代数": ["线代", "线性代数学"],
        }

        # 检查核心主题是否在同义词映射中
        for key, synonyms in synonym_map.items():
            if key in core_topic:
                for synonym in synonyms:
                    variant = core_topic.replace(key, synonym)
                    variants.append(variant)
                    if resource_type:
                        variants.append(f"{variant} {resource_type}")

        # 反向检查：如果同义词在核心主题中，也添加原始关键词
        for key, synonyms in synonym_map.items():
            for synonym in synonyms:
                if synonym in core_topic:
                    variant = core_topic.replace(synonym, key)
                    if variant not in variants:
                        variants.append(variant)
                        if resource_type:
                            variants.append(f"{variant} {resource_type}")

        # 生成更简洁的变体（移除"的"等虚词）
        simplified = core_topic.replace("的", "").strip()
        if simplified != core_topic:
            variants.append(simplified)
            if resource_type:
                variants.append(f"{simplified} {resource_type}")

        # 生成更详细的变体（添加相关术语）
        if "概率" in core_topic:
            related_terms = ["随机事件", "概率计算", "概率公式", "概率公理", "概率定理"]
            for term in related_terms:
                if term not in core_topic:
                    variants.append(f"{core_topic} {term}")
                    if resource_type:
                        variants.append(f"{core_topic} {term} {resource_type}")
        elif "函数" in core_topic:
            related_terms = ["函数性质", "函数图像", "函数应用"]
            for term in related_terms:
                if term not in core_topic:
                    variants.append(f"{core_topic} {term}")

        # 确保包含"概率的基本性质"相关变体
        if "概率" in core_topic:
            # 直接添加"概率的基本性质"相关变体
            basic_prob_variants = ["概率的基本性质", "概率基本性质", "概率性质"]
            for variant in basic_prob_variants:
                if variant not in variants:
                    variants.append(variant)
                    if resource_type:
                        variants.append(f"{variant} {resource_type}")

    # 去重并确保变体数量合理
    variants = list(set(variants))
    # 限制变体数量，避免过多（优化速度：从8减少到3）
    max_variants = 3
    if len(variants) > max_variants:
        # 优先保留包含"概率的基本性质"的变体
        prob_basic_variants = [v for v in variants if "概率的基本性质" in v or "概率基本性质" in v or "概率性质" in v]
        other_variants = [v for v in variants if v not in prob_basic_variants]
        # 保留概率相关变体，然后添加其他变体
        variants = prob_basic_variants + other_variants
        variants = variants[:max_variants]

    return variants


def _extract_themes_from_query(query: str) -> List[str]:
    """
    从查询中提取所有主题（知识点）

    Args:
        query: 用户查询

    Returns:
        主题列表
    """
    # 移除资源类型关键词
    query_without_resource_type = query
    resource_type_keywords = ["教案", "教学设计", "课件", "习题", "课例", "GGB", "教学大纲"]
    for keyword in resource_type_keywords:
        query_without_resource_type = query_without_resource_type.replace(keyword, "")

    # 移除"分别"等查询意图词
    # V317.0修复：按关键词长度排序，确保长短语优先被替换，避免部分匹配导致的错误
    intent_keywords = ["帮我找", "找一下", "请找", "分别", "各自", "分开", "帮我", "想要", "需要"]
    for keyword in intent_keywords:
        query_without_resource_type = query_without_resource_type.replace(keyword, "")

    # 处理中文逗号，替换为"和"
    query_without_resource_type = query_without_resource_type.replace("、", "和")

    # 常见主题连接词
    theme_connectors = ["和", "与", "及", "还有", "以及"]

    # 按连接词拆分
    themes = []
    # 首先处理所有中文逗号
    query_without_resource_type = query_without_resource_type.replace("、", "和")
    
    # 递归处理所有连接词
    def split_by_connectors(text):
        for connector in theme_connectors:
            if connector in text:
                parts = text.split(connector)
                # 处理第一个部分
                first_part = parts[0].strip()
                if first_part and len(first_part) > 1:
                    # 移除"的"后缀
                    if first_part.endswith("的"):
                        first_part = first_part[:-1].strip()
                    if first_part and len(first_part) > 1:
                        themes.append(first_part)
                # 递归处理剩余部分
                remaining = connector.join(parts[1:]).strip()
                if remaining:
                    split_by_connectors(remaining)
                return
        # 如果没有连接词，添加整个文本作为主题
        if text and len(text) > 1:
            # 移除"的"后缀
            if text.endswith("的"):
                text = text[:-1].strip()
            if text and len(text) > 1:
                themes.append(text)
    
    # 开始处理
    split_by_connectors(query_without_resource_type)

    # 如果没有连接词，尝试提取复合主题（如"复数的几何意义"）
    if not themes:
        # 尝试匹配常见的复合主题模式
        compound_patterns = [
            r"复数的几何意义",
            r"平面向量的坐标表示",
            r"直线与平面垂直",
            r"平面与平面垂直",
            r"函数的单调性",
            r"函数的奇偶性",
            r"指数函数",
            r"对数函数",
            r"二次函数",
            r"三角函数",
            r"分层抽样",
            r"简单随机抽样",
            r"离散型随机变量",
        ]
        for pattern in compound_patterns:
            match = re.search(pattern, query_without_resource_type)
            if match:
                themes.append(match.group())
                query_without_resource_type = query_without_resource_type.replace(match.group(), "")

        # 如果还是没找到，取整个查询作为主题
        if not themes:
            query_cleaned = query_without_resource_type.strip()
            if query_cleaned:
                themes.append(query_cleaned)

    return themes


def _ensure_separate_query_coverage(original_query: str, variants: List[str], resource_type: str = "") -> List[str]:
    """
    V312.0改进：确保分别查询时每个主题都有变体

    当检测到分别查询时，确保每个主题都有至少一个变体被生成。

    Args:
        original_query: 原始查询
        variants: 当前生成的变体列表
        resource_type: 资源类型（如"教案"、"课件"等）

    Returns:
        补充后的变体列表
    """
    # 检测是否为分别查询
    is_separate_query = any(keyword in original_query for keyword in ["分别", "各自", "分开"])
    if not is_separate_query:
        return variants

    print("V312.0检测到分别查询，确保每个主题都有变体...")

    # 提取查询中的所有主题
    themes = _extract_themes_from_query(original_query)
    print(f"V312.0提取到的主题: {themes}")

    # 检查每个主题是否至少有一个变体
    covered_themes = set()
    for variant in variants:
        for theme in themes:
            # 检查变体是否包含该主题（作为完整词或主要部分）
            if theme in variant or any(word in variant for word in theme.split()):
                covered_themes.add(theme)

    print(f"V312.0已覆盖的主题: {covered_themes}")

    # 为未覆盖的主题生成变体
    uncovered_themes = [t for t in themes if t not in covered_themes]
    if uncovered_themes:
        print(f"V312.0未覆盖的主题: {uncovered_themes}，生成补充变体...")
        for theme in uncovered_themes:
            # 为该主题生成基础变体
            theme_variant = theme
            variants.append(theme_variant)

            # 如果有资源类型，生成带资源类型的变体
            if resource_type:
                type_variant = f"{theme} {resource_type}"
                variants.append(type_variant)
                print(f"V312.0为'{theme}'生成变体: {theme_variant}, {type_variant}")
            else:
                print(f"V312.0为'{theme}'生成变体: {theme_variant}")

    # 去重
    variants = list(set(variants))

    print(f"V312.0最终变体列表: {variants}")
    return variants


import asyncio

def execute_search_tool_calls(
    tool_calls: List[Dict[str, Any]],
    search_tool: Any,
    original_user_query: str | None = None,
    llm: Any = None,
) -> Tuple[Dict[str, Any], str, int, List[str]]:
    all_resource_groups = []
    response_text = ""
    best_result_count = -1
    attempted_queries: List[str] = []

    for idx, tool_call in enumerate(tool_calls, start=1):
        if tool_call.get("name") != search_tool.name:
            print(f"⚠️ 跳过未知工具调用[{idx}]: {tool_call.get('name')}")
            continue
        tool_args = tool_call.get("args", {}) or {}

        # V62.0改进：增强查询扩展，使用大模型生成更多相关的查询变体
        print(f"检查查询变体数量: {len(tool_args.get('queries', []))}")

        # 检测是否为多主题查询（包含"和"、"与"、"及"等连接词，或多个逗号分隔的主题）
        # V307.0修复：优先使用original_user_query来检测多主题，因为tool_args.get("query")可能不包含原始连接词
        base_query = tool_args.get("query", "") or original_user_query or ""
        is_multi_theme_query = False
        is_separate_query = False
        # 优先使用original_user_query来检测多主题模式
        query_for_detection = original_user_query or base_query
        if query_for_detection:
            # 检测多主题模式：包含"和"、"与"、"及"连接多个主题，或包含多个资源类型
            multi_theme_connectors = ["和", "与", "及", "还有", "以及", "分别"]
            if any(connector in query_for_detection for connector in multi_theme_connectors):
                is_multi_theme_query = True
            # V312.0新增：检测分别查询
            if any(keyword in query_for_detection for keyword in ["分别", "各自", "分开"]):
                is_separate_query = True
            # 检测是否包含多个资源类型（教案、课件、习题等）
            resource_type_count = sum(1 for rt in ["教案", "课件", "习题", "课例", "GGB"] if rt in query_for_detection)
            if resource_type_count > 1:
                is_multi_theme_query = True

        # 提取资源类型
        resource_type = ""
        query_for_extraction = tool_args.get("query", "") or original_user_query or ""
        extracted_types = _extract_resource_types_from_query(query_for_extraction)
        if extracted_types:
            resource_type = extracted_types[0] if extracted_types else ""

        if not tool_args.get("queries") or len(tool_args.get("queries", [])) < 5:
            if base_query:
                print(f"准备生成查询变体，base_query: {base_query}")
                print(f"llm参数是否存在: {llm is not None}")
                print(f"多主题查询检测: {is_multi_theme_query}")
                print(f"分别查询检测: {is_separate_query}")
                if llm:
                    generated_variants = _generate_query_variants_with_llm(base_query, llm)
                    print(f"V62.0使用大模型生成查询变体: {len(generated_variants)} 个变体")
                    print(f"生成的变体: {generated_variants}")
                else:
                    generated_variants = _generate_query_variants_fallback(base_query)
                    print(f"V62.0使用回退方式生成查询变体: {len(generated_variants)} 个变体")
                    print(f"生成的变体: {generated_variants}")

                if generated_variants:
                    existing_queries = tool_args.get("queries", [])
                    # 合并现有查询和生成的变体，去重
                    combined_queries = list(set(existing_queries + generated_variants))

                    # V312.0改进：分别查询时确保每个主题都有变体
                    if is_separate_query and is_multi_theme_query:
                        combined_queries = _ensure_separate_query_coverage(
                            query_for_detection,
                            combined_queries,
                            resource_type
                        )
                        print(f"V312.0分别查询优化后变体: {combined_queries}")

                    # V302.1优化：多主题查询确保主题覆盖完整
                    # 核心主题变体通常是最高效的检索方式
                    if is_multi_theme_query and len(combined_queries) > 3:
                        # V302.0修复：确保原始查询始终被保留
                        original_query = tool_args.get("query", "") or original_user_query or ""
                        if original_query and original_query not in combined_queries:
                            combined_queries.insert(0, original_query)

                        # V313.0修复：分别查询时，确保每个主题至少有一个变体被保留
                        if is_separate_query:
                            # 提取所有主题
                            themes = _extract_themes_from_query(query_for_detection)
                            
                            # 构建最终变体列表，确保每个主题都有变体
                            final_variants = []
                            theme_covered = {theme: False for theme in themes}
                            
                            # 首先，为每个主题选择第一个匹配的变体
                            for variant in combined_queries:
                                for theme in themes:
                                    if theme in variant and not theme_covered[theme]:
                                        final_variants.append(variant)
                                        theme_covered[theme] = True
                                        break
                            
                            # 如果还有空位，添加其他变体
                            for variant in combined_queries:
                                if variant not in final_variants and len(final_variants) < 5:
                                    final_variants.append(variant)
                            
                            # 如果最终变体数量不足3个，添加原始查询
                            if len(final_variants) < 3 and original_query and original_query not in final_variants:
                                final_variants.insert(0, original_query)
                        else:
                            # 对于非分别查询，保持原有的优化逻辑
                            # 对于多主题查询，优先保留能体现多主题的变体
                            multi_theme_variants = [q for q in combined_queries if any(c in q for c in ["和", "与", "及", "分别"])]
                            single_theme_variants = [q for q in combined_queries if not any(c in q for c in ["和", "与", "及", "分别"])]

                            # 构建最终变体列表：原始多主题查询 + 每个主题的单查询变体
                            final_variants = []

                            # 1. 优先添加原始多主题查询（如果有）
                            for q in multi_theme_variants:
                                if q not in final_variants:
                                    final_variants.append(q)
                                    if len(final_variants) >= 2:
                                        break

                            # 2. 补充每个主题的单查询变体，确保每个主题都能被检索到
                            # V309.0修复：放宽冗余检查，确保每个主题都有机会被检索
                            existing_themes = set()
                            for q in single_theme_variants:
                                if len(final_variants) >= 5:
                                    break
                                # 检查这个变体是否包含新的主题信息
                                has_new_theme = False
                                for word in q.split():
                                    if len(word) > 2 and word not in existing_themes:
                                        has_new_theme = True
                                        existing_themes.add(word)
                                if has_new_theme:
                                    final_variants.append(q)

                            # 如果最终变体数量不足3个，添加原始查询
                            if len(final_variants) < 3 and original_query and original_query not in final_variants:
                                final_variants.insert(0, original_query)

                        tool_args["queries"] = final_variants
                        print(f"V302.1多主题优化：保留 {len(final_variants)} 个高效变体")
                        print(f"V302.1最终查询变体: {final_variants}")
                    else:
                        tool_args["queries"] = combined_queries[:3]  # 限制最多3个查询变体（优化速度）
                        print(f"V62.0增强查询扩展: 共 {len(tool_args['queries'])} 个查询变体")
                    print(f"最终查询变体: {tool_args['queries']}")
        else:
            print(f"查询变体数量足够，跳过生成")

        attempted_queries.extend(normalize_query_inputs(tool_args.get("query", ""), tool_args.get("queries", [])))

        # V61.0改进：如果工具调用中没有提供resource_types，自动从查询中提取
        if not tool_args.get("resource_types"):
            query_for_extraction = tool_args.get("query", "") or original_user_query or ""
            extracted_types = _extract_resource_types_from_query(query_for_extraction)
            if extracted_types:
                tool_args["resource_types"] = extracted_types
                print(f"V61.0自动识别资源类型: {extracted_types}")

        print(
            f"执行工具调用[{idx}]: "
            f"query={tool_args.get('query', '')!r}, queries={tool_args.get('queries', [])}, "
            f"resource_types={tool_args.get('resource_types', [])}"
        )



        # V314.0实现：分别查询时拆分为多个单主题查询
        # V316.0优化：并行执行 + 缓存机制
        if is_separate_query and is_multi_theme_query:
            print("V314.0检测到分别查询，将多主题查询拆分为多个单主题查询...")
            print("V316.0优化：并行执行多个主题查询 + 缓存机制")

            # 提取各个主题
            themes = _extract_themes_from_query(original_user_query or tool_args.get("query", ""))
            print(f"V314.0提取到的主题: {themes}")

            # 获取资源类型
            resource_types = tool_args.get("resource_types", [])

            # 为每个主题创建查询任务参数
            query_tasks = []
            for theme in themes:
                theme_query = f"{theme} {resource_types[0]}" if resource_types else theme
                single_theme_args = {
                    "query": theme_query,
                    "queries": [theme_query],
                    "resource_types": resource_types,
                    "theme": theme  # 传递主题信息
                }
                query_tasks.append(single_theme_args)

            # V316.0：并行执行所有主题查询
            print(f"V316.0 并行执行 {len(themes)} 个主题查询...")
            start_time = time.time()
            
            results = asyncio.run(_parallel_separate_query(search_tool, query_tasks))
            
            elapsed = time.time() - start_time
            print(f"V316.0 并行查询完成，耗时 {elapsed:.2f} 秒")

            # 处理并行查询结果
            for result in results:
                if result is None:
                    continue
                theme = result['theme']
                candidate_resources = result['resources']
                candidate_count = result['count']
                
                print(f"   V316.0 主题'{theme}'返回资源总数: {candidate_count}")

                if isinstance(candidate_resources, dict) and candidate_count > 0:
                    # 设置matched_themes字段
                    for category, resources in candidate_resources.items():
                        if isinstance(resources, list):
                            for resource in resources:
                                if isinstance(resource, dict):
                                    resource['matched_themes'] = [theme]
                    all_resource_groups.append(candidate_resources)
        else:
            # 并行处理查询变体的检索
            if tool_args.get("queries") and len(tool_args.get("queries", [])) > 1:
                print("=" * 60)
                print("=== 并行处理查询变体开始 ===")
                print(f"原始查询: {original_user_query}")
                print(f"查询变体数量: {len(tool_args.get('queries', []))}")
                print(f"查询变体: {tool_args.get('queries', [])}")
                print(f"资源类型: {tool_args.get('resource_types', [])}")
                print("=" * 60)

                # 为每个查询变体创建单独的工具参数
                query_args_list = []
                for query_variant in tool_args.get("queries", []):
                    variant_args = tool_args.copy()
                    variant_args["query"] = query_variant
                    variant_args["queries"] = [query_variant]  # 每个变体单独检索
                    query_args_list.append(variant_args)

                # 并行执行所有查询变体
                print("=== 开始并行执行查询变体 ===")
                results = asyncio.run(_parallel_invoke(search_tool, query_args_list))
                print("=== 并行执行完成 ===")

                # 处理并行结果
                for i, (variant_result, variant_args) in enumerate(zip(results, query_args_list)):
                    try:
                        parsed = json.loads(variant_result)
                    except Exception:
                        parsed = {}
                    if isinstance(parsed, dict):
                        candidate_resources = parsed.get("retrieved_resources")
                        candidate_count = count_retrieved_resources(candidate_resources)
                        print(f"   并行查询[{i+1}] '{variant_args.get('query', '')}' 返回资源总数: {candidate_count}")
                        if isinstance(candidate_resources, dict):
                            all_resource_groups.append(candidate_resources)
                            if candidate_count > best_result_count:
                                best_result_count = candidate_count
                                print(f"   并行查询[{i+1}] 成为当前最佳结果")
                                response_text = build_search_response_payload(
                                    query=original_user_query or variant_args.get("query", "") or "",
                                    resource_types=variant_args.get("resource_types", []),
                                    retrieved_resources=candidate_resources,
                                ).strip()
                    else:
                        print(f"   并行查询[{i+1}] 未返回有效结果")
            else:
                # 单查询变体，使用传统方式
                tool_result = search_tool.invoke(tool_args)
                try:
                    parsed = json.loads(tool_result)
                except Exception:
                    parsed = {}
                if isinstance(parsed, dict):
                    candidate_resources = parsed.get("retrieved_resources")
                    candidate_count = count_retrieved_resources(candidate_resources)
                    print(f"   工具调用[{idx}] 返回资源总数: {candidate_count}")
                    if isinstance(candidate_resources, dict):
                        all_resource_groups.append(candidate_resources)
                        if candidate_count > best_result_count:
                            best_result_count = candidate_count
                            print(f"   工具调用[{idx}] 成为当前最佳结果")
                            response_text = build_search_response_payload(
                                query=original_user_query or tool_args.get("query", "") or "",
                                resource_types=tool_args.get("resource_types", []),
                                retrieved_resources=candidate_resources,
                            ).strip()
                    else:
                        print(f"   工具调用[{idx}] 未超过当前最佳结果数 {best_result_count}")    # 合并所有工具调用的结果
    retrieved_resources = merge_retrieved_resources(all_resource_groups)
    final_count = count_retrieved_resources(retrieved_resources)
    print(f"   合并所有工具调用结果，总数: {final_count}")

    # 如果合并后的结果不为空，重新生成响应文本
    if final_count > 0:
        response_text = build_search_response_payload(
            query=original_user_query or "",
            resource_types=[],
            retrieved_resources=retrieved_resources,
        ).strip()

    return retrieved_resources, response_text, final_count, attempted_queries


async def _parallel_invoke(search_tool: Any, args_list: List[Dict[str, Any]]) -> List[str]:
    """
    并行执行多个搜索工具调用

    Args:
        search_tool: 搜索工具实例
        args_list: 工具参数列表

    Returns:
        工具调用结果列表
    """
    async def invoke_with_args(args):
        # 在单独的线程中执行同步调用，避免阻塞事件循环
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                search_tool.invoke,
                args
            )
        return result

    # 并行执行所有调用
    tasks = [invoke_with_args(args) for args in args_list]
    results = await asyncio.gather(*tasks)
    return results


async def _parallel_separate_query(search_tool: Any, query_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    V316.0：并行执行多个主题的分别查询（包含缓存机制）
    
    Args:
        search_tool: 搜索工具实例
        query_tasks: 查询任务参数列表，每个任务包含 {'query', 'queries', 'resource_types', 'theme'}
    
    Returns:
        结果列表，每个结果包含 {'theme', 'resources', 'count'}
    """
    async def query_with_cache(task):
        theme = task['theme']
        resource_types = task.get('resource_types', [])
        
        # 尝试从缓存获取结果
        cached = _get_cached_results(theme, resource_types)
        if cached is not None:
            return {
                'theme': theme,
                'resources': cached,
                'count': count_retrieved_resources(cached)
            }
        
        # 缓存未命中，执行实际查询
        args = {
            'query': task['query'],
            'queries': task['queries'],
            'resource_types': resource_types
        }
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                search_tool.invoke,
                args
            )
        
        try:
            parsed = json.loads(result)
        except Exception:
            parsed = {}
        
        if isinstance(parsed, dict):
            candidate_resources = parsed.get("retrieved_resources", {})
            candidate_count = count_retrieved_resources(candidate_resources)
            
            # 更新缓存（只缓存有结果的查询）
            if candidate_count > 0:
                _set_cache_results(theme, resource_types, candidate_resources)
            
            return {
                'theme': theme,
                'resources': candidate_resources,
                'count': candidate_count
            }
        
        return None
    
    # 并行执行所有查询任务
    tasks = [query_with_cache(task) for task in query_tasks]
    results = await asyncio.gather(*tasks)
    return results


def retry_search_until_results(
    llm_with_tools: Any,
    system_message: Any,
    conversation_messages: List[Any],
    initial_tool_calls: List[Dict[str, Any]],
    search_tool: Any,
    original_user_query: str,
    max_search_rounds: int = 3,
    llm: Any = None,
) -> Tuple[Dict[str, Any], str, int, List[str]]:
    # 优先使用传入的llm参数，如果没有则从llm_with_tools中提取
    if llm is None:
        llm = getattr(llm_with_tools, "llm", None)

    retrieved_resources, response_text, best_result_count, attempted_queries = execute_search_tool_calls(
        initial_tool_calls,
        search_tool=search_tool,
        original_user_query=original_user_query,
        llm=llm,
    )

    current_round = 1
    while not has_any_retrieved_resources(retrieved_resources) and current_round < max_search_rounds:
        next_round = current_round + 1
        unique_attempted = []
        seen_queries = set()
        for query in attempted_queries:
            if query and query not in seen_queries:
                seen_queries.add(query)
                unique_attempted.append(query)

        print(f"🔁 SEARCH_AGENT_NODE 第{current_round}轮检索为空，发起第{next_round}轮多 query 重试")
        retry_message = HumanMessage(
            content=(
                f"前 {current_round} 轮 search_resources_tool 检索都没有拿到结果。\n"
                f"原始用户请求：{original_user_query}\n"
                f"之前已经尝试过的 query：{unique_attempted}\n"
                "请重新判断是否需要再次调用 search_resources_tool。\n"
                "如果再次调用，必须保留用户原始语义，并提供 2-4 条新的互补 queries。\n"
                "新的 queries 要尽量避免与上面已经试过的重复，优先覆盖更完整主题、自然中文表达、不同短语组合。\n"
                "不要直接回答'没找到'，先完成这一轮重试。"
            )
        )
        retry_response = llm_with_tools.invoke([system_message, *conversation_messages, retry_message])
        retry_tool_calls = getattr(retry_response, "tool_calls", None) or []
        print(f"🧰 SEARCH_AGENT_NODE 第{next_round}轮重试 tool_calls 数量: {len(retry_tool_calls)}")
        if not retry_tool_calls:
            break

        retry_resources, retry_response_text, retry_best_result_count, retry_attempted_queries = execute_search_tool_calls(
            retry_tool_calls,
            search_tool=search_tool,
            original_user_query=original_user_query,
            llm=llm,
        )
        attempted_queries.extend(retry_attempted_queries)
        if retry_best_result_count > best_result_count:
            best_result_count = retry_best_result_count
            retrieved_resources = retry_resources
            response_text = retry_response_text
        current_round = next_round

    return retrieved_resources, response_text, best_result_count, attempted_queries


def extract_exercise_details(retrieved_resources: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从 retrieved_resources 中提取习题的结构化详情。

    后端检索链路中 _process_exercise_resource 已将题干、解析、知识点等
    独立字段写入 resource 字典，但最终展示时被拼接成 content 字符串。
    本函数将这些结构化字段提取为前端可直接使用的干净列表。

    Args:
        retrieved_resources: 检索结果字典（含 exercise_resources 等分类）

    Returns:
        习题详情列表，每条包含：
        - title: 习题标题
        - question: 题干文本
        - answer: 解析/答案
        - question_type: 题目类型（选择题/解答题/证明题等）
        - knowledge_tags: 知识点标签
        - difficulty: 难度（1-5）
        - question_image_url: 题目图片链接（如有）
        - answer_image_url: 答案图片链接（如有）
        - question_format: "text" 或 "image"
        - answer_format: "text"、"latex" 或 "image"
        - relevance: 相关性分数
        - matched_themes: 匹配的主题列表
    """
    exercise_resources = retrieved_resources.get("exercise_resources", [])
    if not exercise_resources:
        # 兼容旧版 state 中的其他 exercise 键名
        for key in ["exercise", "exercises", "习题资源"]:
            if key in retrieved_resources:
                exercise_resources = retrieved_resources[key]
                break

    details = []
    for resource in exercise_resources:
        if not isinstance(resource, dict):
            continue

        detail = {
            "title": resource.get("title", ""),
            "question": resource.get("question", ""),
            "answer": resource.get("answer", ""),
            "question_type": resource.get("question_type", ""),
            "knowledge_tags": resource.get("knowledge_tags", ""),
            "difficulty": resource.get("difficulty", ""),
            "usage_scene": resource.get("usage_scene", ""),
            "question_image_url": resource.get("question_image_url", ""),
            "answer_image_url": resource.get("answer_image_url", ""),
            "question_format": resource.get("question_format", "text"),
            "answer_format": resource.get("answer_format", "text"),
            "has_question_image": resource.get("has_question_image", False),
            "has_answer_image": resource.get("has_answer_image", False),
            "is_image_exercise": resource.get("is_image_exercise", False),
            "relevance": resource.get("relevance", 0),
            "matched_themes": resource.get("matched_themes", []),
            "match_level": resource.get("match_level", ""),
            "source": resource.get("source", ""),
            "filename": resource.get("filename", ""),
        }
        details.append(detail)

    return details
