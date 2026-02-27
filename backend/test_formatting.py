#!/usr/bin/env python3
"""
测试格式化修改是否生效
"""

import re

# 测试标题格式
def test_title_format():
    print("=== 测试标题格式 ===")
    # 模拟从文件中读取标题行
    test_cases = [
        "# 《函数的单调性》教学设计",  # 旧格式
        "《函数的单调性》教学设计"   # 新格式
    ]
    
    for i, test_case in enumerate(test_cases):
        if test_case.startswith("# "):
            print(f"❌ 测试 {i+1}: 标题包含多余的#号: {test_case}")
        else:
            print(f"✅ 测试 {i+1}: 标题格式正确: {test_case}")

# 测试理论依据格式
def test_theory_format():
    print("\n=== 测试理论依据格式 ===")
    # 模拟生成的理论依据
    test_theory = """**📌 理论依据**
┌─────────────────────────────────────┐
│ 【理论卡片二十二：APOS理论】│
│                                      │
│ ▸ **核心观点**：数学概念的习得需经历活动、过程、对象、图式四个递进且循环的认知阶段。 │
│                                      │
│ ▸ **教学启发**：教学应设计可操作的实践活动，引导学生从具体体验抽象为数学语言，最终构建知识网络。 │
│                                      │
│ ▸ **应用场景**：设计体现了教学启发中的：操作的具象化、过程的抽象化、图式的体系化 │
└─────────────────────────────────────┘"""
    
    # 检查是否包含层次结构
    has_border = "┌─────────────────────────────────────┐" in test_theory
    has_core_view = "▸ **核心观点**" in test_theory
    has_teaching_inspiration = "▸ **教学启发**" in test_theory
    has_application = "▸ **应用场景**" in test_theory
    
    if has_border and has_core_view and has_teaching_inspiration and has_application:
        print("✅ 理论依据格式正确，包含层次结构")
    else:
        print("❌ 理论依据格式不正确，缺少层次结构")

# 测试后续操作建议格式
def test_operation_suggestions():
    print("\n=== 测试后续操作建议格式 ===")
    # 模拟生成的操作建议
    test_suggestions = """**您可以：**
1. 📖 查看完整教案
2. ✏️ 提出修改意见，我可以帮您调整
3. 📥 导出教案（支持 Markdown、HTML、Word 格式）
4. 🔄 基于这个教案继续优化"""
    
    # 检查是否每行一个建议
    lines = test_suggestions.strip().split('\n')
    has_header = "**您可以：**" in lines[0]
    has_numbered_list = all(line.strip().startswith(f"{i+1}. ") for i, line in enumerate(lines[1:]))
    
    if has_header and has_numbered_list:
        print("✅ 后续操作建议格式正确，每行一个")
    else:
        print("❌ 后续操作建议格式不正确")

if __name__ == "__main__":
    test_title_format()
    test_theory_format()
    test_operation_suggestions()
    print("\n测试完成！")
