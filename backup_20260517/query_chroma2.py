"""
查看搜索文本(search_text)的内容
"""
import chromadb
from chromadb.config import Settings
import math

client = chromadb.PersistentClient(
    path='d:/Git_Repository/Mathemist/backend/chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

func_col = client.get_collection('math_resources_function')
total_count = func_col.count()
print(f'函数集合总数: {total_count}')

# 获取所有数据（分批），查看搜索文本
batch_size = 500
num_batches = math.ceil(total_count / batch_size)

print()
print('=== 三角恒等变换相关习题的搜索文本样本 ===')
found_count = 0

for i in range(num_batches):
    offset = i * batch_size
    results = func_col.get(
        limit=batch_size,
        offset=offset,
        include=['metadatas', 'documents']
    )
    metadatas = results['metadatas']
    documents = results['documents']
    
    for j, meta in enumerate(metadatas):
        rt = meta.get('resource_type', '') or ''
        if rt != 'exercise':
            continue
            
        kp = meta.get('知识点标签', '') or ''
        title = meta.get('title', '') or ''
        
        # 检查是否与三角恒等变换相关
        keywords_to_check = [
            '三角恒等变换', '二倍角', '诱导公式', 
            '和差化积', '积化和差', '半角', 
            '两角和', '两角差', '辅助角', '降幂'
        ]
        matched = False
        for kw in keywords_to_check:
            if kw in title or kw in kp:
                matched = True
                break
        
        if matched:
            found_count += 1
            if found_count <= 5:  # 只打印前5条的搜索文本
                doc = documents[j] or ''
                print(f'--- 第 {found_count} 条 ---')
                print(f'标题: {title}')
                print(f'知识点标签: {kp}')
                print(f'知识点(analysis): {meta.get("知识点", "")}')
                print(f'搜索文本前500字符:')
                print(doc[:500])
                print()
            
            if found_count >= 5:
                break
    
    if found_count >= 5:
        break

print(f'共找到 {found_count} 条相关习题（仅显示前5条的搜索文本）')
