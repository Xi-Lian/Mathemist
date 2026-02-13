#!/usr/bin/env python3
# 综合测试脚本 - 测试nodes.py中的所有函数

import sys
import os
import json
from typing import Dict, Any

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.nodes import (
    get_chroma_client,
    get_embedding_model,
    get_model,
    classify_resource,
    retrieve_resources,
    intent_understanding_node,
    resource_retrieval_node,
    lesson_plan_generation_node,
    visualization_suggestion_node,
    search_result_processing_node,
    extract_filename_from_content,
    response_formatting_node
)

class TestState:
    """测试用的状态类"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class TestAllFunctions:
    """测试所有函数的类"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def run_test(self, test_name, test_function):
        """运行单个测试"""
        self.total_tests += 1
        print(f"\n{'='*60}")
        print(f"🔍 测试: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_function()
            print(f"✅ 测试通过: {test_name}")
            self.passed_tests += 1
            self.test_results.append({
                "test": test_name,
                "status": "passed",
                "result": result
            })
            return True
        except Exception as e:
            print(f"❌ 测试失败: {test_name}")
            print(f"   错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results.append({
                "test": test_name,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def test_get_chroma_client(self):
        """测试get_chroma_client函数"""
        client = get_chroma_client()
        print(f"✅ 获取到ChromaDB客户端: {type(client).__name__}")
        return f"ChromaDB客户端类型: {type(client).__name__}"
    
    def test_get_embedding_model(self):
        """测试get_embedding_model函数"""
        model = get_embedding_model()
        print(f"✅ 获取到Embedding模型: {type(model).__name__}")
        return f"Embedding模型类型: {type(model).__name__}"
    
    def test_get_model(self):
        """测试get_model函数"""
        models = []
        for task in ["default", "intent"]:
            model = get_model(task)
            model_type = type(model).__name__
            models.append(f"任务: {task}, 模型: {model_type}")
            print(f"✅ 获取到{task}模型: {model_type}")
        return models
    
    def test_classify_resource(self):
        """测试classify_resource函数"""
        test_cases = [
            ("教案.md", "教学目标", "lesson_plan"),
            ("理论卡片.md", "知识点", "theory"),
            ("可视化示例.md", "图表", "visualization"),
            ("习题.md", "选择题", "exercise"),
            ("其他.md", "内容", "other")
        ]
        
        results = []
        for source, content, expected in test_cases:
            result = classify_resource(source, content)
            status = "✅" if result == expected else "❌"
            results.append(f"{status} 源: {source}, 结果: {result}, 期望: {expected}")
            print(f"{status} 源: {source}, 结果: {result}")
        
        return results
    
    def test_extract_filename_from_content(self):
        """测试extract_filename_from_content函数"""
        test_cases = [
            "这是内容 3-1-1函数的概念答案1.png 这是其他内容",
            "内容包含文件: example.jpg 和 another.pdf",
            "没有文件名的内容",
            "多个文件: file1.png, file2.jpg, file3.mp4"
        ]
        
        results = []
        for content in test_cases:
            filename = extract_filename_from_content(content)
            results.append(f"内容: {content[:50]}..., 提取: {filename or '无'}")
            print(f"内容: {content[:50]}..., 提取: {filename or '无'}")
        
        return results
    
    def test_retrieve_resources(self):
        """测试retrieve_resources函数"""
        test_queries = ["二次函数", "三角函数"]
        
        results = []
        for query in test_queries:
            result = retrieve_resources(query, "search")
            resource_counts = {
                "theory": len(result.get("theory_resources", [])),
                "lesson_plan": len(result.get("lesson_plan_patterns", [])),
                "visualization": len(result.get("visualization_examples", [])),
                "general": len(result.get("general_resources", []))
            }
            results.append(f"查询: {query}, 资源: {resource_counts}")
            print(f"查询: {query}, 资源: {resource_counts}")
        
        return results
    
    def test_intent_understanding_node(self):
        """测试intent_understanding_node函数"""
        test_queries = [
            "生成二次函数的教案",
            "提供三角函数的可视化设计",
            "查找函数的相关资源"
        ]
        
        results = []
        for query in test_queries:
            test_state = TestState(user_query=query)
            result = intent_understanding_node(test_state)
            intent = result.get("intent", "unknown")
            results.append(f"查询: {query}, 意图: {intent}")
            print(f"查询: {query}, 意图: {intent}")
        
        return results
    
    def test_resource_retrieval_node(self):
        """测试resource_retrieval_node函数"""
        test_state = TestState(user_query="二次函数", intent="search")
        result = resource_retrieval_node(test_state)
        retrieved = result.get("retrieved_resources", {})
        counts = {
            "theory": len(retrieved.get("theory_resources", [])),
            "lesson_plan": len(retrieved.get("lesson_plan_patterns", [])),
            "visualization": len(retrieved.get("visualization_examples", [])),
            "general": len(retrieved.get("general_resources", []))
        }
        print(f"资源检索结果: {counts}")
        return f"资源检索结果: {counts}"
    
    def test_search_result_processing_node(self):
        """测试search_result_processing_node函数"""
        # 创建测试资源
        test_resources = {
            "theory_resources": [{
                "title": "测试理论",
                "content": "这是理论内容",
                "source": "test.md",
                "relevance": 0.9
            }],
            "lesson_plan_patterns": [],
            "visualization_examples": [],
            "general_resources": []
        }
        
        test_state = TestState(retrieved_resources=test_resources, intent="search")
        result = search_result_processing_node(test_state)
        search_results = result.get("search_results", "")
        print(f"✅ 搜索结果处理成功，结果长度: {len(search_results)}")
        return f"搜索结果处理成功，结果长度: {len(search_results)}"
    
    def test_lesson_plan_generation_node(self):
        """测试lesson_plan_generation_node函数"""
        test_state = TestState(
            user_query="二次函数",
            intent="lesson_plan",
            retrieved_resources={
                "theory_resources": [{
                    "content": "二次函数知识点"
                }],
                "lesson_plan_patterns": [{
                    "content": "教案模式"
                }]
            }
        )
        
        result = lesson_plan_generation_node(test_state)
        status = result.get("current_step", "unknown")
        print(f"教案生成状态: {status}")
        return f"教案生成状态: {status}"
    
    def test_visualization_suggestion_node(self):
        """测试visualization_suggestion_node函数"""
        test_state = TestState(
            user_query="二次函数图像",
            intent="visualization",
            retrieved_resources={
                "visualization_examples": [{
                    "content": "可视化示例"
                }]
            }
        )
        
        result = visualization_suggestion_node(test_state)
        status = result.get("current_step", "unknown")
        print(f"可视化建议状态: {status}")
        return f"可视化建议状态: {status}"
    
    def test_response_formatting_node(self):
        """测试response_formatting_node函数"""
        test_state = TestState(
            user_query="二次函数",
            search_results="测试搜索结果",
            lesson_plan="测试教案",
            visualization_suggestions="测试可视化建议"
        )
        
        result = response_formatting_node(test_state)
        response = result.get("response", "")
        print(f"✅ 响应格式化成功，响应长度: {len(response)}")
        return f"响应格式化成功，响应长度: {len(response)}"
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行所有函数测试")
        print("="*80)
        
        # 运行所有测试
        self.run_test("get_chroma_client", self.test_get_chroma_client)
        self.run_test("get_embedding_model", self.test_get_embedding_model)
        self.run_test("get_model", self.test_get_model)
        self.run_test("classify_resource", self.test_classify_resource)
        self.run_test("extract_filename_from_content", self.test_extract_filename_from_content)
        self.run_test("retrieve_resources", self.test_retrieve_resources)
        self.run_test("intent_understanding_node", self.test_intent_understanding_node)
        self.run_test("resource_retrieval_node", self.test_resource_retrieval_node)
        self.run_test("search_result_processing_node", self.test_search_result_processing_node)
        self.run_test("lesson_plan_generation_node", self.test_lesson_plan_generation_node)
        self.run_test("visualization_suggestion_node", self.test_visualization_suggestion_node)
        self.run_test("response_formatting_node", self.test_response_formatting_node)
        
        # 打印测试结果
        print("\n" + "="*80)
        print("📊 测试结果汇总")
        print("="*80)
        print(f"总测试数: {self.total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.total_tests - self.passed_tests}")
        print(f"通过率: {self.passed_tests / self.total_tests * 100:.1f}%")
        
        # 打印详细结果
        print("\n📋 详细测试结果:")
        print("-"*60)
        for result in self.test_results:
            status = "✅" if result["status"] == "passed" else "❌"
            print(f"{status} {result['test']}")
            if result["status"] == "failed":
                print(f"   错误: {result['error']}")
            else:
                if isinstance(result['result'], list):
                    for item in result['result']:
                        print(f"   - {item}")
                else:
                    print(f"   结果: {result['result']}")
        
        print("\n" + "="*80)
        print("🎯 测试完成")
        print("="*80)

if __name__ == "__main__":
    tester = TestAllFunctions()
    tester.run_all_tests()
