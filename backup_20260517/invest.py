import os
import traceback
from pathlib import Path
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

def main():
    # 配置参数
    DOCS_DIR = r"C:\Users\pain\Desktop\学习\大二下\数智师小队\learning_resource"
    CHROMA_DB_DIR = "chroma_db"
    COLLECTION_NAME = "knowledge_base"
    
    # 初始化 ChromaDB 客户端（提前初始化，避免后续异常导致客户端未定义）
    client = None
    try:
        # === 1. 校验路径和文件 ===
        if not os.path.exists(DOCS_DIR):
            raise FileNotFoundError(f"文档目录不存在：{DOCS_DIR}")
        
        # === 2. 加载 .md 文件（带编码和空检查）===
        print("📂 加载 Markdown 文件...")
        loader = DirectoryLoader(
            DOCS_DIR, 
            glob="**/*.md", 
            show_progress=True,
            # encoding="utf-8"  # 解决中文乱码
        )
        documents = loader.load()
        
        if len(documents) == 0:
            raise ValueError(f"未在 {DOCS_DIR} 找到任何 .md 文件，请检查路径/文件格式")
        print(f"✅ 加载 {len(documents)} 个文档")

        # === 3. 切分文本 ===
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

        # === 4. 加载 embedding 模型（优先本地，兜底远程）===
        print("🧠 加载 embedding 模型...")
        # 方案：使用多语言模型（对中文友好），避免重复赋值
        model = SentenceTransformer( r"C:\Users\pain\Desktop\学习\大二下\数智师小队\paraphrase-multilingual-MiniLM-L12-v2")
        # model = SentenceTransformer(
        #     "paraphrase-multilingual-MiniLM-L12-v2",
        #     cache_folder= r"C:\Users\pain\Desktop\学习\大二下\数智师小队\paraphrase-multilingual-MiniLM-L12-v2"  # 模型缓存到本地，避免重复下载
        # )
        
        # from sentence_transformers import SentenceTransformer

        # model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        # sentences = [
        #     "The weather is lovely today.",
        #     "It's so sunny outside!",
        #     "He drove to the stadium."
        # ]
        # embeddings = model.encode(sentences)

        # similarities = model.similarity(embeddings, embeddings)
        # print(similarities.shape)
        # [3, 3]
        # === 5. 生成向量（分批编码，避免内存溢出）===
        embeddings = model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=32,  # 小批次编码，适配低配电脑
            normalize_embeddings=True
        ).tolist()
        print(f"✅ 生成 {len(embeddings)} 个向量")

    #     # === 6. 初始化 ChromaDB（确保目录可写）===
    #     os.makedirs(CHROMA_DB_DIR, exist_ok=True)  # 确保目录存在
    #     client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
    #     # === 7. 操作 ChromaDB ===
    #     # 删除旧集合（忽略不存在的情况）
    #     if client.get_collection(COLLECTION_NAME) is not None:
    #         client.delete_collection(COLLECTION_NAME)
        
    #     # 创建新集合
    #     collection = client.create_collection(
    #         name=COLLECTION_NAME,
    #         metadata={"hnsw:space": "cosine"}
    #     )
        
    #     # 批量添加数据
    #     collection.add(
    #         ids=ids,
    #         embeddings=embeddings,
    #         documents=texts,
    #         metadatas=metadatas
    #     )

    #     print("🎉 全部完成！数据已存入 ChromaDB（路径：{}）".format(CHROMA_DB_DIR))

    # except Exception as e:
    #     # 捕获所有异常，打印详细堆栈
    #     print(f"\n❌ 执行失败：{str(e)}")
    #     traceback.print_exc()
    # finally:
    #     # 确保客户端正常关闭（避免资源泄漏）
    #     if client is not None:
    #         try:
    #             client.close()
    #         except:
    #             pass
    # === 6. 初始化 ChromaDB ===
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

        # === 7. 安全删除并重建集合 ===
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"🗑️  已删除旧集合: {COLLECTION_NAME}")
        except chromadb.errors.NotFoundError:
            print(f"ℹ️  集合 {COLLECTION_NAME} 不存在，将创建新集合")

        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        # 分批插入，避免超过 ChromaDB 的最大批量限制（5461）
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
        # # 添加数据
        # collection.add(
        #     ids=ids,
        #     embeddings=embeddings,
        #     documents=texts,
        #     metadatas=metadatas
        # )
    except Exception as e:
        # 捕获所有异常，打印详细堆栈
        print(f"\n❌ 执行失败：{str(e)}")
        traceback.print_exc()
    finally:
        # 确保客户端正常关闭（避免资源泄漏）
        if client is not None:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    main()