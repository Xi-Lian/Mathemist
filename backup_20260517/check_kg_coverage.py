"""
通用性检查 v2：找出每个知识图谱节点的关键词缺口
"""
import json, os, re

# 1. ChromaDB 提取习题标签
print("提取 ChromaDB 数据...")
import chromadb
chroma_path = os.path.join(os.path.dirname(__file__), 'backend', 'chroma_db')
client = chromadb.PersistentClient(path=chroma_path)

all_tags = set()  # (kp, title) pairs
for col in client.list_collections():
    results = col.get(include=['metadatas'])
    for meta in results['metadatas']:
        kp_str = meta.get('知识点', '') or meta.get('知识点标签', '') or ''
        title = meta.get('title', '')
        for kp in kp_str.replace('；', ';').split(';'):
            kp = kp.strip()
            if kp:
                all_tags.add(kp)

# 标签到标题的映射
tag_titles = {}
for col in client.list_collections():
    results = col.get(include=['metadatas'])
    for meta in results['metadatas']:
        kp_str = meta.get('知识点', '') or meta.get('知识点标签', '') or ''
        title = meta.get('title', '')
        for kp in kp_str.replace('；', ';').split(';'):
            kp = kp.strip()
            if kp and kp not in tag_titles:
                tag_titles[kp] = title

print(f"共 {len(all_tags)} 条不重复标签")

# 2. 知识图谱
kg_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')
with open(kg_path, 'r', encoding='utf-8') as f:
    kg_data = json.load(f)
nodes = kg_data['nodes']
node_id_index = {n['id']: n for n in nodes}

# 收集后代
def collect_desc(nid, visited=None):
    if visited is None: visited = set()
    kws = set()
    for n in nodes:
        if n.get('parent') == nid and n['id'] not in visited:
            visited.add(n['id'])
            kws.add(n.get('label', ''))
            kws.update(n.get('keywords', []))
            kws.update(collect_desc(n['id'], visited))
    return kws

# 3. 匹配函数
def _word_match(kp, kw):
    if kp == kw: return True
    if kp and kw.startswith(kp) and len(kp) >= 3: return True
    if kw and kp.startswith(kw): return True
    return False

# 4. 分析：对每个知识图谱节点，找出能匹配到的标签
node_analysis = []
for node in nodes:
    nid = node['id']
    label = node.get('label', '')
    own_kws = set(node.get('keywords', []))
    own_kws.add(label)
    desc_kws = collect_desc(nid)
    all_kws = own_kws | desc_kws
    
    matched_tags = []
    for kp in all_tags:
        for kw in all_kws:
            if _word_match(kp, kw):
                matched_tags.append(kp)
                break
    
    # 找出无法匹配的标签（在该节点的章节范围内）
    # 通过标题前缀推断
    m = re.match(r'^(\d+-\d+)', label)
    unmatched_in_scope = []
    if m:
        prefix = m.group(1)
        for kp in all_tags:
            title = tag_titles.get(kp, '')
            if title.startswith(prefix):
                can_match = False
                for kw in all_kws:
                    if _word_match(kp, kw):
                        can_match = True
                        break
                if not can_match:
                    unmatched_in_scope.append((kp, title))
    
    node_analysis.append({
        'label': label,
        'matched_count': len(matched_tags),
        'matched_tags': sorted(set(matched_tags)),
        'own_keywords': sorted(own_kws),
        'all_keywords_count': len(all_kws),
        'unmatched_in_scope': unmatched_in_scope,
    })

# 5. 输出报告
report = []
for na in node_analysis:
    report.append({
        'label': na['label'],
        'matched_count': na['matched_count'],
        'own_keywords': na['own_keywords'],
        'unmatched_in_scope': [(kp, t) for kp, t in na['unmatched_in_scope']],
    })

out_path = os.path.join(os.path.dirname(__file__), 'kg_gap_report.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2, default=str)

# 人类可读报告
txt_path = os.path.join(os.path.dirname(__file__), 'kg_gap_report.txt')
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("知识图谱关键词覆盖检查报告\n")
    f.write(f"习题标签总数: {len(all_tags)}, 知识图谱节点数: {len(nodes)}\n")
    f.write("=" * 80 + "\n\n")
    
    # 只显示有匹配或有缺口的节点
    has_gap = False
    for na in node_analysis:
        if not na['unmatched_in_scope']:
            continue
        has_gap = True
        f.write(f"【{na['label']}】\n")
        f.write(f"  当前关键词: {na['own_keywords']}\n")
        f.write(f"  匹配到的习题标签 ({na['matched_count']}个): {sorted(set(na['matched_tags']))[:15]}\n")
        f.write(f"  无法匹配的习题标签 (本章节范围内):\n")
        for kp, title in na['unmatched_in_scope']:
            f.write(f"    ✗ '{kp}' — {title}\n")
        f.write("\n")
    
    if not has_gap:
        f.write("所有章节标签均已覆盖，无缺口。\n")
    
    # 误匹配检查
    f.write("\n" + "=" * 80 + "\n")
    f.write("【潜在误匹配检查】\n")
    f.write("=" * 80 + "\n")
    
    # 对每个标签，看它匹配到了哪些节点
    tag_to_nodes = {}
    for kp in all_tags:
        matched_nodes = []
        for na in node_analysis:
            if kp in na['matched_tags']:
                matched_nodes.append(na['label'])
        if len(matched_nodes) > 2:
            tag_to_nodes[kp] = matched_nodes
    
    if tag_to_nodes:
        f.write(f"被3个以上节点匹配的标签 ({len(tag_to_nodes)}个):\n")
        for kp, nodes_list in sorted(tag_to_nodes.items()):
            f.write(f"  '{kp}' → {nodes_list}\n")
    else:
        f.write("无严重误匹配（所有标签最多匹配2个节点）\n")
    
    # 跨域匹配
    f.write("\n" + "=" * 80 + "\n")
    f.write("【跨域匹配检查】被不同章节节点匹配的标签\n")
    f.write("=" * 80 + "\n")
    
    cross_domain = {}
    for kp in all_tags:
        matched_nodes = []
        for na in node_analysis:
            if kp in na['matched_tags']:
                matched_nodes.append(na['label'])
        if len(matched_nodes) > 1:
            # 检查是否跨章节
            chapters = set()
            for nl in matched_nodes:
                nm = re.match(r'^(\d+)', nl)
                if nm:
                    chapters.add(nm.group(1))
            if len(chapters) > 1:
                cross_domain[kp] = matched_nodes
    
    if cross_domain:
        f.write(f"跨章节匹配的标签 ({len(cross_domain)}个):\n")
        for kp, nodes_list in sorted(cross_domain.items()):
            f.write(f"  '{kp}' → {nodes_list}\n")
    else:
        f.write("无跨章节匹配\n")

print(f"报告已保存: {txt_path}")
print(f"JSON已保存: {out_path}")
