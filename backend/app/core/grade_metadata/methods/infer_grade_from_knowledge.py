from .._shared import *


class _InferGradeFromKnowledgeMixin:
    def infer_grade_from_knowledge(self, knowledge_tags: str) -> Optional[Dict[str, Any]]:
        """
        从知识点标签推断年级信息
        
        Args:
            knowledge_tags: 知识点标签字符串（分号分隔）
            
        Returns:
            年级信息字典
        """
        if not knowledge_tags:
            return None
        
        tags = [tag.strip() for tag in knowledge_tags.split(';')]
        
        # 统计各年级出现的次数
        grade_counts = {}
        for tag in tags:
            for knowledge, grade in self.KNOWLEDGE_TO_GRADE.items():
                if knowledge in tag:
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        if grade_counts:
            # 选择出现次数最多的年级
            best_grade = max(grade_counts.keys(), key=lambda g: grade_counts[g])
            grade_level = self._grade_to_level(best_grade)
            
            return {
                'grade': best_grade,
                'grade_level': grade_level,
                'inference_source': 'knowledge_tags',
                'confidence': min(0.7 + 0.1 * grade_counts[best_grade], 0.9)
            }
        
        return None
