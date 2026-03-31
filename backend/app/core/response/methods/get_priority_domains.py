from .._shared import *


class _GetPriorityDomainsMixin:
    def _get_priority_domains(self, query: str) -> List[str]:
        """
        根据用户查询确定优先领域
        
        Args:
            query: 用户查询
            
        Returns:
            优先领域列表
        """
        if not query:
            return []
        
        query_lower = query.lower()
        priority_domains = []
        
        # 主题到领域的映射
        theme_domain_map = {
            "函数的概念": "一般函数",
            "函数的表示法": "一般函数",
            "函数的性质": "一般函数",
            "单调性": "一般函数",
            "奇偶性": "一般函数",
            "周期性": "一般函数",
            "指数函数": "具体函数",
            "对数函数": "具体函数",
            "幂函数": "具体函数",
            "三角函数": "三角函数",
            "正弦函数": "三角函数",
            "余弦函数": "三角函数",
            "正切函数": "三角函数",
        }
        
        # 检查查询中包含的主题
        for theme, domain in theme_domain_map.items():
            if theme in query_lower:
                if domain not in priority_domains:
                    priority_domains.append(domain)
        
        # 特殊处理：检查具体函数的概念
        if "指数函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "对数函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "幂函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "三角函数" in query_lower:
            if "三角函数" not in priority_domains:
                priority_domains.append("三角函数")
        elif "函数" in query_lower:
            if "一般函数" not in priority_domains:
                priority_domains.append("一般函数")
        
        return priority_domains
