"""临时脚本：查看 5-5-1 习题的知识点标签"""
import chromadb
import os
import json

client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), 'backend', 'chroma_db'))
col = client.get_collection('math_resources_function')

results = col.get(include=['metadatas'])

# 找出所有 5-5-1 习题
output = []
for doc_id, meta in zip(results['ids'], results['metadatas']):
    title = meta.get('title', '')
    if '5-5-1' in title and 'exercise' in doc_id:
        kp = meta.get('知识点', '')
        kp_tag = meta.get('知识点标签', '')
        output.append({
            'id': doc_id,
            'title': title,
            '知识点': kp,
            '知识点标签': kp_tag,
        })

with open(os.path.join(os.path.dirname(__file__), 'check_kp_result.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Found {len(output)} exercises with 5-5-1 in title')
