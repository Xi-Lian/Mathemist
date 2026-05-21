#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行测试并保存完整结果
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_improved_scenarios import test_improved_scenarios

# 保存标准输出
import io
from contextlib import redirect_stdout

# 运行测试并捕获输出
f = io.StringIO()
with redirect_stdout(f):
    test_improved_scenarios()

# 获取输出内容
output = f.getvalue()

# 保存到文件
with open('test_results.txt', 'w', encoding='utf-8') as file:
    file.write(output)

print("测试结果已保存到 test_results.txt")
print("\n前2000个字符预览:")
print(output[:2000])
