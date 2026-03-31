"""
查询智能预处理模块

职责：
- 清洗和标准化用户查询
- 提取关键词和核心概念
- 处理LaTeX数学公式
- 支持模糊匹配
- 生成多种检索策略的查询文本
- 查询分类（概念型、方法型、资源型、问题型、混合型）
- 查询明确度计算
"""

import re
from typing import List, Dict, Any, Set
import logging
from ...config.resource_type_config import (
    get_all_user_types,
    get_standard_name,
    normalize_resource_types
)

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """模糊匹配器"""
    
    def __init__(self):
        """初始化模糊匹配器"""
        # 常见拼写错误映射
        self.typo_map = {
            "函书": "函数",
            "方程试": "方程式",
            "不等试": "不等式",
            "指树": "指数",
            "对树": "对数",
            "倒树": "导数",
            "积份": "积分",
            "极现": "极限",
            "三角函书": "三角函数",
            "二次函书": "二次函数",
            "园": "圆",
            "三交形": "三角形",
            "平形": "平行",
            "垂值": "垂直",
            "相试": "相似",
            "全登": "全等",
            "概律": "概率",
            "统记": "统计"
        }
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        计算Levenshtein编辑距离
        
        Args:
            s1: 字符串1
            s2: 字符串2
            
        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def correct_typos(self, text: str) -> str:
        """
        纠正常见拼写错误
        
        Args:
            text: 输入文本
            
        Returns:
            纠正后的文本
        """
        corrected = text
        for typo, correct in self.typo_map.items():
            corrected = corrected.replace(typo, correct)
        return corrected
    
    def fuzzy_match_keywords(self, query: str, keywords: List[str], max_distance: int = 2) -> List[str]:
        """
        模糊匹配关键词
        
        Args:
            query: 查询文本
            keywords: 关键词列表
            max_distance: 最大编辑距离
            
        Returns:
            匹配的关键词列表
        """
        matches = []
        
        for keyword in keywords:
            if keyword in query:
                if keyword not in matches:
                    matches.append(keyword)
                continue
            
            if len(keyword) >= 3:
                query_words = re.findall(r'[\w\u4e00-\u9fff]+', query)
                for q_word in query_words:
                    if len(q_word) >= 2:
                        distance = self.levenshtein_distance(q_word, keyword)
                        if distance <= max_distance and distance < len(keyword):
                            if keyword not in matches:
                                matches.append(keyword)
                                logger.debug(f"模糊匹配: {q_word} -> {keyword} (距离: {distance})")
        
        return matches


