"""
教案导出模块

职责：
- 将生成的教案导出为多种格式（Markdown、HTML、DOCX、PDF）
- 支持自定义导出模板
- 保持教案的格式和结构

依赖：
- markdown (Markdown处理)
- python-docx (Word文档生成)
- weasyprint (PDF生成，可选)
- pathlib (路径管理)
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import markdown
from ..config_manager import config_manager


