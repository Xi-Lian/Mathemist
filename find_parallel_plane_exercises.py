#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

analysis_dir = 'learning_resource/exercise_analysis'
parallel_plane_files = []

for filename in os.listdir(analysis_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(analysis_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if '面面平行' in content:
                    parallel_plane_files.append(filename)
        except:
            pass

print(f"找到 {len(parallel_plane_files)} 个包含'面面平行'的分析文件")
print("=" * 60)

for i, filename in enumerate(parallel_plane_files[:10], 1):
    filepath = os.path.join(analysis_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{i}. {filename}")
    print(f"   知识点: {data.get('知识点', [])}")
    print(f"   题型: {data.get('题型', '')}")
    print(f"   难度: {data.get('难度', '')}")
    question = data.get('题干', '')[:150]
    print(f"   题干预览: {question}...")

print("\n" + "=" * 60)
print("搜索完成")
