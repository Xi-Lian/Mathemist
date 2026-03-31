from .._shared import *


class _ProcessCoursewareResourceMixin:
    def _process_courseware_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理课件资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        content = metadata.get('内容', '')
        filename = metadata.get('文件名', '')
        usage = metadata.get('教学用途', '')
        
        resource['title'] = f"课件: {filename}"
        resource['content'] = f"内容：{content}\n教学用途：{usage}"
        resource['filename'] = filename
