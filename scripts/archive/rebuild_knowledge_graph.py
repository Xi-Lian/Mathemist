"""
重建 knowledge_graph.json，把所有板块节点合并到 nodes，所有边合并到 edges。
"""
import json

# 读取当前被破坏的文件
with open("knowledge_graph.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 收集所有节点
all_nodes = []
all_edges = []

# nodes 数组（原始结构）
if "nodes" in data and isinstance(data["nodes"], list):
    all_nodes.extend(data["nodes"])

# edges 数组（原始结构）
if "edges" in data and isinstance(data["edges"], list):
    all_edges.extend(data["edges"])

# 收集新增板块的节点（它们在顶层以板块名作为 key）
new_sections = [
    "algebra_basic", "analytic_geometry", "sequence",
    "plane_vector", "plane_geometry"
]
for key in new_sections:
    if key in data and isinstance(data[key], list):
        all_nodes.extend(data[key])

# 收集新增板块的 edges（如果有）
new_edge_keys = [
    "algebra_basic_edges", "analytic_geometry_edges", "sequence_edges",
    "plane_vector_edges", "plane_geometry_edges"
]
for key in new_edge_keys:
    if key in data and isinstance(data[key], list):
        all_edges.extend(data[key])

# 去重（按 id）
seen_ids = set()
deduped_nodes = []
for n in all_nodes:
    nid = n.get("id", "")
    if nid and nid not in seen_ids:
        seen_ids.add(nid)
        deduped_nodes.append(n)

seen_edge_keys = set()
deduped_edges = []
for e in all_edges:
    ek = (e.get("source", ""), e.get("target", ""), e.get("type", ""))
    if ek not in seen_edge_keys:
        seen_edge_keys.add(ek)
        deduped_edges.append(e)

# 重新组装
output = {
    "nodes": deduped_nodes,
    "edges": deduped_edges
}

with open("knowledge_graph.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"完成：{len(deduped_nodes)} 个节点，{len(deduped_edges)} 条边")
