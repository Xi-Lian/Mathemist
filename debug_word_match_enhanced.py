"""测试 _word_match_enhanced 函数的匹配逻辑"""

# 定义具体函数类型集合
SPECIFIC_FUNCTION_TYPES = {
    "指数函数", "对数函数", "幂函数", 
    "正弦函数", "余弦函数", "正切函数", "余切函数", "正割函数", "余割函数",
    "反正弦函数", "反余弦函数", "反正切函数", "反余切函数",
    "一次函数", "二次函数", "反比例函数", "正比例函数",
    "分段函数", "复合函数", "周期函数", "奇函数", "偶函数"
}

def _is_specific_function_query(theme):
    """判断是否是具体函数类型查询"""
    if not theme or not isinstance(theme, str):
        return False
    first_theme = theme.split(',')[0].strip()
    return first_theme in SPECIFIC_FUNCTION_TYPES

def _word_match_enhanced(kp, kw, core_theme, is_specific_function):
    """增强的知识点匹配"""
    kp = kp.lower()
    kw = kw.lower()
    core_theme_lower = core_theme.lower()
    
    # 1. 精确匹配
    if kp == kw:
        return True
    
    # 2. 前缀/包含匹配
    if kp.startswith(kw) or kw.startswith(kp) or kp in kw or kw in kp:
        return True
    
    # 3. 如果是具体函数类型查询，需要额外检查同级函数类型
    if is_specific_function:
        # 提取当前查询的函数类型名称（去掉"函数"后缀）
        base_function = core_theme.replace("函数", "").strip()
        
        # 定义其他函数类型关键词
        other_function_keywords = [
            "对数", "幂", "正弦", "余弦", "正切", "余切", "正割", "余割",
            "分段", "一次", "二次", "反比例", "正比例",
            "复合", "周期", "奇函数", "偶函数"
        ]
        # 排除当前查询的函数类型
        other_function_keywords = [k for k in other_function_keywords if k != base_function]
        
        # 检查kp或kw是否包含其他函数类型
        kp_has_other = any(other in kp for other in other_function_keywords)
        kw_has_other = any(other in kw for other in other_function_keywords)
        
        # 检查kp或kw是否包含当前查询的函数类型
        kp_has_current = core_theme in kp or base_function in kp
        kw_has_current = core_theme in kw or base_function in kw
        
        print(f"  [DEBUG] kp='{kp}', kw='{kw}'")
        print(f"  [DEBUG] kp_has_other={kp_has_other}, kw_has_other={kw_has_other}")
        print(f"  [DEBUG] kp_has_current={kp_has_current}, kw_has_current={kw_has_current}")
        
        # 【关键改进】如果习题知识点同时包含当前函数类型和其他函数类型
        # 说明这是综合题或跨章节复习题，应该允许通过
        if kp_has_current and kp_has_other:
            print(f"  [DEBUG] → 综合题，允许通过")
            pass  # 继续后续检查
        
        # 如果习题的知识点只包含其他函数类型，完全不包含当前查询的函数类型
        # 需要进一步检查是否包含通用词（如"函数应用"、"函数模型"等）
        elif kp_has_other and not kp_has_current:
            # 检查是否包含通用词
            generic_terms = ["函数应用", "函数模型", "函数的应用", "模型选择", "数据拟合"]
            has_generic_term = any(term in kp for term in generic_terms)
            
            print(f"  [DEBUG] has_generic_term={has_generic_term}")
            
            if has_generic_term:
                # 包含通用词，允许通过，由语义分数决定
                print(f"  [DEBUG] → 包含通用词，允许通过")
                pass  # 继续后续检查
            else:
                # 不包含通用词，确实是其他函数类型，拒绝
                print(f"  [DEBUG] → 不包含通用词，拒绝")
                return False
        
        # 如果KG关键词包含其他函数类型，但习题知识点不包含
        # 也需要检查
        elif kw_has_other and not kp_has_other:
            result = core_theme in kp or core_theme in kw
            print(f"  [DEBUG] → kw有其他函数类型，结果={result}")
            return result
        
        # 如果不包含其他函数类型，但包含通用词如"函数"、"应用"等
        # 应该允许通过，由后续的语义分数来决定是否展示
        if not kp_has_other and not kw_has_other:
            generic_terms = ["函数", "应用", "模型", "性质", "图像"]
            if any(term in kp for term in generic_terms):
                print(f"  [DEBUG] → 包含通用词，允许通过")
                # 返回True，让语义分数来决定
                return True
    
    # 4. 常规前缀匹配
    return False

# 测试用例
print("=" * 80)
print("测试场景：查询'指数函数'")
print("=" * 80)

core_theme = "指数函数"
is_specific = _is_specific_function_query(core_theme)
print(f"\ncore_theme='{core_theme}', is_specific={is_specific}\n")

# KG关键词
kg_keywords = ["指数函数", "过定点", "指数运算", "指数函数模型", "指数增长", 
               "指数衰减", "底数", "指数方程", "指数不等式"]

# 测试习题知识点
test_cases = [
    ("函数模型;数据拟合", "4-5-3函数模型的应用"),
    ("模型选择", "4-4-1不同函数增长的差异"),
    ("对数运算;指数运算", "4-3-2对数的运算"),
    ("分段函数；函数应用", "3-4函数的应用（1）"),
    ("象限角;弧度制;集合表示", "5-1-2弧度制"),
    ("正弦函数的实际应用", "5-7三角函数的应用"),
    ("二次函数;一元二次不等式", "2.3 二次函数与一元二次方程"),
]

for kp_str, title in test_cases:
    print(f"\n{'='*80}")
    print(f"习题: {title}")
    print(f"知识点: {kp_str}")
    
    # 分割知识点
    kp_list = [kp.strip() for kp in kp_str.replace("；", ";").split(";") if kp.strip()]
    
    has_kg_match = False
    matched_keywords = []
    
    for kp in kp_list:
        for kw in kg_keywords:
            result = _word_match_enhanced(kp, kw, core_theme, is_specific)
            if result:
                has_kg_match = True
                matched_keywords.append(f"{kp}←{kw}")
                break
        if has_kg_match:
            break
    
    print(f"\n结果: has_kg_match={has_kg_match}")
    if matched_keywords:
        print(f"匹配: {matched_keywords}")
    else:
        print(f"未匹配任何KG关键词")
