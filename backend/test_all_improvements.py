#!/usr/bin/env python3
# 测试所有改进功能

import sys
import os

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.nodes import search_result_processing_node, retrieve_resources, classify_resource

class TestState:
    """测试用的状态类"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def test_all_improvements():
    """测试所有改进功能"""
    print("====================================")
    print("🔍 测试所有改进功能")
    print("====================================")
    
    # 测试1：资源分类
    print("\n【测试1：资源分类】")
    print("-" * 60)
    
    test_cases = [
        ("教案.md", "教学目标：理解二次函数", "lesson_plan"),
        ("教学大纲.md", "课程标准：高中数学", "syllabus"),
        ("课件.pptx", "演示文稿", "courseware"),
        ("课例.md", "课堂实录", "lesson_case"),
        ("ggb.ggb", "动态数学", "ggb"),
        ("习题.md", "选择题", "exercise"),
        ("理论卡片.md", "教学启发", "theory")
    ]
    
    for source, content, expected in test_cases:
        result = classify_resource(source, content)
        status = "✅" if result == expected else "❌"
        print(f"{status} 源: {source}, 结果: {result}, 期望: {expected}")
    
    # 测试2：搜索结果处理
    print("\n【测试2：搜索结果处理】")
    print("-" * 60)
    
    test_queries = [
        "二次函数",
        "三角函数",
        "教学大纲"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        try:
            # 调用资源检索节点
            retrieve_result = retrieve_resources(query, "search")
            print(f"✅ 资源检索成功")
            
            # 创建测试状态
            test_state = TestState(
                retrieved_resources=retrieve_result,
                intent="search",
                user_input=query
            )
            
            # 调用搜索结果处理节点
            process_result = search_result_processing_node(test_state)
            print(f"✅ 搜索结果处理成功")
            
            # 显示处理结果
            search_results = process_result.get('search_results', '')
            print(f"\n📋 处理结果:")
            print(search_results)
            
            # 分析结果
            print(f"\n📊 结果分析:")
            print(f"   - 内容长度: {len(search_results)} 字符")
            print(f"   - 包含分类: {'是' if '【' in search_results and '】' in search_results else '否'}")
            print(f"   - 包含文件路径: {'是' if '文件路径' in search_results else '否'}")
            
            # 检查是否过滤了理论卡片
            if "理论资源" in search_results:
                print(f"   ⚠️  理论卡片未被过滤")
            else:
                print(f"   ✅ 理论卡片已过滤")
            
            # 检查是否包含新资源类型
            new_types = []
            if "课件资源" in search_results:
                new_types.append("课件")
            if "课例资源" in search_results:
                new_types.append("课例")
            if "GGB资源" in search_results:
                new_types.append("GGB")
            if "教学大纲" in search_results:
                new_types.append("教学大纲")
            
            if new_types:
                print(f"   ✅ 包含新资源类型: {', '.join(new_types)}")
            else:
                print(f"   ℹ️  未包含新资源类型")
                
        except Exception as e:
            print(f"❌ 测试出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n====================================")
    print("🔍 测试完成")
    print("====================================")

if __name__ == "__main__":
    test_all_improvements()
