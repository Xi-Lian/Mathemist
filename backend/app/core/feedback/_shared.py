"""
用户反馈系统

功能：
- 记录用户对资源的点赞/点踩反馈
- 记录详细的反馈原因
- 记录改进建议
- 提供反馈数据分析功能
- 提供反馈处理状态跟踪
- 提供反馈趋势分析
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 反馈数据存储路径
FEEDBACK_DATA_DIR = Path(__file__).parent.parent.parent / "data"
FEEDBACK_FILE = FEEDBACK_DATA_DIR / "user_feedback.json"


