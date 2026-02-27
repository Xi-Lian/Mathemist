#!/usr/bin/env python3
"""
测试用户提供的具体案例格式化
"""

import re

# 测试用户提供的案例
def test_user_case():
    print("=== 测试用户提供的案例 ===")
    
    # 用户提供的原始内容
    user_content = """📌 理论依据 ┌─────────────────────────────────────┐ │ 【理论卡片八：TPACK理论】 │ │ │ ▸ 核心观点：强调技术知识（TK）、教学法知识（PK）与学科内容知识（CK）三者的深度有机融合（TPACK），而非简单叠加。│ │ │ │ ▸ 教学启发： │ │ ·技术工具的情境适配：选择GeoGebra（TK）动态演示函数图象，正是为了突破“单调性”这一抽象内容（CK）的理解难点，其“动态性”与探究式教学法（PK）高度契合。│ │ ·教学策略的整合设计:P PT用于高效呈现信息，板书用于动态生成和结构化知识，学案用于引导探究路径，三者与讲授、探究等教学法（PK）整合，共同服务于学生对函数单调性（CK）的深度学习。│ │ │ │ ▸ 应用场景：本课的教学手段设计是TPACK的实践。GeoGebra（TK）的运用不是为了用技术而用技术，而是因为它能完美地服务于“通过直观想象理解抽象性质”（CK&PK）这一教学核心目标，实现了三者的深度融合。│ └─────────────────────────────────────┘ 
 
 ┌─────────────────────────────────────┐ │ 1️⃣ 创设情境（2分钟） │ │ └─ 教师展示三组图片，学生快速观察： │ │ 📊 气温日变化图：先升后降。│ │ 📈 某股票走势图：波动上升。│ │ 📏 青少年平均身高随年龄变化图：持续增长。│ │ 提问：“这些图表反映了什么共同特点？”（都有上升或下降的变化趋势） │ │ │ │ 2️⃣ 提出问题（3分钟） │ │ └─ 教师用GeoGebra展示 y = x² 的图象。│ │ ❓ 引导观察：“当x从负无穷大到0时，图象从左到右如何变化？”（下降） │ │ ❓ 引导观察：“当x从0到正无穷大时，图象从左到右如何变化？”（上升） │ │ ❓ 引出课题：“在数学中，如何精确地描述函数图象这种‘上升’或‘下降’的性质呢？这就是我们今天要学习的——函数的单调性 
 
 ┌─────────────────────────────────────┐ │ • 策略1（针对难点1）：采用“反例辨析法”和“小组辩论法”。举出在区间内“很多点”都满足但并非单调的函数反例（如震荡函数局部图），引发认知冲突，通过讨论深刻理解“任意”不可替代。│ │ • 策略2（针对难点2）：贯彻“数形结合思想”。利用GeoGebra动态演示，同步呈现图象升降与 取值及 大小关系的变化，建立“形”与“数”的直观联系。│ │ • 策略3（针对难点3）：采用“范例教学”与“程序性分解”。教师规范板演一道用定义证明的例题，将过程分解为“设元→作差→变形→定号→结论”五步，并强调每一步的依据和关键，让学生有章可循。│ └─────────────────────────────────────┘x₁, x₂f(x₁), f(x₂)"""
    
    # 清理和格式化内容
    def clean_and_format(content):
        # 1. 清理多余的空格和换行
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\s*│\s*', '│', content)
        
        # 2. 处理理论依据部分
        theory_pattern = r'📌 理论依据.*?└─────────────────────────────────────┘'
        theory_matches = re.findall(theory_pattern, content, re.DOTALL)
        
        for theory in theory_matches:
            # 提取理论卡片信息
            theory_key_match = re.search(r'【(理论卡片[^：]+)：([^】]+)】', theory)
            if theory_key_match:
                theory_key = theory_key_match.group(1)
                theory_name = theory_key_match.group(2)
                
                # 提取核心观点
                core_view_match = re.search(r'▸ 核心观点：([^│]+)', theory)
                core_view = core_view_match.group(1).strip() if core_view_match else ""
                
                # 提取教学启发
                teaching_inspiration_match = re.search(r'▸ 教学启发：([^▸]+)', theory, re.DOTALL)
                teaching_inspiration = teaching_inspiration_match.group(1).strip() if teaching_inspiration_match else ""
                
                # 提取应用场景
                application_match = re.search(r'▸ 应用场景：([^└]+)', theory)
                application = application_match.group(1).strip() if application_match else ""
                
                # 文本换行函数
                def wrap_text(text, width=20):
                    lines = []
                    current_line = []
                    current_width = 0
                    
                    for char in text:
                        if '\u4e00' <= char <= '\u9fa5':
                            char_width = 2
                        else:
                            char_width = 1
                        
                        if current_width + char_width <= width:
                            current_line.append(char)
                            current_width += char_width
                        else:
                            lines.append(''.join(current_line))
                            current_line = [char]
                            current_width = char_width
                    
                    if current_line:
                        lines.append(''.join(current_line))
                    
                    return lines
                
                # 处理各部分
                core_view_lines = wrap_text(core_view, 20)
                core_view_formatted = '\n│ ' + '\n│ '.join(core_view_lines)
                
                teaching_inspiration_lines = wrap_text(teaching_inspiration, 20)
                teaching_inspiration_formatted = '\n│ ' + '\n│ '.join(teaching_inspiration_lines)
                
                application_lines = wrap_text(application, 20)
                application_formatted = '\n│ ' + '\n│ '.join(application_lines)
                
                # 生成新格式
                new_theory = f"""**📌 理论依据**
┌─────────────────────────────────────┐
│ 【{theory_key}：{theory_name}】       │
│                                      │
│ ▸ **核心观点**：{core_view_formatted} │
│                                      │
│ ▸ **教学启发**：{teaching_inspiration_formatted} │
│                                      │
│ ▸ **应用场景**：{application_formatted} │
└─────────────────────────────────────┘"""
                
                # 替换
                content = content.replace(theory, new_theory)
        
        # 3. 处理其他边框部分
        border_pattern = r'┌─[─]+┐[\s\S]*?└─[─]+┘'
        border_matches = re.findall(border_pattern, content)
        
        for border in border_matches:
            # 清理边框内容
            cleaned_border = border.replace('││', '│')
            cleaned_border = re.sub(r'│\s*│', '│', cleaned_border)
            cleaned_border = re.sub(r'\s+│', ' │', cleaned_border)
            cleaned_border = re.sub(r'│\s+', '│ ', cleaned_border)
            
            # 替换
            content = content.replace(border, cleaned_border)
        
        # 4. 清理末尾的多余内容
        content = re.sub(r'└─────────────────────────────────────┘.*', '└─────────────────────────────────────┘', content)
        
        return content
    
    # 格式化内容
    formatted_content = clean_and_format(user_content)
    print("\n格式化后的内容：")
    print(formatted_content)

if __name__ == "__main__":
    test_user_case()
