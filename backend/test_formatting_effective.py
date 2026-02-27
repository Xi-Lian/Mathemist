#!/usr/bin/env python3
"""
测试格式化修改是否在实际生成中生效
"""

import json
import requests

# 测试标题格式和理论依据格式
def test_lesson_plan_format():
    print("=== 测试教案格式化 ===")
    
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
                
                # 测试1：标题格式
                print("\n1. 测试标题格式：")
                lines = lesson_plan.split('\n')
                title_line = None
                for line in lines:
                    if "教学设计" in line:
                        title_line = line.strip()
                        break
                
                if title_line:
                    if title_line.startswith("# "):
                        print(f"✅ 标题格式正确: {title_line}")
                    else:
                        print(f"❌ 标题缺少一级标题标记: {title_line}")
                else:
                    print("❌ 未找到标题")
                
                # 测试2：理论依据格式
                print("\n2. 测试理论依据格式：")
                import re
                has_theory_card = re.search(r'- \*\*理论卡片\*\*：', lesson_plan)
                has_core_view = re.search(r'- \*\*核心观点\*\*：', lesson_plan)
                has_teaching_inspiration = re.search(r'- \*\*教学启发\*\*：', lesson_plan)
                has_application = re.search(r'- \*\*应用场景\*\*：', lesson_plan)
                has_border = "┌─────────────────────────────────────┐" in lesson_plan
                
                print(f"Debug: has_theory_card={has_theory_card}, has_core_view={has_core_view}, has_teaching_inspiration={has_teaching_inspiration}, has_application={has_application}, has_border={has_border}")
                
                if has_theory_card and has_core_view and has_application and not has_border:
                    print("✅ 理论依据格式正确，使用无边框分点格式")
                    # 显示部分理论依据内容
                    start_idx = lesson_plan.find("**📌 理论依据**")
                    if start_idx != -1:
                        end_idx = lesson_plan.find("###", start_idx)
                        if end_idx != -1:
                            theory_section = lesson_plan[start_idx:end_idx].strip()
                            print("\n理论依据示例：")
                            print(theory_section)
                else:
                    print("❌ 理论依据格式不正确，未使用无边框分点格式")
                    # 显示当前理论依据格式
                    start_idx = lesson_plan.find("**📌 理论依据**")
                    if start_idx != -1:
                        end_idx = lesson_plan.find("###", start_idx)
                        if end_idx != -1:
                            theory_section = lesson_plan[start_idx:end_idx].strip()
                            print("\n当前理论依据格式：")
                            print(theory_section)
                
                # 测试3：后续操作建议格式
                print("\n3. 测试后续操作建议格式：")
                if "**您可以：**" in lesson_plan:
                    print("✅ 后续操作建议格式正确")
                elif "**后续操作建议：**" in lesson_plan:
                    print("❌ 后续操作建议使用了旧格式")
                else:
                    print("⚠️ 未找到后续操作建议")
                
            else:
                print(f"❌ 响应状态失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    test_lesson_plan_format()
