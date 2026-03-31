from .._shared import *


class _ProcessSyllabusResourceMixin:
    def _process_syllabus_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理教学大纲资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        chapter = metadata.get('章节', '')
        task = metadata.get('教学任务（教学内容）', '')
        
        resource['title'] = f"教学大纲: {chapter}"
        resource['content'] = f"章节：{chapter}\n教学任务：{task}"
