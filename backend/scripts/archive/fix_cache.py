import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import hashlib
import json
import requests

def check_lesson_plan_content():
    """
    直接检查目标教案在解析过程中的实际内容
    """
    # 目标教案的云端链接
    cloud_url = "https://math-1415627924.cos.ap-guangzhou.myqcloud.com/math-teaching-resources/03-概率与统计/01-教案/必修二/第十章概率/10.1 随机事件与概率/课时3310_10.1.4 概率的基本性质-10.1.4 概率的基本性质【公众号dc008免费分享】.md"

    print(f"云端链接: {cloud_url}")

    # 模拟_download_cloud_markdown的缓存逻辑
    cache_key = hashlib.md5(cloud_url.encode("utf-8")).hexdigest()
    cache_dir = r"D:\Git_Repository\Mathemist\backend\data\cloud_lesson_plan_cache"
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    print(f"Cache key: {cache_key}")
    print(f"Cache file: {cache_file}")
    print(f"Cache exists: {os.path.exists(cache_file)}")

    # 直接下载云端文件
    print("\n=== 直接下载云端文件 ===")
    try:
        response = requests.get(cloud_url, timeout=10)
        response.raise_for_status()
        content = response.text
        print(f"云端文件长度: {len(content)}")
        print(f"是否包含占位符: {'占位符' in content or '此文件为自动生成' in content}")

        # 写入缓存
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({"url": cloud_url, "content": content}, f, ensure_ascii=False)
        print(f"\n已写入缓存文件: {cache_file}")

    except Exception as e:
        print(f"下载失败: {e}")

if __name__ == "__main__":
    check_lesson_plan_content()