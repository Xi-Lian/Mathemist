from .._shared import *


class _ApplyGradeFilterMixin:
    def _apply_grade_filter(self, classified: Dict[str, Any], grade_info: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """
        V33.0: 应用年级过滤
        
        Args:
            classified: 分类后的资源
            grade_info: 年级信息
            query: 查询文本
        
        Returns:
            过滤后的资源
        """
        target_grade = grade_info.get('grade', '')
        if not target_grade:
            return classified
        
        grade_keywords = {
            '高一上学期': ['必修一', '必修第一册', '高一上', '第一章', '第二章', '第三章', '第四章', '第五章'],
            '高一下学期': ['必修二', '必修第二册', '高一下', '第六章', '第七章', '第八章', '第九章', '第十章'],
            '高二上学期': ['选择性必修一', '高二上', '必修一', '必修二'],  # 增加必修一和必修二
            '高二下学期': ['选择性必修二', '高二下', '必修一', '必修二'],  # 增加必修一和必修二
            '高三': ['选择性必修三', '高三', '高考', '必修一', '必修二', '选择性必修一', '选择性必修二'],  # V52.0改进：高三可以匹配所有年级
            '高一': ['必修一', '必修二', '必修第一册', '必修第二册', '高一'],
            '高二': ['选择性必修一', '选择性必修二', '选择性必修三', '高二', '必修一', '必修二'],  # 增加必修一和必修二
        }
        
        keywords = grade_keywords.get(target_grade, [])
        if not keywords:
            return classified
        
        # V53.1改进：使用动态生成的主题关键词，而不是硬编码
        # 这样当资源库扩展时，系统也能自动适应
        
        # V94.0改进：优化年级过滤逻辑
        # - 高一高二：年级词不重要，重点在于知识点匹配，完全禁用年级过滤
        # - 高三：年级比较重要，因为是复习巩固，但也可以匹配所有年级
        if target_grade in ['高一', '高二']:
            print(f"   🎓 V94.0高一高二查询: 禁用年级过滤，重点在知识点匹配")
            return classified
        elif target_grade == '高三':
            print(f"   🎓 V52.0高三查询: 禁用年级过滤，允许所有年级资源（复习性质）")
            return classified
        
        # 增强的年级匹配逻辑
        print(f"   🎓 应用年级过滤: 目标年级='{target_grade}', 关键词={keywords}")
        
        for category in classified:
            if isinstance(classified[category], list):
                filtered = []
                for resource in classified[category]:
                    # 获取资源信息
                    source_file = resource.get('source', '')
                    title = resource.get('title', '')
                    
                    # 获取知识点标签（可能在metadata中或直接在resource中）
                    metadata = resource.get('metadata', {})
                    knowledge_tags = metadata.get('知识点标签', '')
                    content = resource.get('content', '')
                    
                    # 检查是否包含年级关键词
                    match_found = False
                    for keyword in keywords:
                        if keyword in source_file or keyword in title or keyword in knowledge_tags or keyword in content:
                            match_found = True
                            print(f"   ✅ 年级关键词匹配: '{keyword}' 在 '{title}' 中")
                            break
                    
                    # V53.1改进：如果是跨年级主题，允许更宽松的年级匹配
                    if not match_found:
                        is_cross_grade_topic = False
                        for keyword in self.all_theme_keywords:
                            if keyword in knowledge_tags or keyword in title or keyword in content or keyword in source_file:
                                is_cross_grade_topic = True
                                break
                        
                        if is_cross_grade_topic:
                            # 对于跨年级主题，允许跨年级匹配
                            # 例如：高二的三角函数查询可以匹配高一的三角函数资源
                            match_found = True
                            print(f"   🎓 跨年级主题宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    # 特殊处理2：如果是习题资源，允许更宽松的年级匹配
                    if not match_found:
                        resource_type = metadata.get('resource_type', '')
                        if resource_type == 'exercise':
                            # 对于习题资源，只要主题相关，就允许跨年级匹配
                            match_found = True
                            print(f"   🎓 习题资源宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    # 特殊处理3：如果查询包含"应用"关键词，允许更宽松的年级匹配
                    if not match_found:
                        if '应用' in query or '应用题' in query:
                            # 对于应用题查询，只要主题相关，就允许跨年级匹配
                            match_found = True
                            print(f"   🎓 应用题查询宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    if match_found:
                        filtered.append(resource)
                    else:
                        print(f"   🎓 年级过滤移除: '{title}' (目标年级: {target_grade})")
                
                classified[category] = filtered
                print(f"   📊 {category} 过滤后剩余 {len(filtered)} 条资源")
        
        return classified
