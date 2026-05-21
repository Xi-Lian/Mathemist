import sys
sys.path.insert(0, 'app')

from core.retrieval.retrieve_helpers.single_theme import _passes_unified_semantic_gate, _normalize_match_text, _extract_theme_keywords

# 测试语义门控对课件资源的放宽效果
print("测试语义门控对课件资源的放宽效果")
print("=" * 60)

# 核心主题
core_theme = "组合数"
theme_keywords = _extract_theme_keywords(core_theme)
print(f"核心主题: '{core_theme}'")
print(f"提取的关键词: {theme_keywords}")

# 测试课件资源
test_cases = [
    {
        "title": "6.2.3　组合+6.2.4　组合数",
        "source_file": "概率与统计-课件汇总.xlsx",
        "teaching_use": "练习课课件",
        "resource_type": "courseware",
        "distance": 0.9127,  # 实际检索的相似度距离
        "doc": "6.2.3　组合　6.2.4　组合数"
    },
    {
        "title": "组合数的综合应用(习题课)",
        "source_file": "概率与统计-课件汇总.xlsx",
        "teaching_use": "练习课课件",
        "resource_type": "courseware",
        "distance": 0.9094,
        "doc": "组合数的综合应用"
    },
    {
        "title": "第六章  6.2.3组合& 6.2.4组合数",
        "source_file": "概率与统计-课件汇总.xlsx",
        "teaching_use": "新授课课件",
        "resource_type": "courseware",
        "distance": 0.9127,
        "doc": "6.2.3　组合　6.2.4　组合数"
    },
    {
        "title": "排列与组合的综合应用",
        "source_file": "概率与统计-课件汇总.xlsx",
        "teaching_use": "练习课课件",
        "resource_type": "courseware",
        "distance": 0.9094,
        "doc": "排列与组合的综合应用"
    }
]

print("\n测试课件资源：")
for i, test_case in enumerate(test_cases):
    meta = {
        "title": test_case["title"],
        "source_file": test_case["source_file"],
        "教学用途": test_case["teaching_use"],
        "resource_type": test_case["resource_type"]
    }
    
    result = _passes_unified_semantic_gate(
        query="组合数 练习课 课件",
        core_theme=core_theme,
        doc=test_case["doc"],
        meta=meta,
        distance=test_case["distance"],
        kg=None
    )
    
    status = "✅ 通过" if result else "❌ 拒绝"
    print(f"\n{i+1}. {status}")
    print(f"   标题: {test_case['title']}")
    print(f"   教学用途: {test_case['teaching_use']}")
    print(f"   距离: {test_case['distance']:.4f}")
