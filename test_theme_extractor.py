import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.methods.extract_theme_with_llm import _ExtractThemeWithLlmMixin
from app.config import ModelConfig

# 创建测试类
class TestThemeExtractor(_ExtractThemeWithLlmMixin):
    def __init__(self):
        self.model_config = ModelConfig()

# 测试
extractor = TestThemeExtractor()
print("=" * 80)
print("测试1: 查询'分段函数单调性的习题'")
print("=" * 80)
theme, board = extractor._extract_theme_with_llm(
    "分段函数单调性", 
    has_resource_type=True, 
    intent="", 
    is_exercise=True
)
print(f"主题: '{theme}'")
print(f"板块: '{board}'")
print()

print("=" * 80)
print("测试2: 查询'函数单调性的区间判断'")
print("=" * 80)
theme, board = extractor._extract_theme_with_llm(
    "函数单调性的区间判断", 
    has_resource_type=True, 
    intent="", 
    is_exercise=True
)
print(f"主题: '{theme}'")
print(f"板块: '{board}'")
