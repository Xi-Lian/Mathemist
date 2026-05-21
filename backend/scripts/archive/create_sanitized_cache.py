import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import hashlib
import json
import requests
from urllib.parse import urlsplit, urlunsplit, quote, unquote

def create_correct_cache():
    """
    为目标教案创建正确的缓存（基于sanitized URL）
    """
    # 实际的MD URL
    md_url = "https://math-1415627924.cos.ap-guangzhou.myqcloud.com/math-teaching-resources/03-概率与统计/01-教案/必修二/第十章概率/10.1 随机事件与概率/课时3310_10.1.4 概率的基本性质-10.1.4 概率的基本性质【公众号dc008免费分享】.md"

    # 模拟sanitize_cloud_url
    def sanitize_url(url):
        parts = urlsplit(url.strip())
        sanitized_path = quote(unquote(parts.path), safe="/-_.~")
        sanitized_query = quote(unquote(parts.query), safe="=&-_.~")
        return urlunsplit((parts.scheme, parts.netloc, sanitized_path, sanitized_query, parts.fragment))

    # 生成正确的缓存键
    sanitized_md_url = sanitize_url(md_url)
    cache_key = hashlib.md5(sanitized_md_url.encode("utf-8")).hexdigest()

    cache_dir = r"D:\Git_Repository\Mathemist\backend\data\cloud_lesson_plan_cache"
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    print(f"MD URL: {md_url}")
    print(f"Sanitized URL: {sanitized_md_url}")
    print(f"Cache key: {cache_key}")
    print(f"Cache file: {cache_file}")

    # 下载内容
    print("\n下载内容...")
    try:
        response = requests.get(md_url, timeout=10)
        response.raise_for_status()
        content = response.text
        print(f"下载成功，内容长度: {len(content)}")

        # 写入缓存
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({"url": sanitized_md_url, "content": content}, f, ensure_ascii=False)
        print(f"已写入缓存文件: {cache_file}")

    except Exception as e:
        print(f"下载失败: {e}")

if __name__ == "__main__":
    create_correct_cache()