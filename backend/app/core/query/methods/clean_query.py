from .._shared import *


class _CleanQueryMixin:
    def _clean_query(self, query: str) -> str:
        """
        清洗查询文本
        """
        if not query:
            return ""
        
        cleaned = re.sub(r'\s+', ' ', query.strip())
        cleaned = re.sub(r'\$.*?\$', '', cleaned)
        cleaned = re.sub(r'\\\[.*?\\\]', '', cleaned)
        cleaned = re.sub(r'\\\(.*?\\\)', '', cleaned)
        cleaned = re.sub(r'[^\w\u4e00-\u9fff，。？！,.!?]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
