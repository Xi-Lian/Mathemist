#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

with open('../knowledge_graph.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

print("知识图谱中的所有节点:")
for i, node in enumerate(kg['nodes']):
    keywords = node.get('keywords', [])[:3]
    print("%d. %s (keywords: %s)" % (i+1, node['label'], keywords))

print("\n总计: %d 个节点" % len(kg['nodes']))

print("\n\n与'三角'相关的节点:")
for node in kg['nodes']:
    if '三角' in node['label']:
        print("  - %s" % node['label'])

print("\n与'恒等'相关的节点:")
for node in kg['nodes']:
    if '恒等' in node['label']:
        print("  - %s" % node['label'])

print("\n与'函数'相关的节点:")
count = 0
for node in kg['nodes']:
    if '函数' in node['label']:
        print("  - %s" % node['label'])
        count += 1
        if count >= 10:
            print("  ... (更多)")
            break