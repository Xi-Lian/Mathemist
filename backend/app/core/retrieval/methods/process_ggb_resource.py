from .._shared import *


class _ProcessGgbResourceMixin:
    def _process_ggb_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理GGB资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        filename = metadata.get('ggb文件名', '')
        chapter = metadata.get('章节', '')
        usage = metadata.get('教学用途', '')
        
        resource['title'] = f"GGB资源: {filename}"
        resource['content'] = f"章节：{chapter}\n教学用途：{usage}"
        resource['filename'] = filename
