"""
查找3-2-1函数的单调性.md文件中所有习题
"""
import json
import os
import glob

analysis_dir = r"d:\Git_Repository\Mathemist\learning_resource\exercise_analysis copy"

# 查找所有来自 "3-2-1函数的单调性.md" 的习题
target_source = "云端习题/函数习题/3-2-1函数的单调性.md"

print("=" * 80)
print(f"查找来源文件: {target_source}")
print("=" * 80)

found_exercises = []

for json_file in glob.glob(os.path.join(analysis_dir, "*.json")):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        source = data.get('original_resource', {}).get('source_file', '')
        if source == target_source:
            found_exercises.append({
                'file': os.path.basename(json_file),
                'data': data
            })
    except Exception as e:
        pass

print(f"\n共找到 {len(found_exercises)} 条习题\n")
print("-" * 80)

# 按题干长度排序（通常填空题较短）
found_exercises.sort(key=lambda x: len(x['data'].get('original_resource', {}).get('题干', '')))

for i, exercise in enumerate(found_exercises):
    data = exercise['data']
    original = data.get('original_resource', {})
    analysis = data.get('analysis', {})
    
    question_type = original.get('题目类型', 'N/A')
    stem = original.get('题干', 'N/A')[:150]
    difficulty = original.get('难度（1-5）', 'N/A')
    knowledge_tags = original.get('知识点标签', 'N/A')
    
    print(f"\n{i+1}. 文件: {exercise['file']}")
    print(f"   题型: {question_type}")
    print(f"   难度: {difficulty}")
    print(f"   知识点: {knowledge_tags}")
    print(f"   题干: {stem}...")
    
    # 检查是否是目标习题
    if 'x^2 - 2x - 3' in str(stem) or '绝对值' in str(knowledge_tags):
        print(f"   ⭐⭐⭐ 这是目标习题！⭐⭐⭐")
        
        # 打印完整的分析信息
        print(f"\n   完整分析:")
        print(f"     知识点: {analysis.get('知识点', [])}")
        print(f"     核心考点: {analysis.get('核心考点', '')}")
        print(f"     解题思路: {analysis.get('解题思路', '')[:100]}")
