from .._shared import *


class _ApplyFlexibleGradeFilterMixin:
    def _apply_flexible_grade_filter(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V32.0：应用灵活的年级筛选（用于宽泛查询）
        
        策略：
        - 宽泛查询时，放宽年级筛选，允许各年级相关内容
        - 优先返回查询年级的内容，但也允许其他年级的相关内容
        - 通过调整相关性得分来体现优先级
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
            
        Returns:
            筛选结果字典
        """
        source_file = metadata.get('source_file', '')
        
        # 使用年级元数据增强器推断资源的年级
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        
        if not resource_grade:
            # 无法推断年级，默认通过
            return {'pass': True, 'reason': '无法推断资源年级', 'score_adjustment': 0.8}
        
        target_grade = grade_info.get('grade')
        target_grade_level = grade_info.get('grade_level')
        resource_grade_level = resource_grade.get('grade_level')
        
        # 完全匹配 - 最高优先级
        if resource_grade.get('grade') == target_grade:
            return {'pass': True, 'reason': f'年级完全匹配: {target_grade}', 'score_adjustment': 1.0}
        
        # 高三查询 - 允许高一、高二、高三的所有内容（复习需要）
        if target_grade_level and target_grade_level >= 14:  # 高三
            if resource_grade_level:
                if resource_grade_level <= 14:  # 高一、高二、高三
                    # 根据距离调整得分
                    level_diff = abs(target_grade_level - resource_grade_level)
                    score_adjustment = max(0.6, 1.0 - level_diff * 0.15)  # 最多降低40%
                    return {
                        'pass': True, 
                        'reason': f'高三复习: 包含{resource_grade.get("grade")}内容',
                        'score_adjustment': score_adjustment
                    }
        
        # 其他年级查询 - 允许相邻年级的内容
        if target_grade_level and resource_grade_level:
            level_diff = abs(resource_grade_level - target_grade_level)
            if level_diff <= 2:  # 允许相差2个级别（如高一和高二）
                score_adjustment = max(0.5, 1.0 - level_diff * 0.2)  # 最多降低60%
                return {
                    'pass': True,
                    'reason': f'年级相近: {resource_grade.get("grade")} vs {target_grade}',
                    'score_adjustment': score_adjustment
                }
        
        # 年级相差太大，降低相关性但不完全过滤
        return {
            'pass': True,
            'reason': f'年级较远但仍相关: {resource_grade.get("grade")} vs {target_grade}',
            'score_adjustment': 0.4  # 大幅降低相关性
        }
