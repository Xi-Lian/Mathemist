import chromadb

def find_target_lesson_plan():
    """
    查找目标教案在向量数据库中的实际状态
    """
    db_path = r"D:\Git_Repository\Mathemist\backend\chroma_db"

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("math_resources")

    # 获取所有lesson_plan资源
    all_lessons = collection.get(
        where={"resource_type": "lesson_plan"},
        limit=1000
    )

    print(f"数据库中lesson_plan资源总数: {len(all_lessons.get('ids', []))}")

    # 查找包含"10.1.4"的教案
    target_plans = []
    for i, metadata in enumerate(all_lessons.get('metadatas', [])):
        if metadata and isinstance(metadata, dict):
            title = metadata.get('title', '')
            if '10.1.4' in title:
                target_plans.append((i, title, metadata))

    print(f"\n找到包含'10.1.4'的教案数量: {len(target_plans)}")

    for idx, title, metadata in target_plans:
        print(f"\n--- 教案 {idx} ---")
        print(f"标题: {title}")
        print(f"元数据: {metadata}")

        # 获取对应的文档内容
        doc_id = all_lessons['ids'][idx]
        doc_result = collection.get(ids=[doc_id], include=["documents"])
        if doc_result['documents']:
            doc = doc_result['documents'][0]
            print(f"文档长度: {len(doc)}")
            print(f"文档前500字符: {doc[:500]}...")

if __name__ == "__main__":
    find_target_lesson_plan()