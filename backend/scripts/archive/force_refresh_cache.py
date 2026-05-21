import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import hashlib
import json
import requests

def force_refresh_cache():
    """
    强制刷新目标教案的缓存
    """
    cloud_url = "https://math-1415627924.cos.ap-guangzhou.myqcloud.com/math-teaching-resources/03-概率与统计/01-教案/必修二/第十章概率/10.1 随机事件与概率/课时3310_10.1.4 概率的基本性质-10.1.4 概率的基本性质【公众号dc008免费分享】.md"

    # 计算cache key
    cache_key = hashlib.md5(cloud_url.encode("utf-8")).hexdigest()
    cache_dir = r"D:\Git_Repository\Mathemist\backend\data\cloud_lesson_plan_cache"
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    print(f"目标缓存文件: {cache_file}")

    # 删除旧缓存
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("已删除旧缓存文件")

    # 重新下载云端内容
    print("\n重新下载云端内容...")
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
        print(f"已写入新缓存文件")

        # 验证缓存
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        print(f"\n验证缓存: 长度={len(cached.get('content', ''))}")

    except Exception as e:
        print(f"下载失败: {e}")

if __name__ == "__main__":
    force_refresh_cache()