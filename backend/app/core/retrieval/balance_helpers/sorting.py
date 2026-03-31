from .._shared import *


GENERAL_CONCEPTS = [
    "函数的单调性", "函数的奇偶性", "函数的周期性", "函数的值域", "函数的定义域",
    "函数的图像", "函数的性质", "函数的概念", "函数的应用", "函数的零点", "二分法",
    "定义域", "值域", "单调性", "奇偶性", "周期性", "对称性",
    "集合", "不等式", "方程", "导数", "积分", "极限", "概率", "统计", "期望", "方差", "向量", "复数", "数列",
]

GENERAL_CHAPTERS = [
    "第三章-函数的概念", "第三章", "函数的概念", "函数的性质",
    "第一章-集合", "第一章", "集合",
    "第二章-不等式", "第二章", "不等式",
]


def sort_resources_for_balance(retriever, resources, core_theme, query):
    is_general_concept_query = any(concept in core_theme for concept in GENERAL_CONCEPTS)
    print(f"   🔍 V31.0 _balance_resource_distribution 被调用，core_theme='{core_theme}', resources数量={len(resources)}")
    print(f"   🔍 V31.0 is_general_concept_query={is_general_concept_query}")

    if "单调性" in core_theme and "证明题" in query:
        print("   🔍 V46.0单调性证明题查询: 不使用通用概念优先排序")
        is_general_concept_query = False

    if is_general_concept_query:
        print(f"   🔍 V31.0检测到通用概念查询: '{core_theme}'，启用优先排序")
        for resource in resources:
            source_file = resource.get("source", "") or resource.get("metadata", {}).get("source_file", "")
            priority_score = 0
            if any(chapter in source_file for chapter in GENERAL_CHAPTERS):
                priority_score += 100
                print(f"      ✅ V31.0通用章节资源: '{resource.get('title', '未知')[:30]}' 来自 {source_file[:50]}")

            knowledge_tags = resource.get("metadata", {}).get("知识点", "") or resource.get("metadata", {}).get("知识点标签", "")
            specific_function_types = retriever.config_loader.get_all_function_types()
            if not any(func_type in knowledge_tags for func_type in specific_function_types):
                priority_score += 50
            else:
                priority_score -= 30
            resource["priority_score"] = priority_score

        resources_sorted = sorted(
            resources,
            key=lambda x: (-x.get("priority_score", 0), -x.get("is_core_match", False), -x.get("relevance", 0), -x.get("matched_theme_count", 0)),
        )
        print("   ✅ V31.0优先排序完成，通用概念资源优先")
        return resources_sorted

    for resource in resources:
        content = resource.get("content", "") or resource.get("metadata", {}).get("content", "") or ""
        title = resource.get("title", "") or resource.get("metadata", {}).get("title", "") or ""
        metadata_str = str(resource) or str(resource.get("metadata", {})) or ""
        resource["contains_core_theme"] = bool(core_theme and (core_theme in content or core_theme in title or core_theme in metadata_str))

    return sorted(resources, key=lambda x: (-x.get("contains_core_theme", False), -x.get("relevance", 0)))
