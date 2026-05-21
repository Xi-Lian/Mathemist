
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import jieba
import re

def _normalize_match_text(text):
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("的", "")
    normalized = re.sub(r"[\s,，。；;、:：()\[\]（）\-_/]+", "", normalized)
    return normalized

def _extract_theme_keywords(core_theme):
    keywords = []
    if isinstance(core_theme, str):
        themes = [t.strip() for t in core_theme.split(',') if t.strip()]
        for theme in themes:
            keywords.append(theme)
            if '指数函数' in theme:
                keywords.extend(['指数函数', '指数', 'exponential'])
            elif '幂函数' in theme:
                keywords.extend(['幂函数', '幂'])
            elif '对数函数' in theme:
                keywords.extend(['对数函数', '对数', 'log'])
            elif '三角函数' in theme:
                keywords.extend(['三角函数', '三角', 'sin', 'cos', 'tan'])
            else:
                jieba_keywords = list(jieba.cut(theme))
                keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
    return list(set(keywords))

# 测试场景
core_theme = "分类加法计数原理"
print(f"核心主题: {core_theme}")

# 提取关键词
keywords = _extract_theme_keywords(core_theme)
print(f"提取的关键词: {keywords}")

# 课件元数据
title = "6.1 分类加法计数原理与分步乘法计数原理"
teaching_use = "练习课课件"
print(f"\n课件标题: {title}")
print(f"教学用途: {teaching_use}")

# 模拟精确匹配的haystack
haystack = f"{title} {teaching_use}"
print(f"\nhaystack: {haystack}")

# 测试主题匹配
print(f"\n测试主题 '{core_theme}' 是否在 haystack 中:")
if core_theme in haystack:
    print(f"  ✅ 主题 '{core_theme}' 直接匹配成功!")
else:
    print(f"  ❌ 主题 '{core_theme}' 直接匹配失败")

# 测试关键词匹配
print(f"\n测试关键词匹配:")
for keyword in keywords:
    if keyword in haystack:
        print(f"  ✅ 关键词 '{keyword}' 匹配成功!")
    else:
        print(f"  ❌ 关键词 '{keyword}' 匹配失败")

# 测试归一化后的匹配
print(f"\n测试归一化后的匹配:")
normalized_haystack = _normalize_match_text(haystack)
print(f"归一化后的 haystack: {normalized_haystack}")

normalized_theme = _normalize_match_text(core_theme)
print(f"\n归一化后的主题: {normalized_theme}")
if normalized_theme in normalized_haystack:
    print(f"  ✅ 归一化后的主题匹配成功!")
else:
    print(f"  ❌ 归一化后的主题匹配失败")

print(f"\n归一化后的关键词匹配:")
for keyword in keywords:
    normalized_kw = _normalize_match_text(keyword)
    if normalized_kw in normalized_haystack:
        print(f"  ✅ 关键词 '{keyword}' (归一化: '{normalized_kw}') 匹配成功!")
    else:
        print(f"  ❌ 关键词 '{keyword}' (归一化: '{normalized_kw}') 匹配失败")

