import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from sentence_transformers import SentenceTransformer

print("开始下载 paraphrase-multilingual-MiniLM-L12-v2 模型...")
print("使用镜像源: https://hf-mirror.com")
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print("✅ 模型下载完成！")
print(f"模型路径: {model._first_module().auto_model}")
