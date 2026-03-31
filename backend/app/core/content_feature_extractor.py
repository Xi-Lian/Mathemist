"""
兼容入口。
"""

from .content_features.service import SubjectiveIntentInterpreter, ContentFeatureExtractor, get_content_feature_extractor

__all__ = ['SubjectiveIntentInterpreter', 'ContentFeatureExtractor', 'get_content_feature_extractor']
