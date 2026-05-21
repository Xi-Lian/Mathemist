from .._shared import *


class _FormatExcellentCaseResourcesMixin:
    def _format_excellent_case_resources(self, excellent_case_resources: List[Dict[str, Any]]) -> str:
        """
        格式化优秀案例分析资源
        
        Args:
            excellent_case_resources: 优秀案例分析资源列表
            
        Returns:
            格式化后的优秀案例分析资源文本
        """
        if not excellent_case_resources:
            return ""
        
        formatted_resources = []
        for i, resource in enumerate(excellent_case_resources[:3], 1):  # 限制最多使用3个优秀案例
            title = resource.get('title', '未知优秀案例')
            content = resource.get('content', '')
            
            # 提取核心内容（前500字符）
            content_preview = content[:500] + '...' if len(content) > 500 else content
            
            formatted_resource = f"### 优秀案例分析 {i}: {title}\n\n{content_preview}\n"
            formatted_resources.append(formatted_resource)
        
        return '\n'.join(formatted_resources)