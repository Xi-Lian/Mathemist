from .._shared import *


class _EnhanceSearchTextMixin:
    def _enhance_search_text(self, base_text: str, resource_type: str, resource: Dict[str, str]) -> str:
        """
        V54.0改进：增强搜索文本，动态添加相关关键词
        
        Args:
            base_text: 基础搜索文本
            resource_type: 资源类型
            resource: 资源字典
            
        Returns:
            增强后的搜索文本
        """
        enhanced_parts = [base_text]
        
        # 获取资源内容
        content = resource.get('内容', '') or resource.get('教学任务（教学内容）', '') or resource.get('分析', '') or resource.get('题干', '')
        filename = resource.get('文件名', '') or resource.get('视频文件名/网址', '') or resource.get('题目文件名', '')
        chapter = resource.get('章节', '')
        source_file = resource.get('source_file', '')
        
        # 合并所有文本进行分析
        all_text = f"{base_text} {content} {filename} {chapter} {source_file}"
        
        # 动态提取函数类型
        function_types = self._extract_keywords_from_text(all_text, self.function_types)
        for func_type in function_types:
            if func_type not in base_text:
                enhanced_parts.append(func_type)
        
        # 动态提取函数性质
        function_props = self._extract_keywords_from_text(all_text, self.function_properties)
        for prop in function_props:
            # 如果是函数性质，确保包含"函数"前缀
            if prop not in base_text:
                if '函数' not in prop:
                    enhanced_parts.append(f"函数的{prop}")
                else:
                    enhanced_parts.append(prop)
        
        # 动态提取数学主题
        math_topics = self._extract_keywords_from_text(all_text, self.math_topics)
        for topic in math_topics:
            if topic not in base_text:
                enhanced_parts.append(topic)
        
        # 动态提取年级信息
        for grade, keywords in self.grade_keywords.items():
            if any(kw in all_text for kw in keywords):
                if grade not in base_text:
                    enhanced_parts.append(grade)
                break
        
        # 动态提取教学场景
        scenarios = self._extract_keywords_from_text(all_text, self.teaching_scenarios)
        for scenario in scenarios:
            if scenario not in base_text:
                enhanced_parts.append(scenario)
        
        # 去重并返回
        unique_parts = []
        seen = set()
        for part in enhanced_parts:
            if part not in seen:
                unique_parts.append(part)
                seen.add(part)
        
        return '，'.join(unique_parts)
