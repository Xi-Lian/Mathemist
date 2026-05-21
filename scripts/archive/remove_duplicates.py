import json
import os

def remove_duplicates():
    analysis_dir = r'd:\Git_Repository\Mathemist\learning_resource\exercise_analysis'
    
    content_signatures = {}
    duplicates_to_remove = []
    kept_files = []
    
    for f in os.listdir(analysis_dir):
        if f.endswith('.json'):
            file_path = os.path.join(analysis_dir, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    
                    title = data.get('title', '')
                    original_resource = data.get('original_resource', {})
                    question = original_resource.get('题干', '')
                    
                    signature = f"{title}||{question}"
                    
                    if signature in content_signatures:
                        duplicates_to_remove.append(f)
                    else:
                        content_signatures[signature] = f
                        kept_files.append(f)
            except Exception as e:
                pass
    
    print(f"发现 {len(duplicates_to_remove)} 个重复文件")
    print(f"保留 {len(kept_files)} 个唯一文件")
    
    deleted_count = 0
    for f in duplicates_to_remove:
        file_path = os.path.join(analysis_dir, f)
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception as e:
            pass
    
    print(f"成功删除 {deleted_count} 个重复文件")
    
    print(f"\n清理后状态:")
    print(f"  剩余文件数: {len([f for f in os.listdir(analysis_dir) if f.endswith('.json')])}")
    print(f"  唯一题目数: {len(content_signatures)}")

if __name__ == "__main__":
    remove_duplicates()
