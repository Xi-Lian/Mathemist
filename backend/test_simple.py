#!/usr/bin/env python3
# 简单测试搜索结果处理

import sys
import os

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.nodes import search_result_processing_node, retrieve_resources

class TestState:
    """测试用的状态类"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def test_simple():
    """简单测试"""
    print("====================================")
    print("🔍 简单测试")
    print("====================================")
    
    query = "二次函数"
    print(f"\n查询: {query}")
    print("-" * 60)
    
    try:
        # 调用资源检索节点
        retrieve_result = retrieve_resources(query, "search")
        print(f"✅ 资源检索成功")
        print(f"检索到的资源类型: {list(retrieve_result.keys())}")
        
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
        error = process_result.get('error', None)
        
        print(f"\n📋 处理结果:")
        print(search_results)
        
        if error:
            print(f"\n❌ 错误信息: {error}")
        else:
            print(f"\n✅ 处理成功，无错误")
            
    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n====================================")
    print("🔍 测试完成")
    print("====================================")

if __name__ == "__main__":
    test_simple()
