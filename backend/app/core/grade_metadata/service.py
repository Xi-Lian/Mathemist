"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.extract_grade_from_query import _ExtractGradeFromQueryMixin
from .methods.infer_grade_from_path import _InferGradeFromPathMixin
from .methods.infer_grade_from_knowledge import _InferGradeFromKnowledgeMixin
from .methods.infer_grade_from_title import _InferGradeFromTitleMixin
from .methods.enrich_resource_grade import _EnrichResourceGradeMixin
from .methods.grade_to_level import _GradeToLevelMixin
from .methods.calculate_grade_match_score import _CalculateGradeMatchScoreMixin
from .methods.parse_query_grade import _ParseQueryGradeMixin
from .methods.get_grade_statistics import _GetGradeStatisticsMixin

class GradeMetadataEnricher(_InitMixin, _ExtractGradeFromQueryMixin, _InferGradeFromPathMixin, _InferGradeFromKnowledgeMixin, _InferGradeFromTitleMixin, _EnrichResourceGradeMixin, _GradeToLevelMixin, _CalculateGradeMatchScoreMixin, _ParseQueryGradeMixin, _GetGradeStatisticsMixin):
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


_grade_enricher = None

def get_grade_enricher() -> GradeMetadataEnricher:
    """获取年级元数据丰富器单例"""
    global _grade_enricher
    if _grade_enricher is None:
        _grade_enricher = GradeMetadataEnricher()
    return _grade_enricher
