from .._shared import *


class _ParseTeachingInspirationElementsMixin:
    def _parse_teaching_inspiration_elements(self, teaching_inspiration: str) -> List[str]:
        """
        智能解析教学启发，提取多个独立维度
        
        Args:
            teaching_inspiration: 教学启发文本
        
        Returns:
            教学启发要素列表
        """
        if not teaching_inspiration:
            return []
        
        elements = []
        
        # 尝试多种分隔符
        separators = ['，', '。', '；', ';', '；', '、', '，', '\n']
        
        # 首先尝试按分隔符分割
        for sep in separators:
            if sep in teaching_inspiration:
                parts = teaching_inspiration.split(sep)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 2:  # 过滤掉太短的片段
                        elements.append(part)
                if len(elements) >= 2:
                    break
        
        # 如果没有找到合适的分隔符，尝试按动词短语分割
        if len(elements) < 2:
            import re
            verb_patterns = [
                r'(设置|设计|创设|提供|引导|鼓励|通过|帮助|优化|简化|分步|建立|明确|培养|激发|增强|促进|搭建|搭建|组织|实现|体现|利用|运用|采用|采用|结合|整合|融合|融合)',
                r'(问题情境|学习情境|教学情境|真实情境|探究任务|学习任务|教学任务|学习活动|教学活动|小组活动|合作活动|探究活动|实践活动|应用活动)',
                r'(脚手架|认知支持|学习支持|教学支持|反馈机制|评价机制|合作机制|学习机制|教学机制)',
                r'(学习兴趣|学习动机|内在动机|外部动机|学习成就感|学习体验|学习效果|学习效率|学习质量)',
                r'(知识体系|知识网络|知识结构|知识框架|知识体系|知识建构|意义建构|认知建构)',
                r'(学习策略|学习方法|学习过程|学习活动|学习行为|学习习惯|学习态度|学习价值观)'
            ]
            
            for pattern in verb_patterns:
                matches = re.findall(pattern, teaching_inspiration)
                if matches:
                    for match in matches:
                        if match not in elements:
                            elements.append(match)
                    if len(elements) >= 2:
                        break
        
        # 如果还是没有足够的要素，尝试按句子分割
        if len(elements) < 2:
            import re
            sentences = re.split(r'[。！？]', teaching_inspiration)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 4:
                    elements.append(sentence)
        
        # 去重并保持顺序
        seen = set()
        unique_elements = []
        for element in elements:
            if element not in seen:
                seen.add(element)
                unique_elements.append(element)
        
        return unique_elements
