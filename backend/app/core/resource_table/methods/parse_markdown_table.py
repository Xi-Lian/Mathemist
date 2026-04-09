from .._shared import *


class _ParseMarkdownTableMixin:
    def _parse_structured_exercise_markdown(self, content: str) -> List[Dict[str, str]]:
        """
        解析按“第 N 题 / 题干 / 解析”组织的习题 Markdown。
        """
        normalized = content.replace('\r\n', '\n').replace('\r', '\n').strip()
        if '### 题干' not in normalized or '### 解析' not in normalized:
            return []

        blocks = re.split(r'(?m)^##\s*第\s*\d+\s*题\s*$', normalized)
        if len(blocks) <= 1:
            return []

        exercises: List[Dict[str, str]] = []
        for block in blocks[1:]:
            block = block.strip()
            if not block:
                continue

            meta_match = re.search(
                r'\*\*题型\*\*：(?P<question_type>.*?)\s*'
                r'\*\*难度\*\*：(?P<difficulty>.*?)\s*'
                r'\*\*知识点\*\*：(?P<knowledge>.*?)\s*'
                r'\*\*适用场景\*\*：(?P<scene>.*?)(?:\n|$)',
                block,
                re.S,
            )
            question_match = re.search(r'###\s*题干\s*\n(?P<question>.*?)\n###\s*解析\s*\n', block, re.S)
            answer_match = re.search(r'###\s*解析\s*\n(?P<answer>.*)$', block, re.S)

            if not question_match:
                continue

            difficulty_text = meta_match.group('difficulty').strip() if meta_match else ''
            difficulty_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*5', difficulty_text)
            difficulty_value = difficulty_match.group(1) if difficulty_match else difficulty_text

            exercises.append({
                '题目类型': meta_match.group('question_type').strip() if meta_match else '',
                '题干': question_match.group('question').strip(),
                '难度（1-5）': difficulty_value,
                '知识点标签': meta_match.group('knowledge').strip() if meta_match else '',
                '解析': answer_match.group('answer').strip() if answer_match else '',
                '适用场景': meta_match.group('scene').strip() if meta_match else '',
                '题目文件名': '',
            })

        return exercises

    def parse_markdown_table(self, content: str) -> List[Dict[str, str]]:
        """
        解析markdown表格内容
        
        Args:
            content: markdown文件内容
            
        Returns:
            解析后的表格数据，每行是一个字典
        """
        structured_exercises = self._parse_structured_exercise_markdown(content)
        if structured_exercises:
            return structured_exercises

        lines = content.strip().split('\n')
        
        # 检查是否是特殊表格格式（使用+和-符号）
        if '+:' in content or '+---' in content:
            return self._parse_special_table(lines)
        
        # 标准markdown表格格式
        return self._parse_standard_table(lines)
