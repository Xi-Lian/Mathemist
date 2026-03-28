"""
年级元数据丰富器

V12.0改进2：年级元数据体系重构
根据文件路径、教材版本和知识点推断年级信息

问题背景：
- 习题资源没有直接的"年级"字段
- 需要根据文件路径（如"必修一第四章"）推断年级
- 不同地区教材版本可能有差异

解决方案：
- 建立教材章节到年级的映射表
- 支持多版本教材（人教A版、人教B版、北师大版等）
- 提供灵活的年级匹配算法
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GradeMetadataEnricher:
    """
    年级元数据丰富器
    
    根据资源文件路径和教材体系推断年级信息
    """
    
    # 教材版本标识
    TEXTBOOK_VERSIONS = {
        '人教A版': ['人教A版', '人教版', '必修一', '必修二', '选择性必修'],
        '人教B版': ['人教B版'],
        '北师大版': ['北师大版', '北京师范大学'],
        '苏教版': ['苏教版', '江苏教育'],
        '湘教版': ['湘教版', '湖南教育'],
    }
    
    # 人教A版教材章节到年级的映射（新教材2019版）
    # 高中数学新教材结构：
    # 必修第一册：高一上学期
    # 必修第二册：高一下学期
    # 选择性必修第一册：高二上学期
    # 选择性必修第二册：高二下学期
    # 选择性必修第三册：高三（部分学校高二下学期开始）
    CHAPTER_TO_GRADE_MAPPING = {
        # 必修第一册 - 高一上学期
        '必修一': {
            'grade': '高一上学期',
            'grade_level': 10,  # 数字表示，便于比较
            'chapters': {
                '第一章': ['集合', '常用逻辑用语'],
                '第二章': ['一元二次函数', '方程和不等式', '二次函数'],
                '第三章': ['函数的概念', '函数概念', '函数的性质'],
                '第四章': ['指数函数', '对数函数'],
                '第五章': ['三角函数'],
            }
        },
        # 必修第二册 - 高一下学期
        '必修二': {
            'grade': '高一下学期',
            'grade_level': 11,
            'chapters': {
                '第六章': ['平面向量'],
                '第七章': ['复数'],
                '第八章': ['立体几何'],
                '第九章': ['统计'],
                '第十章': ['概率'],
            }
        },
        # 选择性必修第一册 - 高二上学期
        '选择性必修一': {
            'grade': '高二上学期',
            'grade_level': 12,
            'chapters': {
                '第一章': ['空间向量', '立体几何'],
                '第二章': ['直线和圆的方程', '直线与圆'],
                '第三章': ['圆锥曲线', '椭圆', '双曲线', '抛物线'],
            }
        },
        # 选择性必修第二册 - 高二下学期
        '选择性必修二': {
            'grade': '高二下学期',
            'grade_level': 13,
            'chapters': {
                '第四章': ['数列', '等差数列', '等比数列'],
                '第五章': ['导数', '一元函数的导数'],
            }
        },
        # 选择性必修第三册 - 高三/高二下学期
        '选择性必修三': {
            'grade': '高三',
            'grade_level': 14,
            'chapters': {
                '第六章': ['计数原理', '排列组合'],
                '第七章': ['随机变量', '分布列'],
                '第八章': ['成对数据的统计分析'],
            }
        },
    }
    
    # 年级关键词映射
    GRADE_KEYWORDS = {
        '高一': ['高一', '高中一年级', '高中1年级', '十年级'],
        '高二': ['高二', '高中二年级', '高中2年级', '十一年级'],
        '高三': ['高三', '高中三年级', '高中3年级', '十二年级', '高考'],
        '高一上学期': ['高一上', '高一上学期', '高一年级上学期', '必修一'],
        '高一下学期': ['高一下', '高一下学期', '高一年级下学期', '必修二'],
        '高二上学期': ['高二上', '高二上学期', '高二年级上学期', '选择性必修一'],
        '高二下学期': ['高二下', '高二下学期', '高二年级下学期', '选择性必修二'],
    }
    
    # 知识点到年级的直接映射（用于跨年级知识点）
    KNOWLEDGE_TO_GRADE = {
        # 高一上学期
        '集合': '高一上学期',
        '常用逻辑用语': '高一上学期',
        '一元二次函数': '高一上学期',
        '方程和不等式': '高一上学期',
        '二次函数': '高一上学期',
        '函数的概念': '高一上学期',
        '函数概念': '高一上学期',
        '函数的性质': '高一上学期',
        '单调性': '高一上学期',
        '奇偶性': '高一上学期',
        '最值': '高一上学期',
        '指数函数': '高一上学期',
        '对数函数': '高一上学期',
        '三角函数': '高一上学期',
        
        # 高一下学期
        '平面向量': '高一下学期',
        '复数': '高一下学期',
        '立体几何': '高一下学期',
        '统计': '高一下学期',
        '概率': '高一下学期',
        
        # 高二上学期
        '空间向量': '高二上学期',
        '直线和圆的方程': '高二上学期',
        '直线与圆': '高二上学期',
        '圆锥曲线': '高二上学期',
        '椭圆': '高二上学期',
        '双曲线': '高二上学期',
        '抛物线': '高二上学期',
        
        # 高二下学期
        '数列': '高二下学期',
        '等差数列': '高二下学期',
        '等比数列': '高二下学期',
        '导数': '高二下学期',
        
        # 高三
        '计数原理': '高三',
        '排列组合': '高三',
        '随机变量': '高三',
        '分布列': '高三',
        '二项式定理': '高三',
    }
    
    def __init__(self):
        """初始化年级元数据丰富器"""
        logger.info("初始化年级元数据丰富器")
    
    def extract_grade_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        从查询中提取年级信息
        
        Args:
            query: 用户查询
            
        Returns:
            年级信息字典，包含grade、grade_level等字段
        """
        if not query:
            return None
        
        query_lower = query.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'query',
                        'confidence': 0.8
                    }
        
        # 检查教材册别
        for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
            if book_key.lower() in query_lower:
                return {
                    'grade': book_info['grade'],
                    'grade_level': book_info['grade_level'],
                    'textbook_volume': book_key,
                    'inference_source': 'query',
                    'confidence': 0.9
                }
        
        return None
    
    def infer_grade_from_path(self, source_file: str) -> Optional[Dict[str, Any]]:
        """
        从文件路径推断年级信息
        
        Args:
            source_file: 资源文件路径（相对于learning_resource）
            
        Returns:
            年级信息字典，包含grade、grade_level等字段
        """
        if not source_file:
            return None
        
        # 标准化路径分隔符
        source_file = source_file.replace('/', '\\')
        path_lower = source_file.lower()
        
        # 1. 检查教材册别标识 - 按长度降序排序，优先匹配更长的名称
        sorted_book_keys = sorted(
            self.CHAPTER_TO_GRADE_MAPPING.keys(), 
            key=len, 
            reverse=True
        )
        
        for book_key in sorted_book_keys:
            book_key_lower = book_key.lower()
            # 检查是否在路径中出现，并且是完整的路径段
            if book_key_lower in path_lower:
                # 检查是否是完整的路径段
                # 查找book_key在路径中的所有位置
                positions = []
                start_pos = 0
                while True:
                    pos = path_lower.find(book_key_lower, start_pos)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start_pos = pos + 1
                
                # 检查每个位置是否是完整的路径段
                for pos in positions:
                    # 检查前后是否是路径分隔符或字符串边界
                    # 前边界：开始位置或路径分隔符/空格
                    has_front_boundary = pos == 0 or path_lower[pos-1] in ['\\', '/'] or path_lower[pos-1].isspace()
                    
                    # 后边界：结束位置或路径分隔符/空格/中文数字（如"第一"）
                    end_pos = pos + len(book_key_lower)
                    has_back_boundary = end_pos == len(path_lower) or \
                        path_lower[end_pos] in ['\\', '/', '.', ' '] or \
                        (end_pos < len(path_lower) and path_lower[end_pos] in ['第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'])
                    
                    is_boundary = has_front_boundary and has_back_boundary
                    
                    if is_boundary:
                        book_info = self.CHAPTER_TO_GRADE_MAPPING[book_key]
                        return {
                            'grade': book_info['grade'],
                            'grade_level': book_info['grade_level'],
                            'textbook_volume': book_key,
                            'inference_source': 'file_path',
                            'confidence': 0.9
                        }
        
        # 2. 检查章节号（如"第四章"、"4.1"）
        chapter_pattern = r'[第]?([一二三四五六七八九十1234567890]+)[章课节]'
        chapter_match = re.search(chapter_pattern, source_file)
        
        if chapter_match:
            chapter_num = chapter_match.group(1)
            # 尝试匹配各册的章节
            for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
                for chap_key in book_info['chapters'].keys():
                    if chapter_num in chap_key or chap_key in chapter_num:
                        return {
                            'grade': book_info['grade'],
                            'grade_level': book_info['grade_level'],
                            'textbook_volume': book_key,
                            'chapter': chap_key,
                            'inference_source': 'chapter_number',
                            'confidence': 0.8
                        }
        
        # 3. 特殊处理：检查路径中是否包含年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in path_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'path_keyword',
                        'confidence': 0.75
                    }
        
        return None
    
    def infer_grade_from_knowledge(self, knowledge_tags: str) -> Optional[Dict[str, Any]]:
        """
        从知识点标签推断年级信息
        
        Args:
            knowledge_tags: 知识点标签字符串（分号分隔）
            
        Returns:
            年级信息字典
        """
        if not knowledge_tags:
            return None
        
        tags = [tag.strip() for tag in knowledge_tags.split(';')]
        
        # 统计各年级出现的次数
        grade_counts = {}
        for tag in tags:
            for knowledge, grade in self.KNOWLEDGE_TO_GRADE.items():
                if knowledge in tag:
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        if grade_counts:
            # 选择出现次数最多的年级
            best_grade = max(grade_counts.keys(), key=lambda g: grade_counts[g])
            grade_level = self._grade_to_level(best_grade)
            
            return {
                'grade': best_grade,
                'grade_level': grade_level,
                'inference_source': 'knowledge_tags',
                'confidence': min(0.7 + 0.1 * grade_counts[best_grade], 0.9)
            }
        
        return None
    
    def infer_grade_from_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        从标题推断年级信息
        
        Args:
            title: 资源标题
            
        Returns:
            年级信息字典
        """
        if not title:
            return None
        
        title_lower = title.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'title',
                        'confidence': 0.75
                    }
        
        return None
    
    def enrich_resource_grade(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        为资源添加年级元数据
        
        Args:
            resource: 资源字典
            
        Returns:
            添加了年级信息的资源字典
        """
        resource_type = resource.get('resource_type', '')
        
        # 尝试多种方式推断年级
        grade_info = None
        confidence = 0
        
        # 1. 从文件路径推断（置信度最高）
        source_file = resource.get('source_file', '')
        if source_file:
            grade_info = self.infer_grade_from_path(source_file)
            if grade_info:
                confidence = grade_info.get('confidence', 0)
        
        # 2. 从知识点标签推断（如果路径推断置信度不够）
        if confidence < 0.8:
            knowledge_tags = resource.get('知识点标签', '')
            knowledge_grade = self.infer_grade_from_knowledge(knowledge_tags)
            if knowledge_grade and knowledge_grade.get('confidence', 0) > confidence:
                grade_info = knowledge_grade
                confidence = knowledge_grade['confidence']
        
        # 3. 从标题推断（最后尝试）
        if confidence < 0.7:
            title = resource.get('title', '')
            title_grade = self.infer_grade_from_title(title)
            if title_grade and title_grade.get('confidence', 0) > confidence:
                grade_info = title_grade
                confidence = title_grade['confidence']
        
        # 添加年级信息到资源
        if grade_info:
            resource['grade'] = grade_info['grade']
            resource['grade_level'] = grade_info['grade_level']
            resource['grade_inference_source'] = grade_info['inference_source']
            resource['grade_confidence'] = confidence
        else:
            # 默认设置
            resource['grade'] = '未知'
            resource['grade_level'] = 0
            resource['grade_inference_source'] = 'none'
            resource['grade_confidence'] = 0
        
        return resource
    
    def _grade_to_level(self, grade: str) -> int:
        """
        将年级字符串转换为数字级别
        
        Args:
            grade: 年级字符串（如"高一上学期"）
            
        Returns:
            数字级别（便于比较）
        """
        grade_map = {
            '高一上学期': 10,
            '高一下学期': 11,
            '高二上学期': 12,
            '高二下学期': 13,
            '高三': 14,
            '高一': 10,
            '高二': 12,
            '高三': 14,
        }
        return grade_map.get(grade, 0)
    
    def calculate_grade_match_score(
        self, 
        resource_grade_level: int, 
        query_grade: str,
        tolerance: int = 1
    ) -> float:
        """
        计算年级匹配得分
        
        Args:
            resource_grade_level: 资源的年级级别
            query_grade: 查询中的年级要求
            tolerance: 允许的年级差距（默认1个学期）
            
        Returns:
            匹配得分 (0-1)
        """
        # 解析查询中的年级
        query_level = self._parse_query_grade(query_grade)
        
        if query_level == 0:
            # 查询中没有明确的年级要求，返回中性分数
            return 0.5
        
        if resource_grade_level == 0:
            # 资源没有年级信息，返回较低分数
            return 0.3
        
        # 计算年级差距
        diff = abs(resource_grade_level - query_level)
        
        if diff == 0:
            return 1.0
        elif diff <= tolerance:
            return 0.8 - (diff - 1) * 0.2
        elif diff <= tolerance + 1:
            return 0.5
        else:
            return 0.0
    
    def _parse_query_grade(self, query_grade: str) -> int:
        """
        解析查询中的年级要求
        
        Args:
            query_grade: 年级字符串
            
        Returns:
            年级级别
        """
        if not query_grade:
            return 0
        
        query_lower = query_grade.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return self._grade_to_level(grade_key)
        
        # 检查教材册别
        for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
            if book_key.lower() in query_lower:
                return book_info['grade_level']
        
        return 0
    
    def get_grade_statistics(self, resources: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计资源列表中的年级分布
        
        Args:
            resources: 资源列表
            
        Returns:
            年级分布统计
        """
        stats = {}
        for resource in resources:
            grade = resource.get('grade', '未知')
            stats[grade] = stats.get(grade, 0) + 1
        return stats


# 全局单例实例
_grade_enricher = None


def get_grade_enricher() -> GradeMetadataEnricher:
    """获取年级元数据丰富器单例"""
    global _grade_enricher
    if _grade_enricher is None:
        _grade_enricher = GradeMetadataEnricher()
    return _grade_enricher