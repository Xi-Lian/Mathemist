import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.intent.service import IntentAnalyzer
from app.core.retrieval.methods.extract_theme_with_llm import extract_theme_with_llm
from app.core.retrieval.methods.enhance_query import enhance_query
from app.core.retrieval.retrieve_helpers.filters import get_retrieval_budget
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试查询
query = "找一下关于分类加法计数原理的练习课课件"

print("=" * 100)
print(f"测试查询: {query}")
print("=" * 100)
print()

# 1. 测试意图分析
print("=== 1. 意图分析 ===")
analyzer = IntentAnalyzer()
intent_result = analyzer.analyze(query)
print(f"主要意图: {intent_result.get('intent')}")
print(f"资源类型: {intent_result.get('resource_types')}")
print(f"LLM原始输出: {intent_result.get('llm_response', 'N/A')}")
print()

# 2. 测试主题提取
print("=== 2. 主题提取 ===")
has_resource_type = len(intent_result.get('resource_types', [])) > 0
try:
    theme_result = extract_theme_with_llm(query, has_resource_type=has_resource_type)
    print(f"主题结果: {theme_result}")
except Exception as e:
    print(f"主题提取出错: {e}")
    import traceback
    traceback.print_exc()
print()

# 3. 测试查询增强
print("=== 3. 查询增强 ===")
try:
    enhanced_query = enhance_query(query, intent_result.get('resource_types', []))
    print(f"增强后查询: {enhanced_query}")
except Exception as e:
    print(f"查询增强出错: {e}")
print()

# 4. 测试检索预算
print("=== 4. 检索预算 ===")
budget = get_retrieval_budget(intent_result.get('resource_types', []))
print(f"检索预算: {budget}")
print()
