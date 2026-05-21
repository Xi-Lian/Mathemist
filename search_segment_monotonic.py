import os
import json

# 搜索所有exercise_analysis文件
analysis_dir = '../learning_resource/exercise_analysis'
found = []

for filename in os.listdir(analysis_dir):
    if filename.startswith('exercise_') and filename.endswith('.json'):
        filepath = os.path.join(analysis_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 检查知识点是否包含分段函数单调性
                analysis = data.get('analysis', {})
                kp_list = analysis.get('知识点', [])
                kp_tag = data.get('original_resource', {}).get('知识点标签', '')
                
                # 检查是否涉及分段函数单调性
                has_segment = any('分段函数' in str(kp) for kp in kp_list) or '分段函数' in kp_tag
                has_monotonic = any('单调' in str(kp) for kp in kp_list) or '单调' in kp_tag
                
                if has_segment and has_monotonic:
                    found.append({
                        'filename': filename,
                        'title': data.get('title', ''),
                        '知识点': kp_list,
                        '知识点标签': kp_tag
                    })
        except Exception as e:
            print(f"Error reading {filename}: {e}")

print(f'找到 {len(found)} 个关于分段函数单调性的习题:')
for item in found[:10]:
    print(f"\n文件: {item['filename']}")
    print(f"标题: {item['title']}")
    print(f"知识点: {item['知识点']}")
    print(f"知识点标签: {item['知识点标签']}")
