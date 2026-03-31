"""
兼容入口。
"""

from .grade_metadata.service import GradeMetadataEnricher, get_grade_enricher

__all__ = ['GradeMetadataEnricher', 'get_grade_enricher']
