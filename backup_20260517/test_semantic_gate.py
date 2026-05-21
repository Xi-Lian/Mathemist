
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import re
import jieba

# 复制相关函数
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

def _passes_unified_semantic_gate(query, core_theme, doc, meta, distance, kg=None):
    if distance is None:
        print(f"  语义门控未通过: distance is None")
        return False
    
    title = meta.get('title', '') or ''
    source_file = meta.get('source_file', '') or ''
    knowledge_tags = meta.get('知识点', '') or meta.get('知识点标签', '') or ''
    resource_type = meta.get('resource_type', '') or ''
    teaching_use = meta.get('教学用途', '') or ''
    text = _normalize_match_text(
        f"{doc} {title} {knowledge_tags} {source_file} {teaching_use}"
    )
    
    print(f"\n  检查资源:")
    print(f"    标题: {title}")
    print(f"    教学用途: {teaching_use}")
    print(f"    资源类型: {resource_type}")
    print(f"    距离: {distance}")
    
    is_ggb_resource = resource_type.lower() == 'ggb' or 'ggb' in source_file.lower()
    
    if core_theme:
        theme_keywords = _extract_theme_keywords(core_theme)
        has_direct_match = any(_normalize_match_text(kw) in text for kw in theme_keywords)
        print(f"    关键词: {theme_keywords}")
        print(f"    直接匹配: {has_direct_match}")
        
        incompatible_topics = []
        if '立体几何' in core_theme or '空间向量' in core_theme:
            incompatible_topics = ['平面几何', '解析几何']
        elif '概率' in core_theme or '统计' in core_theme:
            incompatible_topics = ['函数', '几何', '代数']
        
        has_incompatible = any(_normalize_match_text(topic) in text for topic in incompatible_topics)
        
        if has_incompatible:
            print(f"    语义门控未通过(存在不兼容主题): distance={distance:.3f}, 核心主题='{core_theme}', 不兼容主题={incompatible_topics}")
            return False
        
        if distance <= 0.80:
            if has_direct_match:
                print(f"    语义门控通过(高置信度+直接匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
            elif distance <= 0.65:
                print(f"    语义门控通过(极高置信度): distance={distance:.3f}")
                return True
        
        if distance <= 0.90:
            if has_direct_match:
                print(f"    语义门控通过(中置信度+直接匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
        
        if has_direct_match:
            if distance <= 0.95:
                print(f"    语义门控通过(直接主题匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
        
        if distance <= 0.85:
            print(f"    语义门控通过(较低距离): distance={distance:.3f}")
            return True
        
        # GGB资源放宽
        if is_ggb_resource and distance <= 1.2:
            title_normalized = _normalize_match_text(title)
            source_file_normalized = _normalize_match_text(source_file)
            teaching_use_normalized = _normalize_match_text(teaching_use)
            for kw in theme_keywords:
                kw_normalized = _normalize_match_text(kw)
                if kw_normalized in title_normalized or kw_normalized in source_file_normalized or kw_normalized in teaching_use_normalized:
                    print(f"    语义门控通过(GGB资源放宽+关键词匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                    return True
        
        # 课件资源放宽
        is_courseware_resource = resource_type.lower() == 'courseware' or '课件' in teaching_use
        print(f"    是课件资源: {is_courseware_resource}")
        if is_courseware_resource and distance <= 1.1:
            title_normalized = _normalize_match_text(title)
            source_file_normalized = _normalize_match_text(source_file)
            teaching_use_normalized = _normalize_match_text(teaching_use)
            print(f"    标题归一化: {title_normalized}")
            print(f"    教学用途归一化: {teaching_use_normalized}")
            for kw in theme_keywords:
                kw_normalized = _normalize_match_text(kw)
                print(f"      检查关键词: {kw} -> {kw_normalized}")
                if kw_normalized in title_normalized or kw_normalized in source_file_normalized or kw_normalized in teaching_use_normalized:
                    print(f"    语义门控通过(课件资源放宽+关键词匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                    return True
        
        print(f"    语义门控未通过: distance={distance:.3f}, 核心主题='{core_theme}', 文本中未找到匹配")
        return False
    else:
        result = distance <= 1.10
        print(f"    语义门控(无核心主题): distance={distance:.3f}, result={result}")
        return result

# 测试场景
query = "找一下关于分类加法计数原理的练习课课件"
core_theme = "分类加法计数原理"

# 模拟课件元数据
doc = "课件，内容：6.1分类加法计数原理与分步乘法计数原理，文件名：6.1 分类加法计数原理与分步乘法计数原理，教学用途：练习课课件，来源：概率与统计-课件汇总.xlsx"
meta = {
    "title": "6.1 分类加法计数原理与分步乘法计数原理",
    "filename": "6.1 分类加法计数原理与分步乘法计数原理",
    "教学用途": "练习课课件",
    "resource_type": "courseware"
}
distance = 0.0  # 精确匹配设置的距离

print("=" * 80)
print(f"测试语义门控")
print(f"查询: {query}")
print(f"核心主题: {core_theme}")
print("=" * 80)

# 测试语义门控
result = _passes_unified_semantic_gate(query, core_theme, doc, meta, distance)
print(f"\n最终结果: {'通过' if result else '未通过'}")

