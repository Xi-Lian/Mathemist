import json
import os

analysis_dir = r'd:\Git_Repository\Mathemist\learning_resource\exercise_analysis'

deleted_count = 0
kept_count = 0

for f in os.listdir(analysis_dir):
    if f.endswith('.json'):
        file_path = os.path.join(analysis_dir, f)
        try:
            with open(file_path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                analysis = data.get('analysis')
                if analysis is None or (isinstance(analysis, dict) and len(analysis) == 0):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f'Deleted: {f}')
                else:
                    kept_count += 1
        except Exception as e:
            print(f'Error: {f} - {e}')

print(f'\nDeleted: {deleted_count} files')
print(f'Kept: {kept_count} files')
