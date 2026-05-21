import re

class _ExtractCoreThemeMixin:
    @staticmethod
    def _normalize_theme(theme: str) -> str:
        """
        规范化主题，去除过于具体的修饰词，返回更通用的主题
        """
        if not theme:
            return theme
        
        # 去除常见的过于具体的后缀（按长度从长到短排序）
        suffixes_to_remove = [
            "的单调性", "的奇偶性", "的周期性", "的对称性", "的零点",
            "公式", "定理", "法则", "性质", "定义", "概念", "应用", "运算", "计算"
        ]
        
        for suffix in suffixes_to_remove:
            if theme.endswith(suffix):
                theme = theme[:-len(suffix)].strip()
                # 递归检查，可能有多个后缀需要去除
                theme = _ExtractCoreThemeMixin._normalize_theme(theme)
                break
        
        # 去除末尾的"的"字（处理"组合数的性质"-> "组合数的" -> "组合数"）
        if theme.endswith("的"):
            theme = theme[:-1].strip()
        
        # 去除常见的过于具体的前缀
        prefixes_to_remove = ["的", "与", "和", "及"]
        for prefix in prefixes_to_remove:
            if theme.startswith(prefix):
                theme = theme[len(prefix):].strip()
                # 递归检查，可能有多个前缀需要去除
                theme = _ExtractCoreThemeMixin._normalize_theme(theme)
                break
        
        return theme

# 测试主题规范化
print("测试主题规范化函数：")
print("=" * 60)

test_cases = [
    ("组合数公式", "组合数"),
    ("组合数的性质", "组合数"),
    ("函数的单调性", "函数"),
    ("三角函数公式", "三角函数"),
    ("概率的定义", "概率"),
    ("立体几何概念", "立体几何"),
    ("复数运算", "复数"),
    ("指数函数性质", "指数函数"),
    ("对数函数定义", "对数函数"),
    ("排列组合公式", "排列组合"),
    ("函数的奇偶性", "函数"),
    ("函数的周期性", "函数"),
]

passed = 0
failed = 0

for input_theme, expected in test_cases:
    result = _ExtractCoreThemeMixin._normalize_theme(input_theme)
    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] '{input_theme}' -> '{result}' (期望: '{expected}')")
    if result == expected:
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 60)
print(f"测试结果: {passed} 个通过, {failed} 个失败")
