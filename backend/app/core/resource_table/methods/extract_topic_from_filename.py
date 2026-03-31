from .._shared import *


class _ExtractTopicFromFilenameMixin:
    def _extract_topic_from_filename(self, filename: str) -> str:
        """
        从课例文件名中提取知识点信息
        
        Args:
            filename: 文件名，如 "4.2.1指数函数的概念.mp4"
            
        Returns:
            提取的知识点信息
        """
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 移除常见的标记
        name = re.sub(r'【.*?】', '', name)  # 移除【单调性】等标记
        name = re.sub(r'\(.*?\)', '', name)  # 移除括号内容
        name = re.sub(r'\（.*?\）', '', name)  # 移除中文括号内容
        
        # 提取数字编号后的内容（如 "4.2.1指数函数的概念" -> "指数函数的概念"）
        match = re.search(r'^[\d\.]+\s*(.+)$', name)
        if match:
            return match.group(1).strip()
        
        # 如果没有数字编号，直接返回文件名
        return name
