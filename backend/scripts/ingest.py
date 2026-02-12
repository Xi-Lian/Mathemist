import os
import traceback
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

def main():
    SCRIPT_DIR = Path(__file__).parent.parent.parent
    DOCS_DIR = SCRIPT_DIR / "learning_resource"
    CHROMA_DB_DIR = SCRIPT_DIR / "backend" / "chroma_db"
    COLLECTION_NAME = "knowledge_base"
    
    client = None
    try:
        if not os.path.exists(DOCS_DIR):
            raise FileNotFoundError(f"文档目录不存在：{DOCS_DIR}")
        
        print("📂 加载 Markdown 文件...")
        loader = DirectoryLoader(
            str(DOCS_DIR), 
            glob="**/*.md", 
            show_progress=True
        )
        documents = loader.load()
        
        if len(documents) == 0:
            raise ValueError(f"未在 {DOCS_DIR} 找到任何 .md 文件，请检查路径/文件格式")
        print(f"✅ 加载 {len(documents)} 个文档")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        texts = [chunk.page_content.strip() for chunk in chunks if chunk.page_content.strip()]
        metadatas = [{"source": chunk.metadata["source"]} for chunk in chunks if chunk.page_content.strip()]
        ids = [f"id_{i}" for i in range(len(texts))]
        
        if len(texts) == 0:
            raise ValueError("所有文档切分后均为空，无法生成向量")
        print(f"✅ 文本切分完成，有效文本块数：{len(texts)}")

        print("🧠 加载 embedding 模型...")
        model = SentenceTransformer(r"C:\Users\15137\.cache\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\snapshots\e8f8c211226b894fcb81acc59f3b34ba3efd5f42")

        embeddings = model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True
        ).tolist()
        print(f"✅ 生成 {len(embeddings)} 个向量")

        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"🗑️  已删除旧集合: {COLLECTION_NAME}")
        except ValueError:
            print(f"ℹ️  集合 {COLLECTION_NAME} 不存在，将创建新集合")

        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        BATCH_SIZE = 5000
        total = len(ids)

        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            print(f"📤 插入批次: {start} ~ {end - 1} / {total}")
            
            collection.add(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=texts[start:end],
                metadatas=metadatas[start:end]
            )
        
        print(f"🎉 全部完成！数据已存入 ChromaDB（路径：{CHROMA_DB_DIR}）")
    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")
        traceback.print_exc()
    finally:
        if client is not None:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    main()
