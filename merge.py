import chromadb
import json

# 加载两个数据库
client_md = chromadb.PersistentClient(path="./chroma_db")      # 教案、大纲
client_path = chromadb.PersistentClient(path="./chroma_ppt") # PPT、GGB路径
new_client = chromadb.PersistentClient(path="./chroma_teaching_resource")

# 创建统一的教学资源集合
try:
    collection = new_client.create_collection("teaching_resource")
except:
    collection = new_client.get_collection("teaching_resource")

def merge_with_metadata(source_client, prefix, resource_type, target_collection):
    """
    合并数据并添加资源类型标记
    
    resource_type: "teaching_plan"(教案), "syllabus"(大纲), "ppt", "ggb" 等
    """
    # 获取源数据库的所有集合
    source_collections = source_client.list_collections()
    
    for src_coll in source_collections:
        coll_name = src_coll.name
        source = source_client.get_collection(coll_name)
        data = source.get()
        
        if not data['ids']:
            continue
            
        # 构造新ID: 类型_原集合_前缀_原ID
        new_ids = [f"{resource_type}_{coll_name}_{prefix}_{id}" for id in data['ids']]
        
        # 增强元数据：添加资源类型和来源
        enhanced_metadatas = []
        for meta in data['metadatas']:
            enhanced_meta = {
                **meta,
                "resource_type": resource_type,      # 资源类型
                "source_collection": coll_name,      # 来源集合
                "source_db": prefix,                # 来源数据库
                "content_category": "text" if resource_type in ["teaching_plan", "syllabus"] else "file_path"
            }
            enhanced_metadatas.append(enhanced_meta)
        
        # 添加到目标集合
        target_collection.add(
            ids=new_ids,
            documents=data['documents'],
            metadatas=enhanced_metadatas,
            embeddings=data['embeddings']
        )
        
        print(f"[{resource_type}] 从 {coll_name} 合并了 {len(new_ids)} 条记录")

# 合并教案/大纲（文本内容）
merge_with_metadata(client_md, "db1", "teaching_plan", collection)
# 如果有多个类型，分别调用：
# merge_with_metadata(client_md, "db1", "syllabus", collection)

# 合并PPT/GGB路径
merge_with_metadata(client_path, "db2", "ppt", collection)
# merge_with_metadata(client_path, "db2", "ggb", collection)

print(f"\n✅ 教学资源库构建完成！总计: {collection.count()} 条记录")
