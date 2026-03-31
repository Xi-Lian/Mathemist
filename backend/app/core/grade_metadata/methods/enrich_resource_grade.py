from .._shared import *


class _EnrichResourceGradeMixin:
    def enrich_resource_grade(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        为资源添加年级元数据
        
        Args:
            resource: 资源字典
            
        Returns:
            添加了年级信息的资源字典
        """
        resource_type = resource.get('resource_type', '')
        
        # 尝试多种方式推断年级
        grade_info = None
        confidence = 0
        
        # 1. 从文件路径推断（置信度最高）
        source_file = resource.get('source_file', '')
        if source_file:
            grade_info = self.infer_grade_from_path(source_file)
            if grade_info:
                confidence = grade_info.get('confidence', 0)
        
        # 2. 从知识点标签推断（如果路径推断置信度不够）
        if confidence < 0.8:
            knowledge_tags = resource.get('知识点标签', '')
            knowledge_grade = self.infer_grade_from_knowledge(knowledge_tags)
            if knowledge_grade and knowledge_grade.get('confidence', 0) > confidence:
                grade_info = knowledge_grade
                confidence = knowledge_grade['confidence']
        
        # 3. 从标题推断（最后尝试）
        if confidence < 0.7:
            title = resource.get('title', '')
            title_grade = self.infer_grade_from_title(title)
            if title_grade and title_grade.get('confidence', 0) > confidence:
                grade_info = title_grade
                confidence = title_grade['confidence']
        
        # 添加年级信息到资源
        if grade_info:
            resource['grade'] = grade_info['grade']
            resource['grade_level'] = grade_info['grade_level']
            resource['grade_inference_source'] = grade_info['inference_source']
            resource['grade_confidence'] = confidence
        else:
            # 默认设置
            resource['grade'] = '未知'
            resource['grade_level'] = 0
            resource['grade_inference_source'] = 'none'
            resource['grade_confidence'] = 0
        
        return resource
