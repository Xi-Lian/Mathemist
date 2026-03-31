from .._shared import *


class _ClassifyResourceDomainMixin:
    def _classify_resource_domain(self, resource: Dict[str, Any]) -> str:
        """
        根据教案标题和内容判断所属领域
        
        Args:
            resource: 资源字典
            
        Returns:
            领域名称：一般函数、具体函数、三角函数、其他
        """
        title = resource.get("title", "")
        content = resource.get("content", "")
        source = resource.get("source", "")
        
        # 合并所有文本内容
        full_text = f"{title} {content} {source}"
        
        # 判断领域
        if any(keyword in full_text for keyword in ["三角函数", "正弦函数", "余弦函数", "正切函数", "诱导公式", "三角"]):
            return "三角函数"
        elif any(keyword in full_text for keyword in ["指数函数", "对数函数", "幂函数"]):
            return "具体函数"
        elif any(keyword in full_text for keyword in ["函数的基本性质", "函数的性质", "单调性", "奇偶性", "周期性", "函数的概念", "函数概念"]) and "三角" not in full_text:
            return "一般函数"
        else:
            return "其他"
