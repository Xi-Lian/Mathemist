#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

with open('knowledge_graph.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

nodes = kg.get('nodes', [])
for node in nodes:
    name = node.get('label', '')
    if '三角恒等' in name:
        print(f"节点: {name}")
        print(f"keywords: {node.get('keywords', [])}")
        print(f"id: {node.get('id', '')}")
        break
else:
    print("未找到三角恒等变换节点")
