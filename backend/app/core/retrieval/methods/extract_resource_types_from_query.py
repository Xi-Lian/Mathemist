from .._shared import *


class _ExtractResourceTypesFromQueryMixin:
    def _extract_resource_types_from_query(self, query: str) -> List[str]:
        """
        V61.0改进：从查询中自动识别资源类型
        
        Args:
            query: 用户查询
        
        Returns:
            资源类型列表
        """
        resource_types = []
        resource_type_keywords = {
            "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"],
            "教学大纲": ["教学大纲", "大纲", "课程标准", "教学要求"],
            "课件": ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"],
            "课例": ["课例", "教学视频", "课堂实录", "视频", "教学案例", "课堂案例", "讲解", "示范课", "公开课", "观摩课"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "几何画板"],
            "习题": ["习题", "题目", "练习题", "练习", "试题", "测试题", "计算题", "应用题", "填空题", "选择题", "解答题", "证明题", "分层练习", "简单练习", "专项练习", "综合题", "拓展题"],
            "资料": ["资料", "资源", "教学资源", "教学资料", "参考资料"]
        }
        
        for resource_type, keywords in resource_type_keywords.items():
            if any(kw in query for kw in keywords):
                resource_types.append(resource_type)
        
        # 确保至少返回一个资源类型
        if not resource_types:
            resource_types.append("资料")
        
        return list(set(resource_types))
