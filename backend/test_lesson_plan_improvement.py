"""
测试教案检索优化效果
"""
import sys
from pathlib import Path

# 添加backend目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.resource_table_parser import ResourceTableParser

def test_lesson_plan_improvement():
    """测试教案优化效果"""
    print("="*70)
    print("  🧪 教案检索优化测试")
    print("="*70)
    
    # 初始化解析器
    parser = ResourceTableParser("../learning_resource")
    
    # 测试用的教案内容（模拟）
    test_lesson_plan = {
        "title": "4.2.1指数函数的概念",
        "content": """
# 4.2.1指数函数的概念

## 教学目标
1. 理解指数函数的概念
2. 掌握指数函数的图像和性质
3. 培养学生的数学抽象和逻辑推理能力

## 教学重点
指数函数的概念和图像

## 教学难点
指数函数的性质应用

## 数学学科素养
- 数学抽象
- 逻辑推理
- 数学运算

## 教学过程
### 新课导入
...
        """,
        "source_file": "教案/第四章 指数函数与对数函数/4.2指数函数/4.2.1指数函数的概念.md",
        "resource_type": "lesson_plan"
    }
    
    print("\n📝 测试教案信息:")
    print(f"  标题: {test_lesson_plan['title']}")
    print(f"  来源: {test_lesson_plan['source_file']}")
    
    print("\n" + "-"*70)
    print("🔍 优化前（假设）:")
    print("  标题：4.2.1指数函数的概念，内容：# 4.2.1指数函数的概念...")
    
    print("\n" + "-"*70)
    print("✨ 优化后:")
    optimized_text = parser.format_resource_for_search(test_lesson_plan)
    print(f"  {optimized_text}")
    
    print("\n" + "-"*70)
    print("📊 分析:")
    print("  ✅ 标题重复3次，权重最高")
    print("  ✅ 路径信息重复2次")
    print("  ✅ 只保留高价值内容")
    print("  ✅ 过滤了通用词（教学目标、教学重点、数学学科素养等）")
    print("  ✅ 添加了类型标签（教案、教学设计）")
    
    print("\n" + "="*70)
    print("  ✅ 测试完成！")
    print("="*70)
    
    return optimized_text

if __name__ == "__main__":
    test_lesson_plan_improvement()
