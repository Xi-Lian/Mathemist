from .._shared import *


class _ProcessLessonCaseResourceMixin:
    def _process_lesson_case_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理课例资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        chapter = metadata.get('章节', '')
        filename = metadata.get('视频文件名/网址', '')
        analysis = metadata.get('分析', '')
        textbook = metadata.get('教材', '')
        course_name = metadata.get('课程名称', '')  # V45.2修复：获取课程名称
        
        # V45.2修复：构建标题，优先使用课程名称
        if course_name:
            resource['title'] = f"课例: {course_name}"
        elif chapter:
            resource['title'] = f"课例: {chapter}"
        else:
            resource['title'] = "课例资源"
        
        # 构建描述内容
        content_parts = []
        
        if textbook:
            content_parts.append(f"教材：{textbook}")
        
        if chapter:
            content_parts.append(f"章节：{chapter}")
        
        # 尝试从文件名中提取知识点信息
        if filename and not filename.startswith('http'):
            # 从文件名中提取关键信息
            topic_info = self._extract_topic_from_filename(filename)
            if topic_info:
                content_parts.append(f"知识点：{topic_info}")
        
        if analysis and analysis.strip():
            content_parts.append(f"分析：{analysis}")
        elif filename:
            # 如果分析为空，从文件名中提取关键信息
            content_parts.append(f"视频：{filename}")
        
        resource['content'] = "\n".join(content_parts)
        resource['filename'] = filename
        
        # V45.4修复：保存视频链接字段，供显示时使用
        resource['视频文件名/网址'] = filename
        resource['教材'] = textbook
        resource['课程名称'] = course_name
        resource['章节'] = chapter
        resource['分析'] = analysis
