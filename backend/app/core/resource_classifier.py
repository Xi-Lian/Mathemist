"""
资源分类模块

职责：
- 根据文件路径和内容智能分类资源类型
- 提供关键词匹配和评分机制
- 支持多种资源类型的识别

依赖：
- 无外部依赖（纯逻辑模块）

支持的资源类型：
- lesson_plan: 教案资源
- syllabus: 教学大纲
- courseware: 课件资源
- lesson_case: 课例资源
- ggb: GGB动态数学资源
- visualization: 可视化资源
- exercise: 习题资源
- theory: 理论卡片资源
"""

from typing import Dict


class ResourceClassifier:
    """资源分类器"""
    
    # 关键词配置
    KEYWORDS = {
        "lesson_plan": [
            "教案", "教学设计", "导学案", "说课稿",
            "lesson", "teaching", "design"
        ],
        "syllabus": [
            "教学大纲", "syllabus", "课程标准", "课程大纲"
        ],
        "courseware": [
            "课件", "ppt", "pptx", "演示文稿", "slides",
            "courseware", "presentation"
        ],
        "lesson_case": [
            "课例", "课堂实录", "教学视频", "教学案例",
            "lesson case", "classroom", "video"
        ],
        "ggb": [
            "ggb", "geogebra", ".ggb", "动态数学",
            "geogebra"
        ],
        "visualization": [
            "可视化", "动态", "图象", "图像",
            "visualization", "dynamic", "graph", "plot"
        ],
        "exercise": [
            "习题", "练习", "题目", "答案", "试题",
            "exercise", "practice", "problem", "answer", "question"
        ]
    }
    
    @classmethod
    def classify(cls, source: str, content: str) -> str:
        """
        根据文件路径和内容智能分类资源
        
        Args:
            source: 文件路径
            content: 文件内容
        
        Returns:
            资源类型字符串
        """
        # 确保 source 和 content 不是 None
        if source is None:
            source = ""
        if content is None:
            content = ""
        
        source_lower = source.lower()
        content_lower = content.lower()
        
        # 优先识别理论卡片
        if cls._is_theory_card(content):
            return "theory"
        
        # 计算各类型的关键词匹配分数
        scores = cls._calculate_scores(source_lower, content_lower)
        
        # 返回得分最高的类型
        max_score = max(scores.values())
        
        if max_score == 0:
            return "theory"
        
        for resource_type, score in scores.items():
            if score == max_score and score > 0:
                return resource_type
        
        # 默认返回theory
        return "theory"
    
    @classmethod
    def _is_theory_card(cls, content: str) -> bool:
        """
        判断是否为理论卡片
        
        Args:
            content: 文件内容
        
        Returns:
            是否为理论卡片
        """
        theory_keywords = ["理论卡片", "核心观点", "教学启发"]
        return any(keyword in content for keyword in theory_keywords)
    
    @classmethod
    def _calculate_scores(cls, source_lower: str, content_lower: str) -> Dict[str, int]:
        """
        计算各资源类型的关键词匹配分数
        
        Args:
            source_lower: 小写的文件路径
            content_lower: 小写的文件内容
        
        Returns:
            各类型的分数字典
        """
        scores = {}
        
        for resource_type, keywords in cls.KEYWORDS.items():
            score = sum(
                1 for kw in keywords 
                if kw in source_lower or kw in content_lower
            )
            scores[resource_type] = score
        
        return scores
    
    @classmethod
    def get_all_types(cls) -> list:
        """
        获取所有支持的资源类型
        
        Returns:
            资源类型列表
        """
        return list(cls.KEYWORDS.keys()) + ["theory"]


# 向后兼容的函数接口
def classify_resource(source: str, content: str) -> str:
    """
    根据文件路径和内容智能分类资源（向后兼容接口）
    
    Args:
        source: 文件路径
        content: 文件内容
    
    Returns:
        资源类型字符串
    """
    return ResourceClassifier.classify(source, content)
