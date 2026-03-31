"""
资源汇总表解析模块
用于解析learning_resource文件夹中的markdown表格数据

V12.0改进2：年级元数据体系重构
- 集成GradeMetadataEnricher自动推断年级信息

V54.0改进：动态关键词提取和资源格式化增强
- 添加通用关键词提取方法
- 增强教学大纲、课件、课例视频资源的搜索文本
- 动态从文件路径和内容中提取主题信息
"""

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# V12.0改进2：导入年级元数据丰富器
from ..grade_metadata_enricher import get_grade_enricher


