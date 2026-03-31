"""
兼容入口。
"""

from .query.service import FuzzyMatcher, QueryPreprocessor, get_query_preprocessor

__all__ = ['FuzzyMatcher', 'QueryPreprocessor', 'get_query_preprocessor']
