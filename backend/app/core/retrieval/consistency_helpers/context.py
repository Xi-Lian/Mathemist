from .._shared import *


GENERAL_FUNCTION_PROPERTIES = [
    "函数的单调性", "函数的奇偶性", "函数的周期性", "函数的值域", "函数的定义域",
    "函数的图像", "函数的性质", "函数概念", "函数的概念", "函数的应用",
]
SUBJECTIVE_WORDS = ["基础题", "难题", "冲刺", "提高", "简单", "中等", "综合", "基础", "提高题", "压轴题"]
GENERIC_THEMES = ["函数", "数学", "教学", "函数的应用", "高中数学", "数学教学"]
GENERAL_CHAPTERS = ["函数的概念", "函数的应用", "函数性质", "函数图像", "函数基础", "数学基础", "代数基础", "几何基础"]


def build_consistency_context(metadata, core_theme, doc, query, relevance):
    themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    print(f"\n   🔍 知识点一致性检查 - core_theme: '{core_theme}'")
    print(f"   🔍 解析出的主题: {themes}")
    print(f"   🔍 查询: '{query}'")
    print(f"   🔍 相关性: {relevance}")

    source_file = metadata.get("source_file", "")
    title = metadata.get("title", "")
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "") or metadata.get("knowledge_tags", "")
    question_content = metadata.get("题目描述", "") + metadata.get("题干", "") + metadata.get("content", "") + doc
    question_file = metadata.get("题目文件名", "")
    difficulty = metadata.get("难度（1-5）", "") or metadata.get("难度", "")
    analysis = metadata.get("解析", "")
    usage_scene = metadata.get("适用场景", "")
    all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content} {difficulty} {analysis} {usage_scene}"

    return {
        "themes": themes,
        "source_file": source_file,
        "title": title,
        "knowledge_tags": knowledge_tags,
        "question_content": question_content,
        "question_file": question_file,
        "all_info": all_info,
    }


def should_skip_consistency_check(core_theme, relevance, themes):
    if relevance > 0.8:
        print(f"   ✅ 高相关性资源：相关性分数{relevance}，放宽过滤条件")
        return True

    if any(prop in core_theme for prop in GENERAL_FUNCTION_PROPERTIES):
        print(f"   ✅ 通用函数性质: '{core_theme}' 适用于所有函数类型")
        return True

    if any(word in core_theme for word in SUBJECTIVE_WORDS):
        print(f"   ✅ 主观词汇: '{core_theme}' 是主观词汇，跳过严格匹配")
        return True

    specific_knowledge_points = [theme for theme in themes if theme not in GENERIC_THEMES]
    if not specific_knowledge_points:
        print("   📝 未识别到具体知识点，跳过严格过滤")
        return True

    return False


def extract_specific_knowledge_points(themes):
    return [theme for theme in themes if theme not in GENERIC_THEMES]
