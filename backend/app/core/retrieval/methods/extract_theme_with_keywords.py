from .._shared import *


class _ExtractThemeWithKeywordsMixin:
    def _extract_theme_with_keywords(self, query: str) -> str:
        """
        使用关键词匹配提取主题（备用方案）- 改进版
        支持连接词分割和多主题提取
        
        Args:
            query: 用户查询
            
        Returns:
            核心主题字符串（多个主题用逗号分隔）
        """
        # 收集所有匹配的主题
        matched_themes = []
        
        # V53.3改进：动态获取完整主题列表，从knowledge_hierarchy中提取
        # 不再硬编码具体主题，使系统能够自动适应资源库扩展
        complete_themes = self.all_themes
        
        # 打印完整主题列表，方便调试
        print(f"   📋 完整主题列表: {complete_themes}")
        
        print(f"🔑 关键词匹配 - 查询: '{query}'")
        
        # 改进1：使用连接词分割查询，分别提取每个部分的主题
        # 定义连接词列表
        conjunctions = ['和', '与', '及', '、', '以及', '还有', '跟', '同']
        
        # 分割查询为多个子查询
        sub_queries = [query]
        
        # 对每个连接词进行分割
        for conj in conjunctions:
            temp_sub_queries = []
            for sq in sub_queries:
                if conj in sq:
                    parts = sq.split(conj)
                    temp_sub_queries.extend([p.strip() for p in parts if p.strip()])
                else:
                    temp_sub_queries.append(sq)
            sub_queries = temp_sub_queries
        
        # 去重并保持顺序
        seen = set()
        unique_sub_queries = []
        for sq in sub_queries:
            if sq not in seen:
                seen.add(sq)
                unique_sub_queries.append(sq)
        sub_queries = unique_sub_queries
        
        if len(sub_queries) > 1:
            print(f"   🔄 检测到连接词，将查询分割为 {len(sub_queries)} 个子查询: {sub_queries}")
        
        # 对每个子查询分别提取主题
        for sub_query in sub_queries:
            # 优先匹配完整主题（支持去掉"的"字的匹配）
            query_without_de = sub_query.replace("的", "")
            
            # 特殊处理：如果子查询是函数性质关键词，自动添加"函数的"前缀
            function_property_keywords = ["单调性", "奇偶性", "周期性", "对称性", "零点", "定义域", "值域", "性质"]
            for prop in function_property_keywords:
                if prop in sub_query:
                    enhanced_sub_query = f"函数的{prop}"
                    print(f"   📝 增强子查询: '{sub_query}' -> '{enhanced_sub_query}'")
                    sub_query = enhanced_sub_query
                    query_without_de = sub_query.replace("的", "")
                    break
            
            # V53.3改进：不再硬编码三角函数主题，让所有主题都按顺序匹配
            # 直接匹配所有完整主题（支持去掉"的"字的匹配）
            for theme in complete_themes:
                # 去掉"的"字进行比较
                theme_without_de = theme.replace("的", "")
                
                # 检查完整匹配或关键词匹配
                if (theme in sub_query or 
                    theme_without_de in query_without_de or
                    any(keyword in sub_query for keyword in self.knowledge_hierarchy.get(theme, {}).get('keywords', []))):
                    if theme not in matched_themes:
                        print(f"   ✓ 匹配到完整主题: '{theme}' (来自子查询: '{sub_query}')")
                        matched_themes.append(theme)
        
        # 如果没有匹配到完整主题，使用关键词匹配
        if not matched_themes:
            print(f"   ℹ️  没有匹配到完整主题，使用关键词匹配")
            
            # V53.2改进：使用动态生成的主题关键词，而不是硬编码
            # 从 knowledge_hierarchy 中动态构建 theme_keywords
            theme_keywords = {}
            for theme in self.all_themes:
                theme_info = self.knowledge_hierarchy.get(theme, {})
                keywords = theme_info.get('keywords', [])
                if keywords:
                    theme_keywords[theme] = keywords
            
            # V53.2改进：使用所有主题作为优先级顺序
            priority_order = self.all_themes
            
            for sub_query in sub_queries:
                for theme in priority_order:
                    for keyword in theme_keywords.get(theme, []):
                        if keyword in sub_query and theme not in matched_themes:
                            print(f"   ✓ 匹配到关键词: '{keyword}' -> 主题: '{theme}'")
                            matched_themes.append(theme)
        

        
        # V53.2改进：动态识别应用场景
        # 检查是否包含应用场景关键词
        application_keywords = ["应用", "实际", "问题", "案例", "场景", "生活", "建模", "实际应用", "应用问题", "实际场景"]
        has_application = any(keyword in query for keyword in application_keywords)
        
        # V53.2改进：动态识别包含"应用"的主题，而不是硬编码
        if has_application:
            # 找到所有包含"应用"的主题
            app_themes = [theme for theme in self.all_themes if "应用" in theme]
            
            # 检查是否已经匹配到基础主题，如果是，添加对应的应用主题
            for app_theme in app_themes:
                # 尝试从应用主题中提取基础主题（去掉"的应用"或"应用"）
                base_theme = app_theme.replace("的应用", "").replace("应用", "").strip()
                if base_theme and base_theme in matched_themes and app_theme not in matched_themes:
                    print(f"   📝 增强应用场景识别：添加'{app_theme}'主题")
                    matched_themes.append(app_theme)
        
        # 动态语义关联检测：如果仍然没有匹配到主题，尝试使用向量相似度查找相关资源
        if not matched_themes:
            print(f"   🔍 尝试动态语义关联检测...")
            # 提取查询的核心概念（去除常见词）
            query_clean = query.replace("帮我找", "").replace("教案", "").replace("的", "").replace("一下", "").strip()
            if query_clean:
                # 特殊处理：如果查询包含"图像"，尝试匹配函数相关主题
                if "图像" in query_clean:
                    print(f"   📝 检测到'图像'关键词，尝试匹配函数相关主题")
                    # 遍历所有函数相关主题
                    for theme in self.all_themes:
                        if "函数" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"图像"但还没有匹配到主题，尝试匹配三角函数相关主题
                if not matched_themes and "图像" in query_clean:
                    print(f"   📝 尝试匹配三角函数相关主题")
                    for theme in self.all_themes:
                        if "三角" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加三角函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"函数"，尝试匹配函数相关主题
                if not matched_themes and "函数" in query_clean:
                    print(f"   📝 检测到'函数'关键词，尝试匹配函数相关主题")
                    for theme in self.all_themes:
                        if "函数" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"概念"，尝试匹配函数概念主题
                if not matched_themes and "概念" in query_clean:
                    print(f"   📝 检测到'概念'关键词，尝试匹配函数概念主题")
                    for theme in self.all_themes:
                        if "函数的概念" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数概念主题: '{theme}'")
                            break
                # 如果仍然没有匹配到主题，使用查询本身作为主题
                if not matched_themes:
                    print(f"   📝 使用查询本身作为主题: '{query_clean}'")
                    matched_themes.append(query_clean)
        
        # V53.1改进：通用主题处理，不再硬编码具体主题
        # 如果没有匹配到任何具体主题，但查询包含主题关键词和资源类型词，返回相应的通用主题
        if not matched_themes:
            # 检查是否是资源请求
            resource_request_patterns = ["来几道", "来一些", "给我", "找", "推荐", "有没有", "要几道"]
            is_resource_request = any(pattern in query for pattern in resource_request_patterns)
            
            # 检查是否包含资源类型词
            resource_type_keywords = ["选择题", "习题", "题目", "练习题", "测试题", "教案", "课件", "GGB", "教学大纲", "课例"]
            has_resource_type = any(keyword in query for keyword in resource_type_keywords)
            
            # V53.1改进：使用动态生成的主题关键词，而不是硬编码
            # 检查查询中是否包含任何主题关键词
            for theme in self.all_themes:
                theme_keywords = self.knowledge_hierarchy.get(theme, {}).get('keywords', [])
                if any(kw in query for kw in theme_keywords):
                    # 如果是资源请求或包含资源类型词，添加该主题
                    if is_resource_request or has_resource_type:
                        print(f"   📝 通用主题处理：添加'{theme}'主题")
                        matched_themes.append(theme)
                    break
            
            # V61.0改进：如果仍然没有匹配到主题，添加默认主题"函数"
            if not matched_themes:
                print(f"   📝 默认主题处理：添加'函数'主题")
                matched_themes.append("函数")
        
        result = ",".join(matched_themes) if matched_themes else "函数"
        print(f"   ✅ 关键词匹配结果: '{result}'")
        return result
