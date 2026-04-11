from .._shared import *


class _ProcessLessonPlanResourceMixin:
    def _process_lesson_plan_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理教案资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        # 教案资源使用标题和内容
        title = metadata.get('title', '')
        content = metadata.get('content', '')
        chapter = metadata.get('章节', '')
        knowledge_tags = metadata.get('知识点标签', '')
        file_topic = metadata.get('文件名主题', '')
        
        resource['title'] = f"教案: {title}"
        resource['content'] = content
        resource['source'] = metadata.get('云端链接', '') or metadata.get('原文件云端链接', '') or metadata.get('source_file', '')
        # 传递元数据给主题匹配器
        resource['章节'] = chapter
        resource['知识点标签'] = knowledge_tags
        resource['文件名主题'] = file_topic
        resource['cloud_url'] = metadata.get('云端链接', '')
        resource['original_file_url'] = metadata.get('原文件云端链接', '')
        resource['original_filename'] = metadata.get('原文件名', '')
        resource['related_file'] = metadata.get('关联文件', '')
        resource['full_path'] = metadata.get('完整路径', '')
        
        # V9.1：提取教案内容特征（教学方法、教学环节等）
        try:
            content_features = self.content_extractor.extract_features(content, title)
            resource['content_features'] = content_features
            resource['teaching_methods'] = content_features.get('teaching_methods', [])
            resource['teaching_stages'] = content_features.get('teaching_stages', [])
            resource['teaching_tools'] = content_features.get('teaching_tools', [])
        except Exception as e:
            # 如果特征提取失败，不影响正常使用
            resource['content_features'] = {}
            resource['teaching_methods'] = []
            resource['teaching_stages'] = []
            resource['teaching_tools'] = []
