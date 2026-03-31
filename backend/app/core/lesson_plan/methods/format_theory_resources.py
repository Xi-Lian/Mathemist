from .._shared import *


class _FormatTheoryResourcesMixin:
    def _format_theory_resources(self, resources: List[Dict[str, Any]]) -> str:
        """
        格式化理论资源，提供清晰的理论信息
        
        Args:
            resources: 理论资源列表
        
        Returns:
            格式化后的文本
        """
        if not resources:
            return "暂无相关理论资源"
        
        formatted = []
        for i, resource in enumerate(resources, 1):
            title = resource.get("title", f"理论{i}")
            content = resource.get("content", "")
            source = resource.get("source", "")
            
            # 提取核心观点和教学启发
            core_view = self._extract_section(content, "核心观点")
            teaching_inspiration = self._extract_section(content, "教学启发")
            applicable_links = self._extract_section(content, "适用环节")
            application_case = self._extract_section(content, "应用案例")
            
            formatted.append(f"""
【理论卡片{i}】{title}

📌 核心观点：
{core_view if core_view else content}

💡 教学启发：
{teaching_inspiration if teaching_inspiration else "请根据理论核心观点提炼教学启发"}

🎯 适用环节：
{applicable_links if applicable_links else "适用于教学全过程"}

📖 应用案例：
{application_case if application_case else "请结合具体教学内容设计应用场景"}

---
""")
        
        return "\n".join(formatted)
