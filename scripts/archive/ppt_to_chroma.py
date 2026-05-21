import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

# 初始化 ChromaDB
client = chromadb.PersistentClient(path="./edu_resources_chroma")
embedding_func = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_or_create_collection(
    name="high_school_math_resources",
    embedding_function=embedding_func
)

ids, documents, metadatas = [], [], []

# --- 1. 处理 PPT 表 ---
df_ppt = pd.read_excel("learning_resource/课件/课件汇总（必修一2.3-5.7）.xlsx", header=1)
print(df_ppt.columns.tolist())
df_ppt = df_ppt.dropna(subset=["内容"])  # 去除空行
for idx, row in df_ppt.iterrows():
    _id = f"ppt_{idx:04d}"
    content = str(row["内容"]).strip()
    filename = str(row["文件名"]).strip() if pd.notna(row["文件名"]) else f"ppt_{idx}.pptx"
    
    ids.append(_id)
    documents.append(content)  # 使用"内容"列作为描述
    metadatas.append({
        "type": "ppt",
        "title": content[:50],  # 截取前50字作标题
        "subject": "数学",
        "chapter": "必修一",
        "file_path": f"ppt/{filename}",
        "teaching_purpose": str(row["教学用途"]) if pd.notna(row["教学用途"]) else "新授课课件",
        "source_file": filename
    })

# --- 2. 处理 视频 表 ---
df_video = pd.read_excel("learning_resource/课例视频/优秀课例视频信息汇总.xlsx", header=0)
# 查看实际列名
print("实际列名:", df_video.columns.tolist())
print("\n前3行数据:")
print(df_video.head(3))

for idx, row in df_video.iterrows():
    _id = f"video_{idx:04d}"
    title = str(row["章节"]) if pd.notna(row["章节"]) else ""
    analysis = str(row["分析"]) if pd.notna(row["分析"]) else ""
    filename_raw = str(row["视频文件名/网址"])
    
    # 尝试提取 .mp4 文件名
    if ".mp4" in filename_raw:
        filename = filename_raw.split("/")[-1]
    else:
        filename = f"video_{idx}.mp4"
    
    doc_text = f"{title}。{analysis}".strip()
    
    ids.append(_id)
    documents.append(doc_text if doc_text != "。" else title)
    metadatas.append({
        "type": "video",
        "title": title[:50],
        "subject": "数学",
        "chapter": title,
        "file_path": f"video/{filename}",
        "teaching_purpose": "课例视频",
        "source_file": filename
    })

# --- 3. 处理 GGB 表 ---
df_ggb = pd.read_excel("learning_resource/ggb/ggb信息.xlsx", header=0)

for idx, row in df_ggb.iterrows():
    _id = f"ggb_{idx:04d}"
    chapter = str(row["章节"]) if pd.notna(row["章节"]) else ""
    usage = str(row["教学用途"]) if pd.notna(row["教学用途"]) else ""
    ggb_name = str(row["ggb文件名"]) if pd.notna(row["ggb文件名"]) else f"ggb_{idx}.ggb"
    
    doc_text = f"{chapter}。{usage}".strip()
    
    ids.append(_id)
    documents.append(doc_text if doc_text != "。" else chapter)
    metadatas.append({
        "type": "ggb",
        "title": chapter[:50],
        "subject": "数学",
        "chapter": chapter,
        "file_path": f"ggb/{ggb_name}",
        "teaching_purpose": "动态课件",
        "source_file": ggb_name
    })

# --- 4. 导入 ChromaDB ---
collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print(f"✅ 成功导入 {len(ids)} 条教学资源到 ChromaDB！")
print("示例检索：")
results = collection.query(
    query_texts=["一元二次不等式的解法"],
    n_results=2,
    where={"type": "ppt"}
)
print(results["metadatas"][0][0]["title"], "->", results["metadatas"][0][0]["file_path"])