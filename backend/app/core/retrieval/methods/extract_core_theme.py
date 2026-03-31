from .._shared import *


class _ExtractCoreThemeMixin:
    def _extract_core_theme(self, query: str) -> str:
        """
        提取核心主题（使用LLM动态提取，支持完整主题识别，支持多个主题）
        
        Args:
            query: 用户查询
            
        Returns:
            核心主题字符串（多个主题用逗号分隔）
        """
        print(f"🔍 开始提取核心主题，查询: '{query}'")
        
        # 1. 直接提取查询意图（避免调用_extract_query_conditions导致递归）
        intent = ''
        intent_patterns = [
            ('练习', ['练习题', '习题', '题目', '测试题', '题']),
            ('学习', ['学习', '了解', '掌握', '理解', '认识']),
            ('教学', ['教学', '教案', '课件', '教学设计', '教学方案']),
            ('复习', ['复习', '巩固', '回顾', '总结']),
            ('备考', ['备考', '冲刺', '模拟', '真题']),
            ('比较', ['比较', '对比', '区别', '联系', '异同']),
            ('应用', ['应用', '实际应用', '应用题', '实践'])
        ]
        for intent_name, patterns in intent_patterns:
            for pattern in patterns:
                if pattern in query:
                    intent = intent_name
                    break
            if intent:
                break
        
        # 2. 首先检查查询中是否包含资源类型词
        resource_type_keywords = [
            "教案", "教学设计", "教学方案", "教学大纲", "大纲", "课程标准",
            "课件", "PPT", "幻灯片", "课例", "教学视频", "课堂实录",
            "GGB", "GeoGebra", "动态图", "可视化", "习题", "题目", "练习题",
            "测试题", "计算题", "应用题", "填空题", "选择题", "解答题", "证明题"
        ]
        
        # 检查查询是否包含资源类型词
        has_resource_type = any(keyword in query for keyword in resource_type_keywords)
        
        # 3. 移除资源类型词和修饰词
        cleaned_query = query
        # 移除资源类型词
        for keyword in resource_type_keywords:
            cleaned_query = cleaned_query.replace(keyword, "").strip()
        # 移除修饰词
        modifier_words = [
            "基础", "简单", "中等", "难", "困难", "拔高", "刚学", "入门", "初级",
            "一般", "普通", "常见", "挑战", "压轴", "适中", "容易", "提高", "进阶", "综合",
            "高一", "高二", "高三", "初中", "初一", "初二", "初三",
            "几道", "一些", "几个", "少量", "多个",
            "学习", "了解", "掌握", "理解", "认识", "复习", "巩固", "回顾", "总结",
            "备考", "冲刺", "模拟", "真题", "比较", "对比", "区别", "联系", "异同",
            "应用", "实际应用", "实践"
        ]
        for word in modifier_words:
            cleaned_query = cleaned_query.replace(word, "").strip()
        
        if cleaned_query != query:
            print(f"   📝 清理后的查询: '{cleaned_query}'")
        
        # 4. 首先使用关键词匹配提取主题
        print("🔑 首先使用关键词匹配提取主题...")
        # 特殊处理：三角恒等变换、导数、指数函数和对数函数对比等主题
        if "三角恒等变换" in query:
            keyword_theme = "三角恒等变换"
        elif "导数" in query:
            keyword_theme = "导数"
        elif any(phrase in query for phrase in ["指数函数和对数函数对比", "指数和对数对比", "指数对数对比"]):
            keyword_theme = "指数函数,对数函数"
        else:
            keyword_theme = self._extract_theme_with_keywords(cleaned_query)
        print(f"✅ 关键词匹配结果: '{keyword_theme}'")
        
        # 5. 基于查询意图调整主题提取策略
        if intent == '比较':
            # 对于比较类查询，尝试提取多个主题
            print("   📝 比较类查询，尝试提取多个主题")
            # 检查是否包含比较关键词
            comparison_words = ["比较", "对比", "区别", "联系", "异同"]
            if any(word in query for word in comparison_words):
                # 尝试从查询中提取两个主题
                # 改进：增强对比类查询的主题提取
                print("   📝 增强对比类查询的主题提取...")
                # 分割查询，提取两个主题
                parts = query.split('和')
                if len(parts) == 2:
                    theme1 = self._extract_theme_with_keywords(parts[0].strip())
                    theme2 = self._extract_theme_with_keywords(parts[1].strip())
                    if theme1 and theme2:
                        keyword_theme = f"{theme1},{theme2}"
                        print(f"   ✅ 提取到对比主题: {keyword_theme}")
                # 处理其他分割词
                elif '与' in query:
                    parts = query.split('与')
                    if len(parts) == 2:
                        theme1 = self._extract_theme_with_keywords(parts[0].strip())
                        theme2 = self._extract_theme_with_keywords(parts[1].strip())
                        if theme1 and theme2:
                            keyword_theme = f"{theme1},{theme2}"
                            print(f"   ✅ 提取到对比主题: {keyword_theme}")
        
        # 6. 如果关键词匹配成功提取到具体主题，直接使用
        # V65.0改进：当查询包含资源类型词时，允许提取"函数"这样的通用主题
        if keyword_theme and (keyword_theme not in ["函数", "数学", "教学"] or has_resource_type or intent):
            print("✅ 使用关键词匹配结果作为核心主题")
            return keyword_theme
        
        # 7. V72.0改进：如果查询包含资源类型词，且关键词匹配失败，尝试从原始查询中提取主题
        if has_resource_type and not keyword_theme:
            print("   📝 V72.0改进：查询包含资源类型词，尝试从原始查询中提取主题")
            keyword_theme = self._extract_theme_with_keywords(query)
            print(f"   ✅ 从原始查询提取的主题: '{keyword_theme}'")
            if keyword_theme:
                print("✅ 使用从原始查询提取的主题作为核心主题")
                return keyword_theme
        
        # 8. 备用方案：使用LLM动态提取主题
        try:
            print("🤖 尝试使用LLM提取主题...")
            llm_theme = self._extract_theme_with_llm(cleaned_query, has_resource_type, intent)
            if llm_theme:
                print(f"✅ LLM提取的主题: '{llm_theme}'")
                return llm_theme
            else:
                print("⚠️ LLM返回空结果")
        except Exception as e:
            print(f"❌ LLM主题提取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 9. 如果LLM也失败，使用关键词匹配结果
        print("✅ 使用关键词匹配结果作为核心主题")
        return keyword_theme
