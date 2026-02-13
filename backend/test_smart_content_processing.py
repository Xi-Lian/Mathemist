#!/usr/bin/env python3
# 测试智能内容处理效果

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

def test_smart_content_processing():
    """测试智能内容处理效果"""
    print("====================================")
    print("🔍 测试智能内容处理效果")
    print("====================================")
    
    # 测试查询：查找不同类型的资源
    test_queries = [
        "二次函数习题",
        "三角函数教案",
        "函数图像可视化"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 60)
        
        try:
            # 调用资源检索节点
            retrieve_result = retrieve_resources(query, "search")
            print(f"✅ 资源检索成功")
            
            # 创建测试状态
            test_state = TestState(
                retrieved_resources=retrieve_result,
                intent="search"
            )
            
            # 调用搜索结果处理节点
            process_result = search_result_processing_node(test_state)
            print(f"✅ 搜索结果处理成功")
            
            # 显示处理结果
            search_results = process_result.get('search_results', '')
            print("\n📋 处理结果:")
            print(search_results)
            
            # 分析结果
            if len(search_results) > 500:
                print(f"\n✅ 内容长度适中: {len(search_results)} 字符")
            else:
                print(f"\n⚠️  内容较短: {len(search_results)} 字符")
            
            # 检查是否包含结构化信息
            if "【" in search_results and "】" in search_results:
                print("✅ 包含结构化分类信息")
            else:
                print("❌ 缺少结构化分类信息")
                
        except Exception as e:
            print(f"❌ 测试出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n====================================")
    print("🔍 测试完成")
    print("====================================")

if __name__ == "__main__":
    test_smart_content_processing()
