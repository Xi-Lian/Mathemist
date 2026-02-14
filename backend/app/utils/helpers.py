"""
辅助函数模块

职责：
- 提供通用的辅助函数
- ID生成
- 数据验证
- 格式化工具

依赖：
- 无外部依赖
"""

import uuid
import json
from typing import Any, Dict, List
from datetime import datetime


class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理不可序列化的对象"""
    
    def default(self, obj: Any) -> Any:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


def generate_id() -> str:
    """
    生成唯一ID
    
    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """
    获取当前时间戳（ISO格式）
    
    Returns:
        ISO格式的时间戳字符串
    """
    return datetime.utcnow().isoformat()


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全地获取字典值
    
    Args:
        data: 字典对象
        key: 键名
        default: 默认值
    
    Returns:
        字典值或默认值
    """
    if data is None:
        return default
    return data.get(key, default)


def safe_str(value: Any, default: str = "") -> str:
    """
    安全地转换为字符串
    
    Args:
        value: 任意值
        default: 默认字符串
    
    Returns:
        字符串表示
    """
    if value is None:
        return default
    return str(value)


def is_empty(value: Any) -> bool:
    """
    检查值是否为空
    
    Args:
        value: 任意值
    
    Returns:
        是否为空
    """
    if value is None:
        return True
    if isinstance(value, (str, list, dict)):
        return len(value) == 0
    return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
    
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    格式化百分比
    
    Args:
        value: 小数值（0-1）
        decimals: 小数位数
    
    Returns:
        百分比字符串
    """
    return f"{value * 100:.{decimals}f}%"


def deduplicate_list(items: List[Any], key_func=None) -> List[Any]:
    """
    去重列表
    
    Args:
        items: 列表
        key_func: 键函数，用于提取比较键
    
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    
    for item in items:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def sort_by_key(items: List[Dict[str, Any]], key: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """
    根据键排序字典列表
    
    Args:
        items: 字典列表
        key: 排序键
        reverse: 是否降序
    
    Returns:
        排序后的列表
    """
    return sorted(items, key=lambda x: x.get(key, 0), reverse=reverse)


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典
    
    Args:
        *dicts: 多个字典
    
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否有效
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换不安全字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除首尾空格
    sanitized = sanitized.strip()
    # 限制长度
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
    
    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
