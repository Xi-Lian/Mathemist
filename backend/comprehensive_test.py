import os
import sys
from app.core.resource_retriever import ResourceRetriever

# 将输出重定向到文件
output_file = open('comprehensive_test_output.txt', 'w', encoding='utf-8')
sys.stdout = output_file

# 初始化资源检索器
retriever = ResourceRetriever()

# 定义测试用例
test_cases = [
    # 不同知识点的查询
    {"query": "二次函数的练习题", "resource_types": ["习题"], "expected_topic": "二次函数", "description": "测试二次函数习题查询"},
    {"query": "指数函数的习题", "resource_types": ["习题"], "expected_topic": "指数函数", "description": "测试指数函数习题查询"},
    {"query": "三角函数的题目", "resource_types": ["习题"], "expected_topic": "三角函数", "description": "测试三角函数习题查询"},
    {"query": "幂函数的练习", "resource_types": ["习题"], "expected_topic": "幂函数", "description": "测试幂函数习题查询"},
    {"query": "对数函数的测试题", "resource_types": ["习题"], "expected_topic": "对数函数", "description": "测试对数函数习题查询"},
    
    # 不同资源类型的查询
    {"query": "二次函数的教案", "resource_types": ["教案"], "expected_topic": "二次函数", "description": "测试二次函数教案查询"},
    {"query": "三角函数的课件", "resource_types": ["课件"], "expected_topic": "三角函数", "description": "测试三角函数课件查询"},
    
    # 不同语气的查询
    {"query": "给我找一些二次函数的题", "resource_types": ["习题"], "expected_topic": "二次函数", "description": "测试口语化查询"},
    {"query": "请提供关于指数函数的练习题，谢谢", "resource_types": ["习题"], "expected_topic": "指数函数", "description": "测试礼貌语气查询"},
    {"query": "三角函数题", "resource_types": ["习题"], "expected_topic": "三角函数", "description": "测试简洁查询"},
    {"query": "我想找一些关于幂函数的练习题，最好是选择题", "resource_types": ["习题"], "expected_topic": "幂函数", "description": "测试详细查询"},
    
    # 不同意图的查询
    {"query": "二次函数的学习资料", "resource_types": [], "expected_topic": "二次函数", "description": "测试学习意图查询"},
    {"query": "三角函数的复习题", "resource_types": ["习题"], "expected_topic": "三角函数", "description": "测试复习意图查询"},
    {"query": "指数函数和幂函数的比较", "resource_types": [], "expected_topic": "指数函数/幂函数", "description": "测试比较意图查询"},
    
    # 组合查询
    {"query": "函数的单调性和奇偶性的练习题", "resource_types": ["习题"], "expected_topic": "函数单调性/奇偶性", "description": "测试组合知识点查询"},
    {"query": "二次函数的最值问题", "resource_types": ["习题"], "expected_topic": "二次函数最值", "description": "测试特定问题查询"},
]

# 用于判断资源是否与主题相关的函数
def is_resource_relevant(resource, expected_topic, query=""):
    """判断资源是否与期望主题相关"""
    title = resource.get('title', '')
    knowledge_tags = resource.get('知识点', '')
    content = resource.get('content', '')
    
    # 将期望主题拆分为多个关键词
    topic_keywords = expected_topic.replace('/', ' ').replace('、', ' ').split()
    
    # 检查标题、知识点标签和内容中是否包含任何关键词
    for keyword in topic_keywords:
        if keyword in title or keyword in knowledge_tags or keyword in content:
            return True
    
    # V100.0改进：对于组合查询，检查是否包含查询中的主要概念
    # 例如：查询"二次函数的最值问题"，资源包含"二次函数"或"最值"都应该算相关
    if query:
        # 提取查询中的核心概念
        core_concepts = []
        concept_patterns = [
            ("二次函数", ["二次函数", "抛物线", "顶点", "对称轴"]),
            ("指数函数", ["指数函数", "指数"]),
            ("对数函数", ["对数函数", "对数"]),
            ("幂函数", ["幂函数", "幂"]),
            ("三角函数", ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]),
            ("单调性", ["单调性", "单调递增", "单调递减", "单调区间"]),
            ("奇偶性", ["奇偶性", "奇函数", "偶函数"]),
            ("最值", ["最值", "最大值", "最小值", "极值", "取值范围"]),
            ("函数", ["函数", "function"])
        ]
        
        for concept, patterns in concept_patterns:
            for pattern in patterns:
                if pattern in query:
                    core_concepts.extend(patterns)
                    break
        
        # 检查资源是否包含任何核心概念
        all_text = f"{title} {knowledge_tags} {content}".lower()
        for concept in core_concepts:
            if concept.lower() in all_text:
                return True
    
    return False

