import json
import os

def check_duplicate_content():
    analysis_dir = r'd:\Git_Repository\Mathemist\learning_resource\exercise_analysis'
    
    content_signatures = {}
    duplicates = []
    
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
                        duplicates.append({
                            'file1': content_signatures[signature],
                            'file2': f,
                            'title': title,
                            'question': question[:50] + '...' if len(question) > 50 else question
                        })
                    else:
                        content_signatures[signature] = f
            except Exception as e:
                pass
    
    if duplicates:
        print(f'发现 {len(duplicates)} 组内容重复的题目:')
        for i, dup in enumerate(duplicates[:10], 1):
            print(f"\n{i}. 重复题目:")
            print(f"   文件1: {dup['file1']}")
            print(f"   文件2: {dup['file2']}")
            print(f"   标题: {dup['title']}")
            print(f"   题干: {dup['question']}")
        if len(duplicates) > 10:
            print(f"\n... 还有 {len(duplicates) - 10} 组重复")
    else:
        print('没有发现内容重复的题目')
    
    print(f"\n总共有 {len(content_signatures)} 道不同的题目")
    print(f"总文件数: {len([f for f in os.listdir(analysis_dir) if f.endswith('.json')])}")

if __name__ == "__main__":
    check_duplicate_content()
