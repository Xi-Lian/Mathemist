from .._shared import *


class _ExtractQueryThemesMixin:
    def _extract_query_themes(self, query: str) -> List[str]:
        """
        从查询中提取主题
        严格区分不同主题的核心意图
        支持逗号分隔的多主题格式
        """
        # 检查是否是逗号分隔的多主题格式
        if ',' in query:
            # 分割多主题，清理并过滤空主题
            themes = [t.strip() for t in query.split(',') if t.strip()]
            if len(themes) > 1:
                print(f"🔗 多主题识别: {themes}")
                return themes
        
        # 单主题查询处理
        themes = []
        
        # 常见的数学主题模式（精确匹配）
        # V24.2改进：添加一次函数主题
        # V31.0改进：调整主题顺序，具体函数主题优先于函数性质主题
        # V53.7改进：添加宽泛主题识别
        theme_patterns = [
            # 具体函数主题（优先匹配）
            "指数函数", "对数函数", "幂函数", "二次函数", "一次函数",
            "三角函数", "正弦函数", "余弦函数", "正切函数",

            # 具体函数的细分主题
            "指数函数的概念", "对数函数的概念", "幂函数的概念", "三角函数的概念", "二次函数的概念", "一次函数的概念",
            "指数函数的性质", "对数函数的性质", "幂函数的性质", "三角函数的性质", "二次函数的性质", "一次函数的性质",
            "指数函数的应用", "对数函数的应用", "幂函数的应用", "三角函数的应用", "二次函数的应用", "一次函数的应用",

            # 函数性质主题（次要匹配）
            "函数的概念", "函数的表示法", "函数的单调性", "函数的奇偶性", "函数的周期性",
            "函数的应用", "函数的零点",

            # V309.0添加：非函数类数学主题
            "分层抽样", "简单随机抽样", "随机抽样", "抽样调查",
            "总体与样本", "用样本估计总体",
            "排列", "组合", "二项式定理",
            "空间向量", "平面向量", "向量的加减", "向量的数乘",
            "直线与平面", "平面与平面垂直", "线面垂直",
            "数列", "等差数列", "等比数列", "数列的通项公式", "数列的求和",
            "复数", "复数的运算", "复数的几何意义",
            "集合", "集合的运算", "子集", "交集", "并集",
            "不等式", "解不等式", "一元二次不等式",
        ]
        
        # V53.7改进：宽泛主题列表
        broad_themes = ["函数", "数学", "代数", "几何", "统计", "概率"]
        
        query_lower = query.lower()
        
        # 1. 优先匹配更具体的主题
        # 按长度排序，长的主题优先匹配
        sorted_patterns = sorted(theme_patterns, key=len, reverse=True)
        
        for pattern in sorted_patterns:
            if pattern in query_lower:
                themes.append(pattern)
                # 避免重复匹配
                query_lower = query_lower.replace(pattern, "")
        
        # 2. 如果没有匹配到主题，检查宽泛主题
        if not themes:
            for broad_theme in broad_themes:
                if broad_theme in query_lower:
                    themes.append(broad_theme)
                    print(f"🔗 宽泛主题识别: '{broad_theme}'")
                    break
        
        # 3. 检查是否是资源类型查询（如"教案"、"教学大纲"、"课件"等）
        resource_type_keywords = ["教案", "教学大纲", "课件", "课例视频", "ggb", "习题", "练习题", "题目"]
        resource_type_match = None
        for keyword in resource_type_keywords:
            if keyword in query_lower:
                resource_type_match = keyword
                break
        
        # 4. 如果是资源类型查询且没有匹配到主题，使用资源类型作为主题
        if not themes and resource_type_match:
            themes.append(resource_type_match)
            print(f"🔗 资源类型查询识别: '{resource_type_match}'")
        
        # 5. 如果没有匹配到主题，使用语义关联映射
        if not themes:
            # 检查语义关联
            for concept, core_theme in self.semantic_mappings.items():
                if concept in query_lower:
                    themes.append(core_theme)
                    print(f"🔗 语义关联: '{concept}' -> '{core_theme}'")
                    break
        
        # 6. 如果仍然没有匹配到任何主题，使用查询本身作为主题
        if not themes:
            themes.append(query)
            print(f"🔗 使用查询作为主题: '{query}'")
        
        return themes