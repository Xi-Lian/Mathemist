from .._shared import *


class _GetResourceFilenameMixin:
    def get_resource_filename(self, resource: Dict[str, str]) -> Optional[str]:
        """
        获取资源的文件名
        
        Args:
            resource: 资源字典
            
        Returns:
            文件名，如果没有则返回None
        """
        resource_type = resource.get('resource_type', '')
        
        if resource_type == 'ggb':
            return resource.get('ggb文件名')
        
        elif resource_type == 'exercise':
            return resource.get('题目文件名')
        
        elif resource_type in ['lesson_plan', 'theory']:
            return resource.get('原文件云端链接') or resource.get('云端链接') or resource.get('source_file')
        
        elif resource_type == 'courseware':
            return resource.get('文件名')
        
        elif resource_type == 'lesson_case':
            return resource.get('视频文件名/网址')
        
        return None
