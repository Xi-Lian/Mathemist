import json

with open(r"D:\Git_Repository\Mathemist\knowledge_graph.json", "r", encoding="utf-8") as f:
    d = json.load(f)

nodes = d["nodes"]
edges = d["edges"]

print(f"节点数: {len(nodes)}")
print(f"边数: {len(edges)}")
print(f"顶层键: {list(d.keys())}")

level1 = [n for n in nodes if n.get("level") == 1]
print(f"一级板块数: {len(level1)}")
for n in level1:
    print(f"  - {n['label']} (id={n['id']})")

# 检查三角恒等变换的子节点
print("\n三角恒等变换相关节点：")
for n in nodes:
    if "三角" in n.get("label", "") or "trig_identity" in n.get("id", ""):
        print(f"  {n['id']} | level={n.get('level')} | parent={n.get('parent','')} | {n['label']}")