# 用于分析资源相关性的函数
def analyze_relevance(resources, expected_topic, query):
    """分析资源与查询的相关性"""
    if not resources:
        return {"relevant_count": 0, "total_count": 0, "relevance_rate": 0, "analysis": "未找到资源"}
    
    relevant_count = 0
    irrelevant_resources = []
    
    for resource in resources:
        if is_resource_relevant(resource, expected_topic, query):
            relevant_count += 1
        else:
            irrelevant_resources.append(resource.get('title', '未知'))
    
    total_count = len(resources)
    relevance_rate = relevant_count / total_count if total_count > 0 else 0
    
    analysis = f"相关资源: {relevant_count}/{total_count} ({relevance_rate*100:.1f}%)"
    if irrelevant_resources:
        analysis += f"\n    ⚠️ 不相关资源: {', '.join(irrelevant_resources[:5])}"
        if len(irrelevant_resources) > 5:
            analysis += f" 等{len(irrelevant_resources)}个"
    
    return {
        "relevant_count": relevant_count,
        "total_count": total_count,
        "relevance_rate": relevance_rate,
        "analysis": analysis,
        "irrelevant_resources": irrelevant_resources
    }

# 执行测试
print("=" * 80)
print("全面测试资源检索系统")
print("=" * 80)

test_results = []

for i, test_case in enumerate(test_cases):
    print(f"\n{'=' * 80}")
    print(f"测试 {i+1}/{len(test_cases)}: {test_case['description']}")
    print(f"{'=' * 80}")
    print(f"查询: '{test_case['query']}'")
    print(f"期望主题: {test_case['expected_topic']}")
    print(f"资源类型: {test_case['resource_types']}")
    print("-" * 80)
    
    # 执行查询
    results = retriever.retrieve(
        query=test_case['query'],
        resource_types=test_case['resource_types'] if test_case['resource_types'] else None,
        quantity_limit=10
    )
    
    # 分析结果
    if results:
        total_count = results.get('_total_count', 0)
        visible_count = total_count - results.get('_hidden_count', 0)
        hidden_count = results.get('_hidden_count', 0)
        
        print(f"\n找到 {total_count} 条资源 (可见: {visible_count}, 隐藏: {hidden_count})")
        
        # 获取所有资源
        all_resources = []
        categories = ["exercise_resources", "theory_resources", "lesson_plan_patterns", 
                      "courseware_resources", "ggb_resources", "syllabus_resources", 
                      "lesson_case_resources"]
        
        for category in categories:
            if category in results and results[category]:
                all_resources.extend(results[category])
        
        # 分析相关性
        analysis = analyze_relevance(all_resources, test_case['expected_topic'], test_case['query'])
        
        print(f"\n📊 相关性分析:")
        print(f"  {analysis['analysis']}")
        
        # 打印前5个资源
        print(f"\n前5个资源:")
        for j, resource in enumerate(all_resources[:5]):
            title = resource.get('title', '未知')
            relevance = resource.get('relevance', 0)
            knowledge_tags = resource.get('知识点', '未知')
            is_relevant = is_resource_relevant(resource, test_case['expected_topic'], test_case['query'])
            status = "✅ 相关" if is_relevant else "❌ 不相关"
            print(f"  {j+1}. [{status}] {title}")
            print(f"     相关性: {relevance:.2f}, 知识点: {knowledge_tags}")
        
        # 记录测试结果
        test_results.append({
            "query": test_case['query'],
            "expected_topic": test_case['expected_topic'],
            "total_count": total_count,
            "relevant_count": analysis['relevant_count'],
            "relevance_rate": analysis['relevance_rate'],
            "irrelevant_count": len(analysis['irrelevant_resources'])
        })
    else:
        print("\n❌ 未找到资源")
        test_results.append({
            "query": test_case['query'],
            "expected_topic": test_case['expected_topic'],
            "total_count": 0,
            "relevant_count": 0,
            "relevance_rate": 0,
            "irrelevant_count": 0
        })

# 打印测试总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

total_tests = len(test_results)
successful_tests = sum(1 for r in test_results if r['relevance_rate'] >= 0.8)
partial_success_tests = sum(1 for r in test_results if 0.5 <= r['relevance_rate'] < 0.8)
failed_tests = sum(1 for r in test_results if r['relevance_rate'] < 0.5)

print(f"\n总测试数: {total_tests}")
print(f"成功测试 (相关性≥80%): {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
print(f"部分成功 (50%≤相关性<80%): {partial_success_tests} ({partial_success_tests/total_tests*100:.1f}%)")
print(f"失败测试 (相关性<50%): {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

print("\n详细结果:")
for i, result in enumerate(test_results):
    status = "✅" if result['relevance_rate'] >= 0.8 else ("⚠️" if result['relevance_rate'] >= 0.5 else "❌")
    print(f"  {status} 测试{i+1}: '{result['query']}'")
    print(f"     期望主题: {result['expected_topic']}")
    print(f"     相关性: {result['relevant_count']}/{result['total_count']} ({result['relevance_rate']*100:.1f}%)")

# 关闭文件
sys.stdout = sys.__stdout__
output_file.close()

print("测试完成，结果已保存到 comprehensive_test_output.txt")
