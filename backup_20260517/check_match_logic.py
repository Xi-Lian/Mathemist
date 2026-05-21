"""模拟方案A的匹配逻辑，验证哪些习题能匹配"""
import json
import os

# 加载知识图谱
kg_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')
with open(kg_path, 'r', encoding='utf-8') as f:
    kg_data = json.load(f)

nodes = kg_data.get('nodes', [])
node_id_index = {n['id']: n for n in nodes}
core_theme = '三角恒等变换'

# 找到匹配节点
matched_node_ids = set()
for node in nodes:
    label = node.get('label', '')
    if core_theme and (core_theme == label or core_theme in label):
        matched_node_ids.add(node['id'])
    for kw in node.get('keywords', []):
        if core_theme and (core_theme == kw or core_theme in kw):
            matched_node_ids.add(node['id'])
            break

# 收集扩展关键词
def collect_descendants(node_id, visited=None):
    if visited is None:
        visited = set()
    labels = set()
    keywords = set()
    for node in nodes:
        if node.get('parent') == node_id and node['id'] not in visited:
            visited.add(node['id'])
            labels.add(node.get('label', ''))
            for kw in node.get('keywords', []):
                keywords.add(kw)
            sub_l, sub_k = collect_descendants(node['id'], visited)
            labels.update(sub_l)
            keywords.update(sub_k)
    return labels, keywords

kg_keywords = set()
for nid in matched_node_ids:
    node = node_id_index.get(nid, {})
    kg_keywords.add(node.get('label', ''))
    for kw in node.get('keywords', []):
        kg_keywords.add(kw)
    desc_labels, desc_keywords = collect_descendants(nid)
    kg_keywords.update(desc_labels)
    kg_keywords.update(desc_keywords)

if core_theme:
    kg_keywords.add(core_theme)

print(f"kg_keywords count: {len(kg_keywords)}")
print(f"kg_keywords: {sorted(kg_keywords)}")
print()

# 模拟匹配
test_exercises = [
    ("5-5-1 #507", "正切二倍角;求值"),
    ("5-5-1 #508", "同角关系;正切二倍角;象限符号"),
    ("5-5-1 #509", "二倍角公式;三角函数值"),
    ("5-5-1 #510", "正弦二倍角;同角关系;参数范围"),
    ("5-5-1 #511", "正弦二倍角;单调区间"),
    ("5-5-1 #512", "余弦二倍角;求值"),
    ("5-5-1 #513", "诱导公式;正弦二倍角"),
    ("5-5-1 #514", "正切二倍角;差角公式"),
    ("5-5-1 #515", "正切二倍角;恒等证明"),
    ("5-5-1 #516", "三角形形状;二倍角;恒等变形"),
    ("5-5-1 #517", "二倍角;和角公式;同角关系;综合求值"),
    ("5-5-1 #518", "三角函数;二倍角;最值问题"),
    ("5-5-1 #519", "黄金分割;二倍角;化简求值"),
]

def _is_chinese_char(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF)

def _word_match(kp, kw):
    if kp == kw:
        return True
    if kp in kw:
        idx = kw.index(kp)
        kp_len = len(kp)
        at_start = (idx == 0)
        at_end = (idx + kp_len >= len(kw))
        if at_start or at_end:
            return True
        return not _is_chinese_char(kw[idx - 1])
    if kw in kp:
        idx = kp.index(kw)
        kw_len = len(kw)
        at_start = (idx == 0)
        at_end = (idx + kw_len >= len(kp))
        if at_start or at_end:
            return True
        return not _is_chinese_char(kp[idx - 1])
    return False

for name, kp_str in test_exercises:
    kp_list = [kp.strip() for kp in kp_str.replace("；", ";").split(";") if kp.strip()]
    has_match = False
    matched = []
    for kp in kp_list:
        for kw in kg_keywords:
            if _word_match(kp, kw):
                has_match = True
                matched.append(f"{kp}<->{kw}")
                break
        if has_match:
            break
    
    status = "MATCH" if has_match else "NO MATCH"
    print(f"{status} {name}: kp={kp_str}")
    if matched:
        print(f"       matched: {matched}")
