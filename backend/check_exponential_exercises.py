"""
检查指数函数相关习题的数据库情况
"""
import sys
import os
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.model_config import model_config

def check_exercise_database():
    """检查习题数据库"""
    print("=" * 80)
    print("检查指数函数相关习题的数据库情况")
    print("=" * 80)
    
    # 获取ChromaDB客户端
    vector_db = model_config.get_chroma_client()
    
    # 检查函数板块集合
    collection_name = "math_resources_function"
    print(f"\n1. 检查集合: {collection_name}")
    
    try:
        collection = vector_db.get_collection(collection_name)
        print(f"   ✓ 集合存在")
        
        # 获取集合统计信息
        count = collection.count()
        print(f"   总资源数: {count}")
        
        # 查询所有习题类型的资源
        print(f"\n2. 查询所有习题资源...")
        exercise_results = collection.get(
            where={"resource_type": "exercise"},
            include=["metadatas"]
        )
        
        exercise_count = len(exercise_results['ids']) if exercise_results['ids'] else 0
        print(f"   习题总数: {exercise_count}")
        
        # 检查包含"指数"关键词的习题
        print(f"\n3. 检查包含'指数'关键词的习题...")
        all_metadatas = exercise_results.get('metadatas', [])
        
        index_related = []
        for i, meta in enumerate(all_metadatas):
            title = meta.get('title', '')
            kp = meta.get('知识点', '') or meta.get('知识点标签', '')
            analysis_json = meta.get('analysis_json', '')
            
            # 检查标题、知识点、分析中是否包含"指数"
            if '指数' in title or '指数' in kp or '指数' in analysis_json:
                index_related.append({
                    'index': i,
                    'title': title,
                    'kp': kp,
                    'has_index_in_title': '指数' in title,
                    'has_index_in_kp': '指数' in kp,
                    'has_index_in_analysis': '指数' in analysis_json
                })
        
        print(f"   包含'指数'的习题数: {len(index_related)}")
        
        if index_related:
            print(f"\n4. 详细列表（前20条）:")
            for idx, item in enumerate(index_related[:20]):
                print(f"   [{idx+1}] 标题: {item['title'][:60]}")
                print(f"       知识点: {item['kp'][:80]}")
                print(f"       标题含'指数': {item['has_index_in_title']}, "
                      f"知识点含'指数': {item['has_index_in_kp']}")
                print()
        else:
            print(f"   ⚠️ 未找到任何包含'指数'的习题！")
        
        # 检查一些可能的习题标题样例
        print(f"\n5. 随机抽样10条习题标题:")
        import random
        if all_metadatas:
            samples = random.sample(all_metadatas, min(10, len(all_metadatas)))
            for i, meta in enumerate(samples):
                title = meta.get('title', '无标题')
                kp = meta.get('知识点', '') or meta.get('知识点标签', '')
                print(f"   [{i+1}] {title[:60]} | 知识点: {kp[:40]}")
        
        # 检查是否有"对数的运算"这类相关但标题不含"指数"的习题
        print(f"\n6. 检查可能相关的习题（知识点包含'指数运算'但标题不含'指数'）:")
        related_but_no_index_title = []
        for meta in all_metadatas:
            title = meta.get('title', '')
            kp = meta.get('知识点', '') or meta.get('知识点标签', '')
            
            if ('指数运算' in kp or '指数' in kp) and '指数' not in title:
                related_but_no_index_title.append({
                    'title': title,
                    'kp': kp
                })
        
        print(f"   数量: {len(related_but_no_index_title)}")
        if related_but_no_index_title:
            for idx, item in enumerate(related_but_no_index_title[:10]):
                print(f"   [{idx+1}] 标题: {item['title'][:60]}")
                print(f"       知识点: {item['kp'][:80]}")
        
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    check_exercise_database()
