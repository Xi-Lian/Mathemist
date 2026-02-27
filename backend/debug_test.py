#!/usr/bin/env python3
"""
调试测试失败的问题
"""

import json
import requests

# 测试标题格式和理论依据格式
def test_lesson_plan_format():
    print("=== 调试测试失败问题 ===")
    
    # 准备测试请求
    test_data = {
        "user_input": "生成函数的单调性教案，直接生成",
        "chat_history": [],
        "context": {}
    }
    
    try:
        # 发送请求到智能体端点
        response = requests.post(
            "http://localhost:8000/math-agent/invoke",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                lesson_plan = result.get("data", {}).get("lesson_plan", "")
                
                if not lesson_plan:
                    print("❌ 教案生成失败，返回为空")
                    return
                
                print("\n1. 检查理论依据格式元素：")
                has_border = "┌─────────────────────────────────────┐" in lesson_plan
                has_core_view = "▸ **核心观点**" in lesson_plan
                has_teaching_inspiration = "▸ **教学启发**" in lesson_plan
                has_application = "▸ **应用场景**" in lesson_plan
                
                print(f"has_border: {has_border}")
                print(f"has_core_view: {has_core_view}")
                print(f"has_teaching_inspiration: {has_teaching_inspiration}")
                print(f"has_application: {has_application}")
                
                # 显示理论依据部分
                print("\n2. 理论依据部分：")
                start_idx = lesson_plan.find("**📌 理论依据**")
                if start_idx != -1:
                    end_idx = lesson_plan.find("└─────────────────────────────────────┘", start_idx)
                    if end_idx != -1:
                        theory_section = lesson_plan[start_idx:end_idx+37]
                        print(theory_section)
                
                # 检查是否包含后续操作建议
                print("\n3. 检查后续操作建议：")
                if "**您可以：**" in lesson_plan:
                    print("✅ 包含 '**您可以：**'")
                else:
                    print("❌ 不包含 '**您可以：**'")
                
                # 搜索所有包含"您可以"的内容
                import re
                suggestions = re.findall(r'\*\*您可以.*?\*\*', lesson_plan, re.DOTALL)
                if suggestions:
                    print("找到的后续操作建议：")
                    for i, suggestion in enumerate(suggestions):
                        print(f"{i+1}. {suggestion}")
                
            else:
                print(f"❌ 响应状态失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    test_lesson_plan_format()
