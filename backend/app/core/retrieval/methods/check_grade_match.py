from .._shared import *


class _CheckGradeMatchMixin:
    def _check_grade_match(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V28.0：应用年级筛选
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
        
        Returns:
            筛选结果字典，包含pass和reason
        """
        source_file = metadata.get('source_file', '')
        
        # 使用年级元数据增强器推断资源的年级
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        
        if not resource_grade:
            # 无法推断年级，默认通过
            return {'pass': True, 'reason': '无法推断资源年级'}
        
        # 检查年级是否匹配
        target_grade = grade_info.get('grade')
        target_grade_level = grade_info.get('grade_level')
        
        if resource_grade.get('grade') == target_grade:
            # 年级完全匹配
            return {'pass': True, 'reason': f'年级匹配: {target_grade}'}
        
        # V53.0改进：检查资源年级是否包含目标年级
        # 例如："高一上学期"包含"高一"，"高一下学期"包含"高一"
        resource_grade_str = resource_grade.get('grade', '')
        if target_grade and target_grade in resource_grade_str:
            return {'pass': True, 'reason': f'年级包含匹配: {resource_grade_str}包含{target_grade}'}
        
        # V53.1改进：检查是否是跨年级主题的查询
        # 某些主题（如函数、概率、立体几何等）在高中各年级都有学习，允许更宽松的年级匹配
        is_cross_grade_topic = False
        knowledge_tags = metadata.get('知识点标签', '')
        title = metadata.get('title', '')
        content = metadata.get('题干', '') + metadata.get('解析', '')
        
        # V53.1改进：使用动态生成的主题关键词，而不是硬编码
        # 这样当资源库扩展时，系统也能自动适应
        for keyword in self.all_theme_keywords:
            if keyword in knowledge_tags or keyword in title or keyword in content:
                is_cross_grade_topic = True
                break
        
        # 对于跨年级主题，允许更宽松的年级匹配
        if is_cross_grade_topic:
            # 跨年级主题允许相差2个级别（如高一和高二）
            resource_grade_level = resource_grade.get('grade_level')
            if resource_grade_level and target_grade_level:
                level_diff = abs(resource_grade_level - target_grade_level)
                if level_diff <= 2:
                    return {'pass': True, 'reason': f'跨年级主题: 允许查看{resource_grade.get("grade")}的内容'}
        
        # 检查年级级别是否匹配（允许一定的灵活性）
        resource_grade_level = resource_grade.get('grade_level')
        if resource_grade_level and target_grade_level:
            # 对于高三查询，允许查看高一、高二的内容（高考复习需要）
            if target_grade_level >= 14:  # 高三
                if resource_grade_level <= 14:  # 高一、高二、高三
                    return {'pass': True, 'reason': f'高三复习: 允许查看{resource_grade.get("grade")}的内容'}
            # 对于其他年级，允许相邻年级
            elif abs(resource_grade_level - target_grade_level) <= 1:
                return {'pass': True, 'reason': f'年级相近: {resource_grade.get("grade")} vs {target_grade}'}
        
        # 年级不匹配
        return {
            'pass': False,
            'reason': f'年级不匹配: 资源是{resource_grade.get("grade")}，查询要求{target_grade}'
        }
