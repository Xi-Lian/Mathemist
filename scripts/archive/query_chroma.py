"""
查询 ChromaDB 数据库，统计三角恒等变换相关习题
"""
import chromadb
from chromadb.config import Settings
import math

client = chromadb.PersistentClient(
    path='d:/Git_Repository/Mathemist/backend/chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

# 列出所有集合
collections = client.list_collections()
print('=== 所有集合 ===')
for c in collections:
    count = c.count()
    print(f'  {c.name}: {count} 条')

print()
print('=== 函数集合中习题统计 ===')
func_col = client.get_collection('math_resources_function')
total_count = func_col.count()
print(f'函数集合总数: {total_count}')

# 获取所有元数据（分批）
batch_size = 500
num_batches = math.ceil(total_count / batch_size)

exercise_count = 0
trig_identity_count = 0
sample_meta = []

for i in range(num_batches):
    offset = i * batch_size
    results = func_col.get(
        limit=batch_size,
        offset=offset,
        include=['metadatas']
    )
    for meta in results['metadatas']:
        rt = meta.get('resource_type', '') or ''
        if rt == 'exercise':
            exercise_count += 1
            # 检查是否与三角恒等变换相关
            kp = meta.get('知识点标签', '') or ''
            kp_from_meta = meta.get('知识点', '') or ''
            title = meta.get('title', '') or ''
            
            # 检查关键词
            keywords_to_check = [
                '三角恒等变换', '二倍角', '诱导公式', 
                '和差化积', '积化和差', '半角', 
                '两角和', '两角差', '辅助角', '降幂', '恒等变换'
            ]
            matched = False
            for kw in keywords_to_check:
                if kw in title or kw in kp or kw in kp_from_meta:
                    matched = True
                    break
            if matched:
                trig_identity_count += 1
                if len(sample_meta) < 30:
                    sample_meta.append({
                        'title': title,
                        'kp_tag': kp,
                        'kp_meta': kp_from_meta
                    })

print(f'函数集合中习题总数: {exercise_count}')
print(f'与三角恒等变换相关的习题数: {trig_identity_count}')
print()
print('=== 相关习题样本（前30条）===')
for i, m in enumerate(sample_meta):
    t = m["title"]
    k1 = m["kp_tag"]
    k2 = m["kp_meta"]
    print(f'{i+1}. {t}')
    print(f'   知识点标签: {k1}')
    print(f'   知识点: {k2}')
    print()
