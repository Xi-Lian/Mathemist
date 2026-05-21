import json
import os

analysis_dir = r'd:\Git_Repository\Mathemist\learning_resource\exercise_analysis'

exercise_ids = {}
duplicates = []

for f in os.listdir(analysis_dir):
    if f.endswith('.json'):
        file_path = os.path.join(analysis_dir, f)
        try:
            with open(file_path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                exercise_id = data.get('exercise_id', '')
                if exercise_id:
                    if exercise_id in exercise_ids:
                        duplicates.append((exercise_id, f, exercise_ids[exercise_id]))
                    else:
                        exercise_ids[exercise_id] = f
        except Exception as e:
            pass

if duplicates:
    print(f'发现 {len(duplicates)} 个重复的 exercise_id:')
    for dup in duplicates[:5]:
        print(f'  {dup[0]}: {dup[1]} 和 {dup[2]}')
    if len(duplicates) > 5:
        print(f'  ... 还有 {len(duplicates) - 5} 个重复')
else:
    print('没有发现重复的分析文件')

print(f'\n总共有 {len(exercise_ids)} 个不同的 exercise_id')
print(f'总文件数: {len([f for f in os.listdir(analysis_dir) if f.endswith(".json")])}')
