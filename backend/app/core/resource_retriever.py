"""
兼容入口：资源检索模块

实际实现已迁移到 `app.core.retrieval.service`，保留此文件以兼容现有导入路径。
"""

from .retrieval.service import ResourceRetriever, retrieve_resources

__all__ = ["ResourceRetriever", "retrieve_resources"]
