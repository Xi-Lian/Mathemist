from .._shared import *
import re


class _ExtractCoreThemeMixin:
    @staticmethod
    def _normalize_theme(theme: str) -> str:
        """
        规范化主题，去除过于具体的修饰词，返回更通用的主题
        """
        if not theme:
            return theme
        
        # 去除常见的过于具体的后缀（按长度从长到短排序）
        # 【V108.0修复】保留"应用"后缀，因为"应用"表示用户想要实际应用题目，而不是纯数学概念
        suffixes_to_remove = [
            "的单调性", "的奇偶性", "的周期性", "的对称性", "的零点",
            "公式", "定理", "法则", "性质", "定义", "概念", "运算", "计算"
            # 注意：不再去除"应用"，因为"应用"是重要的语义信息
        ]
        
        for suffix in suffixes_to_remove:
            if theme.endswith(suffix):
                theme = theme[:-len(suffix)].strip()
                # 递归检查，可能有多个后缀需要去除
                theme = _ExtractCoreThemeMixin._normalize_theme(theme)
                break
        
        # 去除末尾的"的"字（处理"组合数的性质"-> "组合数的" -> "组合数"）
        if theme.endswith("的"):
            theme = theme[:-1].strip()
        
        # 去除常见的过于具体的前缀
        prefixes_to_remove = ["的", "与", "和", "及"]
        for prefix in prefixes_to_remove:
            if theme.startswith(prefix):
                theme = theme[len(prefix):].strip()
                # 递归检查，可能有多个前缀需要去除
                theme = _ExtractCoreThemeMixin._normalize_theme(theme)
                break
        
        return theme

    @staticmethod
    def _fallback_theme_from_cleaned_query(cleaned_query: str) -> str:
        candidate = re.sub(r"\s+", "", cleaned_query or "")
        candidate = re.sub(r"^(给我|帮我找|帮我|找|推荐|来|要)", "", candidate)
        candidate = re.sub(r"^\d+", "", candidate)
        candidate = re.sub(r"^[几多少两一二三四五六七八九十百千道个份套题]+", "", candidate)
        candidate = candidate.strip("，。；：:,.!?！？")
        if len(candidate) < 2:
            return ""

        math_markers = (
            "函数", "三角", "正弦", "余弦", "正切", "对数", "指数", "幂函数",
            "导数", "数列", "概率", "统计", "圆锥曲线", "立体几何", "向量", "解析几何", "复数", "虚数"
        )
        if any(marker in candidate for marker in math_markers):
            return candidate
        return ""

    def _extract_core_theme(self, query: str, is_exercise: bool = False) -> tuple:
        """
        提取核心主题和板块（优先使用LLM动态提取，支持完整主题识别，支持多个主题）
        
        Args:
            query: 用户查询
            is_exercise: 是否是习题检索（如果是，需要识别组合查询）
            
        Returns:
            (核心主题字符串, 板块名称)（多个主题用逗号分隔）
        """
        print(f"🔍 开始提取核心主题，查询: '{query}'")
        
        # 1. 直接提取查询意图
        intent = ''
        intent_patterns = [
            ('练习', ['练习课', '练习题', '习题', '题目', '测试题', '题']),
            ('学习', ['学习', '了解', '掌握', '理解', '认识']),
            ('教学', ['教学', '教案', '课件', '教学设计', '教学方案']),
            ('复习', ['复习课', '复习', '巩固', '回顾', '总结']),
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
        
        # 2. 检查查询中是否包含资源类型词
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
            # 【V108.0修复】不再去除"应用"和"实际应用"，因为它们是重要的语义信息，表示用户想要实际应用题目
            # "应用", "实际应用", "实践",  # 已注释
            "复杂"  # 【V107.0新增】识别"复杂"为难度要求
        ]
        for word in modifier_words:
            cleaned_query = cleaned_query.replace(word, "").strip()
        
        if cleaned_query != query:
            print(f"   📝 清理后的查询: '{cleaned_query}'")
        
        # 4. 优先使用LLM提取主题和板块
        print("🤖 优先使用LLM提取主题和板块...")
        try:
            llm_theme, llm_board = self._extract_theme_with_llm(cleaned_query, has_resource_type, intent, is_exercise)
            if llm_theme and llm_theme.strip():
                # V310.0改进：规范化主题，去除过于具体的修饰词
                normalized_llm_theme = self._normalize_theme(llm_theme)
                print(f"✅ 使用LLM提取的主题: '{llm_theme}'，规范化后: '{normalized_llm_theme}'，板块: '{llm_board}'")
                return normalized_llm_theme, llm_board
            else:
                print("⚠️ LLM返回空结果，尝试使用关键词匹配")
        except Exception as e:
            print(f"❌ LLM主题提取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. 使用关键词匹配作为备用方案
        print("🔑 使用关键词匹配提取主题...")
        keyword_theme = self._extract_theme_with_keywords(cleaned_query)
        print(f"✅ 关键词匹配结果: '{keyword_theme}'")
        
        # 6. 基于查询意图调整主题提取策略
        if intent == '比较':
            print("   📝 比较类查询，尝试提取多个主题")
            comparison_words = ["比较", "对比", "区别", "联系", "异同"]
            if any(word in query for word in comparison_words):
                print("   📝 增强对比类查询的主题提取...")
                parts = query.split('和')
                if len(parts) == 2:
                    theme1 = self._extract_theme_with_keywords(parts[0].strip())
                    theme2 = self._extract_theme_with_keywords(parts[1].strip())
                    if theme1 and theme2:
                        keyword_theme = f"{theme1},{theme2}"
                        print(f"   ✅ 提取到对比主题: {keyword_theme}")
                elif '与' in query:
                    parts = query.split('与')
                    if len(parts) == 2:
                        theme1 = self._extract_theme_with_keywords(parts[0].strip())
                        theme2 = self._extract_theme_with_keywords(parts[1].strip())
                        if theme1 and theme2:
                            keyword_theme = f"{theme1},{theme2}"
                            print(f"   ✅ 提取到对比主题: {keyword_theme}")
        
        # 7. 如果关键词匹配成功提取到具体主题，直接使用
        if keyword_theme and (keyword_theme not in ["函数", "数学", "教学"] or has_resource_type or intent):
            print("✅ 使用关键词匹配结果作为核心主题")
            # V310.0改进：规范化主题，去除过于具体的修饰词
            normalized_keyword_theme = self._normalize_theme(keyword_theme)
            if normalized_keyword_theme != keyword_theme:
                print(f"   📝 主题规范化: '{keyword_theme}' -> '{normalized_keyword_theme}'")
            # 对于关键词匹配结果，使用旧的板块识别逻辑
            from ..retrieve_helpers.single_theme import _get_top_board
            board = _get_top_board(normalized_keyword_theme, self.knowledge_hierarchy)
            return normalized_keyword_theme, board
        
        # 8. 如果查询包含资源类型词，且关键词匹配失败，尝试从原始查询中提取主题
        if has_resource_type and not keyword_theme:
            print("   📝 查询包含资源类型词，尝试从原始查询中提取主题")
            keyword_theme = self._extract_theme_with_keywords(query)
            print(f"   ✅ 从原始查询提取的主题: '{keyword_theme}'")
            if keyword_theme:
                print("✅ 使用从原始查询提取的主题作为核心主题")
                # V310.0改进：规范化主题
                normalized_keyword_theme = self._normalize_theme(keyword_theme)
                from ..retrieve_helpers.single_theme import _get_top_board
                board = _get_top_board(normalized_keyword_theme, self.knowledge_hierarchy)
                return normalized_keyword_theme, board

        heuristic_theme = self._fallback_theme_from_cleaned_query(cleaned_query)
        if has_resource_type and heuristic_theme:
            print(f"   ✅ 启发式提取主题: '{heuristic_theme}'")
            # V310.0改进：规范化主题
            normalized_heuristic_theme = self._normalize_theme(heuristic_theme)
            from ..retrieve_helpers.single_theme import _get_top_board
            board = _get_top_board(normalized_heuristic_theme, self.knowledge_hierarchy)
            return normalized_heuristic_theme, board

        # 9. 使用关键词匹配结果
        print("✅ 使用关键词匹配结果作为核心主题")
        # V310.0改进：规范化主题
        normalized_keyword_theme = self._normalize_theme(keyword_theme)
        from ..retrieve_helpers.single_theme import _get_top_board
        board = _get_top_board(normalized_keyword_theme, self.knowledge_hierarchy)
        return normalized_keyword_theme, board
