from .._shared import *


class _GetThemeVariantsMixin:
    def _get_theme_variants(self, theme: str) -> List[str]:
        """
        V11.7：动态获取主题的变体和同义词
        
        支持同一主题的多种表达方式，提高匹配灵活性
        动态提取核心概念，避免静态映射的局限性
        
        V11.7改进：
        - 更严格地控制"一般函数概念"的变体生成
        - "函数的概念"只生成明确相关的变体，不生成"函数"等过于宽泛的变体
        - 区分"一般函数概念"和"具体函数概念"
        
        Args:
            theme: 主题名称
            
        Returns:
            主题变体列表
        """
        # 主题变体映射（仅保留一些特殊的、难以动态处理的映射）
        theme_variants = {
            "函数的概念": ["函数概念", "函数定义", "函数的定义", "函数的基本概念"],
            "函数的单调性": ["函数单调性", "单调性", "函数的增减性", "函数的增减"],
            "函数的奇偶性": ["函数奇偶性", "奇偶性", "函数的对称性", "函数对称性"],
            "函数的周期性": ["函数周期性", "周期性", "函数的周期"],
            "函数的应用": ["函数应用", "应用", "实际应用", "生活应用", "数学建模", "函数模型"],
            "函数的零点": ["函数零点", "零点", "方程求解", "解方程", "方程根", "方程的解"],
            "正弦函数": ["sin函数", "sin", "正弦"],
            "余弦函数": ["cos函数", "cos", "余弦"],
            "正切函数": ["tan函数", "tan", "正切"],
            "二次函数": ["二次函数", "抛物线", "二次", "一元二次"],
            "指数函数": ["指数函数", "指数", "指数增长", "指数衰减"],
            "对数函数": ["对数函数", "对数", "log", "ln"],
            "幂函数": ["幂函数", "幂", "幂运算"],
            "三角函数": ["三角函数", "三角", "正弦", "余弦", "正切", "sin", "cos", "tan"],
        }
        
        # 提取核心关键词
        core_variants = theme_variants.get(theme, [])
        
        # 自动生成一些变体
        auto_variants = []
        
        # V11.7：区分"一般函数概念"和"具体函数概念"
        # 具体函数类型列表
        specific_function_types = ["指数", "对数", "幂", "三角", "正弦", "余弦", "正切", "反三角", "二次"]
        
        # 判断是否是"一般函数概念"（如"函数的概念"、"函数的性质"）
        is_general_function_concept = False
        if theme.startswith("函数的"):
            # 检查是否是"函数的概念"、"函数的性质"等一般概念
            # 而不是"指数函数的概念"等具体概念
            is_general_function_concept = True
        
        # 判断是否是"具体函数概念"（如"指数函数的概念"）
        is_specific_function_concept = False
        matched_func_type = None
        for func_type in specific_function_types:
            if theme.startswith(func_type) or (func_type in theme and "函数" in theme):
                is_specific_function_concept = True
                matched_func_type = func_type
                break
        
        # V11.7：动态提取核心概念
        # 常见的后缀模式，移除这些后缀可以得到核心概念
        suffix_patterns = [
            "的概念", "的概念与意义",
            "的性质", "的性质与应用",
            "的图像", "的图像与性质",
            "的定义", "的定义域",
            "的运算", "的运算法则",
            "的应用", "的应用举例",
            "的公式", "的公式推导"
        ]
        
        # 尝试移除后缀，提取核心概念
        for suffix in suffix_patterns:
            if theme.endswith(suffix):
                core_concept = theme[:-len(suffix)]
                
                # V11.7：只有"具体函数概念"才添加核心概念作为变体
                # "一般函数概念"不添加核心概念作为变体（避免"函数的概念" -> "函数"）
                if is_specific_function_concept and matched_func_type:
                    auto_variants.append(core_concept)
                    
                    # 同时生成带后缀的变体
                    for other_suffix in suffix_patterns:
                        if other_suffix != suffix:
                            auto_variants.append(core_concept + other_suffix)
                break
        
        # V11.7：处理"具体函数"相关的主题
        if is_specific_function_concept and matched_func_type:
            # 添加函数类型作为变体
            auto_variants.append(matched_func_type + "函数")
            # 添加不带"函数"的变体
            auto_variants.append(matched_func_type)
        
        # V11.7：对于"一般函数概念"，移除"的"字生成变体
        # 对于其他主题，也移除"的"字生成变体
        if "的" in theme:
            # V11.7：对于"一般函数概念"，确保变体不包含"函数"单独出现
            if is_general_function_concept:
                variant = theme.replace("的", "")
                # 如果变体不是"函数"，才添加
                if variant != "函数":
                    auto_variants.append(variant)
            else:
                auto_variants.append(theme.replace("的", ""))
        
        # V11.7：移除"函数"后缀（仅对非一般函数概念）
        if theme.endswith("函数") and not is_general_function_concept:
            auto_variants.append(theme[:-2])
        
        # V11.7：移除"函数的"前缀（仅对一般函数概念，但不添加"概念"作为变体）
        # 不执行此操作，避免"函数的概念" -> "概念"
        
        # 合并并去重
        all_variants = list(set(core_variants + auto_variants))
        
        # 确保返回的变体不为空
        if not all_variants:
            return [theme]
        
        return all_variants
