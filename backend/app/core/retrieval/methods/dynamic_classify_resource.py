from .._shared import *


class _DynamicClassifyResourceMixin:
    def _dynamic_classify_resource(self, resource: Dict[str, Any], content: str, metadata: Dict[str, Any], query: str) -> Optional[str]:
        """
        动态分类资源
        V54.0改进：添加对教学大纲和课例视频的支持
        
        Args:
            resource: 资源对象
            content: 资源内容
            metadata: 资源元数据
            query: 用户查询
        
        Returns:
            动态分类结果
        """
        # 1. 基于内容的动态分类
        if '教案' in content or '教学目标' in content or '教学过程' in content:
            return 'lesson_plan'
        elif '教学大纲' in content or '教学任务' in content:
            return 'syllabus'
        elif '课例' in content or '课堂实录' in content or '教学视频' in content:
            return 'lesson_case'
        elif '习题' in content or '题目' in content or '练习' in content or '选择题' in content or '填空题' in content or '解答题' in content:
            return 'exercise'
        elif '课件' in content or 'PPT' in content or '幻灯片' in content:
            return 'courseware'
        elif 'GeoGebra' in content or 'ggb' in content.lower() or '几何画板' in content:
            return 'ggb'
        elif '可视化' in content or '图表' in content or '图像' in content:
            return 'visualization'
        
        # 2. 基于元数据的动态分类
        source_file = metadata.get('source_file', '')
        if '教学大纲' in source_file:
            return 'syllabus'
        elif '教案' in source_file:
            return 'lesson_plan'
        elif '课例' in source_file:
            return 'lesson_case'
        elif '习题' in source_file:
            return 'exercise'
        elif '课件' in source_file:
            return 'courseware'
        elif 'ggb' in source_file.lower():
            return 'ggb'
        
        # 3. 基于文件路径的分类
        file_path = metadata.get('file_path', '')
        if '教学大纲' in file_path:
            return 'syllabus'
        elif '习题' in file_path:
            return 'exercise'
        elif '教案' in file_path:
            return 'lesson_plan'
        elif '课例' in file_path:
            return 'lesson_case'
        elif '课件' in file_path:
            return 'courseware'
        
        # 3. 基于主题的动态分类
        title = metadata.get('title', '')
        detected_themes = self.theme_matcher.dynamic_theme_detection(content, title)
        if detected_themes:
            primary_theme = detected_themes[0]['theme']
            # 根据主题调整分类
            if '函数' in primary_theme:
                # 函数相关资源更可能是理论资源
                if '习题' not in content and '题目' not in content:
                    return 'theory_resources'
        
        # 4. 基于查询的动态分类
        if '教案' in query:
            if '教案' in content or '教学' in content:
                return 'lesson_plan_patterns'
        elif '教学大纲' in query:
            if '教学大纲' in content or '教学任务' in content:
                return 'syllabus_resources'
        elif '课例' in query or '教学视频' in query:
            if '课例' in content or '课堂实录' in content or '教学视频' in content:
                return 'lesson_case_resources'
        elif '习题' in query or '题目' in query or '选择题' in query or '填空题' in query or '解答题' in query or '证明题' in query or '练习题' in query:
            if '习题' in content or '题目' in content or '选择题' in content or '填空题' in content or '解答题' in content or '证明题' in content or '练习' in content:
                return 'exercise_resources'
        elif '课件' in query:
            if '课件' in content or 'PPT' in content:
                return 'courseware_resources'
        
        return None
