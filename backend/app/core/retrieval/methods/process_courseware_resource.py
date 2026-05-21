from .._shared import *
import re


class _ProcessCoursewareResourceMixin:
    def _process_courseware_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理课件资源 - 充分利用三个核心字段
        """
        content = metadata.get('内容', '')
        filename = metadata.get('文件名', '')
        teaching_use = metadata.get('教学用途', '')
        
        resource['title'] = self._generate_smart_title(filename, teaching_use, metadata)
        resource['content'] = self._build_structured_display(content, teaching_use, metadata)
        resource['filename'] = filename
        
        resource.update({
            'teaching_use': teaching_use,
            'knowledge_tags': metadata.get('知识点', '') or metadata.get('知识点标签', ''),
            'chapter': metadata.get('章节', ''),
            'grade': metadata.get('年级', ''),
            'has_interactive': self._detect_interactive_elements(content),
            'structure_quality': self._assess_structure_quality(content),
            'summary': self._generate_brief_summary(filename, teaching_use, content),
        })
    
    def _generate_smart_title(self, filename: str, teaching_use: str, metadata: Dict) -> str:
        """生成智能标题"""
        parts = []
        
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        if knowledge_tags:
            parts.append(knowledge_tags)
        
        if teaching_use:
            use_tag = self._map_to_short_tag(teaching_use)
            parts.append(f"[{use_tag}]")
        
        if filename and not knowledge_tags:
            clean_name = re.sub(r'\.(pptx?|pdf)$', '', filename, flags=re.IGNORECASE)
            parts.append(clean_name)
        
        return ' '.join(parts) if parts else (filename or '未命名课件')
    
    def _build_structured_display(self, content: str, teaching_use: str, metadata: Dict) -> str:
        """构建结构化展示内容"""
        sections = []
        
        info_lines = []
        if teaching_use:
            info_lines.append(f"🎯 教学用途：{teaching_use}")
        
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        if knowledge_tags:
            info_lines.append(f"📚 知识点：{knowledge_tags}")
        
        chapter = metadata.get('章节', '')
        if chapter:
            info_lines.append(f"📖 章节：{chapter}")
        
        grade = metadata.get('年级', '')
        if grade:
            info_lines.append(f"🎓 年级：{grade}")
        
        if info_lines:
            sections.append('\n'.join(info_lines))
        
        features = []
        if self._detect_interactive_elements(content):
            features.append("✨ 含动态交互")
        
        quality = self._assess_structure_quality(content)
        if quality == 'high':
            features.append("📋 结构完整")
        elif quality == 'medium':
            features.append("📝 内容较完整")
        
        if features:
            sections.append(' | '.join(features))
        
        if content:
            summary = content[:300].strip()
            if len(content) > 300:
                summary += "..."
            sections.append(f"\n📄 内容预览：\n{summary}")
        
        return '\n\n'.join(sections)
    
    def _map_to_short_tag(self, teaching_use: str) -> str:
        """映射为简短标签"""
        mapping = {
            '练习课课件': '练习',
            '复习课课件': '复习',
            '新授课课件': '新授',
            '习题课课件': '习题',
        }
        
        for key, tag in mapping.items():
            if key in teaching_use:
                return tag
        
        if '练习' in teaching_use:
            return '练习'
        elif '复习' in teaching_use:
            return '复习'
        elif '新授' in teaching_use or '新课' in teaching_use:
            return '新授'
        
        return teaching_use[:4]
    
    def _detect_interactive_elements(self, content: str) -> bool:
        """检测交互元素"""
        keywords = ['GGB', 'GeoGebra', '几何画板', '动态', '交互', '拖动', '动画']
        return any(kw in content for kw in keywords)
    
    def _assess_structure_quality(self, content: str) -> str:
        """评估结构质量"""
        if not content:
            return 'low'
        
        sections = ['导入', '讲解', '例题', '练习', '总结']
        matched = sum(1 for s in sections if s in content)
        
        if matched >= 4:
            return 'high'
        elif matched >= 2:
            return 'medium'
        return 'low'
    
    def _generate_brief_summary(self, filename: str, teaching_use: str, content: str) -> str:
        """生成简短摘要"""
        parts = []
        
        if teaching_use:
            parts.append(self._map_to_short_tag(teaching_use))
        
        if content:
            brief = content[:50].strip().replace('\n', ' ')
            if len(content) > 50:
                brief += '...'
            parts.append(brief)
        else:
            parts.append(filename)
        
        return ' | '.join(parts)
