from .._shared import *


class _ProcessResourceContentMixin:
    def _process_resource_content(
        self, 
        category: str, 
        title: str, 
        content: str,
        scenario: str = "search"
    ) -> str:
        """
        处理资源内容
        
        Args:
            category: 资源分类
            title: 资源标题
            content: 原始内容
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景
        
        Returns:
            处理后的内容
        """
        # 习题资源特殊处理
        if category == "习题资源":
            if "【图片题目】" in content:
                # 图片题目，显示文件名
                return "【图片题目】请查看题目文件"
            else:
                # 文字题目，显示完整内容
                return content[:200] + "..." if len(content) > 200 else content
        
        # 课件、课例、GGB只显示文件名
        if category in ["课件资源", "课例资源", "GGB资源"]:
            return "（请查看文件）"
        
        # 教案和教学大纲，根据场景决定是否显示内容
        if category in ["教案资源", "教学大纲"]:
            # 资源检索场景：只显示文件名，不显示内容
            if scenario == "search":
                return "（请查看文件）"
            # 教案生成场景：返回完整内容
            else:
                return content
        
        # 其他资源，生成摘要
        return self.content_processor.generate_summary(content, max_length=150)
