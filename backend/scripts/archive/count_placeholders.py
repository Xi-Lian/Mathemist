import chromadb

def count_placeholder_files():
    """
    统计向量数据库中使用占位符文件的资源数量
    """
    db_path = r"D:\Git_Repository\Mathemist\backend\chroma_db"

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("math_resources")

    total = collection.count()
    print(f"数据库中总资源数: {total}")

    # 获取所有资源
    all_resources = collection.get(limit=total, include=["documents", "metadatas"])

    placeholder_count = 0
    real_content_count = 0
    placeholder_by_type = {}
    real_by_type = {}

    for i, doc in enumerate(all_resources.get('documents', [])):
        metadata = all_resources['metadatas'][i] if i < len(all_resources.get('metadatas', [])) else None
        resource_type = metadata.get('resource_type', 'unknown') if metadata else 'unknown'

        is_placeholder = '占位符' in doc or '此文件为自动生成' in doc

        if is_placeholder:
            placeholder_count += 1
            placeholder_by_type[resource_type] = placeholder_by_type.get(resource_type, 0) + 1
        else:
            real_content_count += 1
            real_by_type[resource_type] = real_by_type.get(resource_type, 0) + 1

    print(f"\n=== 统计结果 ===")
    print(f"占位符文件数量: {placeholder_count} ({placeholder_count/total*100:.1f}%)")
    print(f"真实内容文件数量: {real_content_count} ({real_content_count/total*100:.1f}%)")

    print(f"\n=== 按资源类型统计 ===")
    all_types = set(placeholder_by_type.keys()) | set(real_by_type.keys())

    # 获取每种类型的总数
    type_total = {}
    for i, metadata in enumerate(all_resources.get('metadatas', [])):
        if metadata:
            rt = metadata.get('resource_type', 'unknown')
            type_total[rt] = type_total.get(rt, 0) + 1

    for rt in sorted(all_types):
        placeholder = placeholder_by_type.get(rt, 0)
        real = real_by_type.get(rt, 0)
        total_rt = type_total.get(rt, 0)
        print(f"\n{rt}:")
        print(f"  总数: {total_rt}")
        print(f"  占位符: {placeholder} ({placeholder/total_rt*100:.1f}%)")
        print(f"  真实内容: {real} ({real/total_rt*100:.1f}%)")

    # 显示一些占位符示例
    print(f"\n=== 占位符文件示例（前10个） ===")
    example_count = 0
    for i, doc in enumerate(all_resources.get('documents', [])):
        if '占位符' in doc or '此文件为自动生成' in doc:
            metadata = all_resources['metadatas'][i] if i < len(all_resources.get('metadatas', [])) else None
            title = metadata.get('title', '未知') if metadata else '未知'
            rt = metadata.get('resource_type', 'unknown') if metadata else 'unknown'
            print(f"  {example_count + 1}. [{rt}] {title}")
            example_count += 1
            if example_count >= 10:
                break

if __name__ == "__main__":
    count_placeholder_files()