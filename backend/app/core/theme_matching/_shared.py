"""
主题匹配系统

职责：
- 建立主题-关键词映射库
- 多维度主题匹配
- 分级加分机制
- 冲突主题降权
- 匹配结果可视化
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re


