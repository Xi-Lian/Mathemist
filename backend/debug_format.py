#!/usr/bin/env python3
"""
调试理论依据格式问题
"""

import re

# 模拟模型生成的理论依据格式
test_lesson_plan = """
### 📚 知识与技能目标
🔹 **概念理解**：理解函数单调性的定义，掌握判断函数单调性的基本方法。

**📌 理论依据：[理论卡片二十二：APOS理论] - 数学概念的习得需经历活动、过程、对象、图式四个递进且循环的认知阶段。 - 应用场景：本目标设计遵循APOS理论，从生活实例（活动）出发，引导学生抽象出单调性的符号化定义（过程），再通过证明与应用将其固化为独立的数学对象（对象），最终融入函数性质的知识体系（图式）。**
"""

print("=== 调试理论依据格式 ===")
print("原始文本:")
print(test_lesson_plan)
print("\n" + "="*50)

# 测试正则表达式
pattern = r"\*\*📌 理论依据：\[(理论卡片[^\]]+)\] - ([^-]+) - 应用场景：([^\*]+)\*\*"
matches = re.findall(pattern, test_lesson_plan, re.DOTALL)

print("正则匹配结果:")
print(matches)

if matches:
    for match in matches:
        print(f"理论卡片: {match[0]}")
        print(f"核心观点: {match[1].strip()}")
        print(f"应用场景: {match[2].strip()}")

# 测试文本换行函数
def wrap_text(text, width=38):
    """文本换行，确保不超出边框宽度"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line:
        lines.append(' '.join(current_line))
    return lines

# 测试换行函数
if matches:
    core_view = matches[0][1].strip()
    print("\n换行测试:")
    print(f"原始核心观点: {core_view}")
    print(f"长度: {len(core_view)}")
    
    wrapped = wrap_text(core_view, 38)
    print(f"换行后: {wrapped}")
    print(f"行数: {len(wrapped)}")
    
    for i, line in enumerate(wrapped):
        print(f"第{i+1}行: '{line}' (长度: {len(line)})")
