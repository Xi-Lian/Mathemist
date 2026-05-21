"""
检查习题的实际字段结构
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.model_config import model_config

def check_exercise_fields():
    """检查习题的字段结构"""
    print("=" * 80)
    print("检查习题的实际字段结构")
    print("=" * 80)
    
    vector_db = model_config.get_chroma_client()
    collection = vector_db.get_collection("math_resources_function")
    
    # 获取一条包含"指数"的习题
    results = collection.get(
        where={"resource_type": "exercise"},
        include=["metadatas"],
        limit=100
    )
    
    all_metadatas = results.get('metadatas', [])
    
    # 找到包含"指数"的习题
    index_exercises = []
    for meta in all_metadatas:
        title = meta.get('title', '')
        kp = meta.get('知识点', '') or meta.get('知识点标签', '')
        if '指数' in title or '指数' in kp:
            index_exercises.append(meta)
    
    print(f"\n找到 {len(index_exercises)} 条包含'指数'的习题\n")
    
    if index_exercises:
        # 显示第一条的完整字段
        print("=" * 80)
        print("第一条习题的完整元数据字段：")
        print("=" * 80)
        first_meta = index_exercises[0]
        
        for key, value in sorted(first_meta.items()):
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            print(f"  {key}: {value_str}")
        
        print("\n" + "=" * 80)
        print("关键字段检查：")
        print("=" * 80)
        
        # 检查关键宇段是否存在
        key_fields = [
            'title',
            '知识点',
            '知识点标签',
            'analysis',
            'analysis_json',
            'resource_type',
            '题干',
            '题目文件名',
            'document'
        ]
        
        for field in key_fields:
            if field in first_meta:
                value = first_meta[field]
                if isinstance(value, str) and len(value) > 80:
                    value = value[:80] + "..."
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ {field}: 不存在")
        
        # 特别检查"4-3-2对数的运算"这条
        print("\n" + "=" * 80)
        print("检查'4-3-2对数的运算'这类习题：")
        print("=" * 80)
        
        for meta in index_exercises:
            title = meta.get('title', '')
            if '对数' in title and '指数' in (meta.get('知识点', '') or meta.get('知识点标签', '')):
                print(f"\n标题: {title}")
                print(f"  知识点: {meta.get('知识点', 'N/A')}")
                print(f"  知识点标签: {meta.get('知识点标签', 'N/A')}")
                print(f"  analysis存在: {'analysis' in meta}")
                print(f"  analysis_json存在: {'analysis_json' in meta}")
                
                if 'analysis_json' in meta and meta['analysis_json']:
                    import json
                    try:
                        analysis = json.loads(meta['analysis_json'])
                        print(f"  analysis.知识点: {analysis.get('知识点', 'N/A')}")
                    except:
                        print(f"  analysis_json解析失败")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_exercise_fields()
