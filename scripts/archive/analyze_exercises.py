#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

import os
import json
import time
import threading
from queue import Queue
from app.core.vector_database_builder import VectorDatabaseBuilder, ExerciseAnalyzer

def process_exercise(exercise_id, resource, analyzer, builder, output_dir, progress_queue):
    """处理单个习题"""
    try:
        title = resource.get('title', '')
        source_file = resource.get('source_file', '')
        
        output_file = os.path.join(output_dir, f"{exercise_id}.json")
        
        # 检查是否已分析（且analysis不为空）
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if existing_data.get('analysis') and len(existing_data['analysis']) > 0:
                    progress_queue.put({'type': 'skipped', 'exercise_id': exercise_id, 'title': title})
                    return
        
        # analysis为空或文件不存在，需要分析
        processed_resource = builder._resolve_image_paths(resource)
        analysis = analyzer.analyze_exercise(processed_resource)
        
        # 保存结果
        result = {
            'exercise_id': exercise_id,
            'resource_type': resource.get('resource_type', 'exercise'),
            'title': title,
            'source_file': source_file,
            'analysis': analysis,
            'original_resource': resource,
            'analyzed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        progress_queue.put({'type': 'analyzed', 'exercise_id': exercise_id, 'title': title})
        
    except Exception as e:
        progress_queue.put({'type': 'error', 'exercise_id': exercise_id, 'error': str(e)})

def analyze_and_save_exercises():
    """
    分析所有习题并保存结果到JSON文件
    支持检测空analysis字段并重新分析
    """
    print("=" * 60)
    print("Analyzing exercises and saving results")
    print("=" * 60)
    
    output_dir = os.path.join(os.path.dirname(__file__), 'learning_resource', 'exercise_analysis')
    os.makedirs(output_dir, exist_ok=True)
    
    api_key = 'sk-b1bbbcbf88504b1c96e70da79772ff16'
    analyzer = ExerciseAnalyzer(api_key)
    print("Analyzer initialized")
    
    builder = VectorDatabaseBuilder('learning_resource')
    print("Builder initialized")
    
    print("Parsing resource tables...")
    all_resources = builder.parser.parse_all_tables()
    
    exercise_resources = {}
    for resource_type, resources in all_resources.items():
        if resource_type.lower() in ['exercise', '习题', '题目']:
            exercise_resources[resource_type] = resources
    
    total_exercises = sum(len(resources) for resources in exercise_resources.values())
    print("Total exercises found:", total_exercises)
    
    # 收集所有待处理的习题
    all_tasks = []
    for resource_type, resources in exercise_resources.items():
        for i, resource in enumerate(resources):
            source_file = resource.get('source_file', '')
            title = resource.get('title', '')
            exercise_id = f"{resource_type}_{i}_{hash(source_file + title) % 100000}"
            
            output_file = os.path.join(output_dir, f"{exercise_id}.json")
            need_analysis = True
            
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if existing_data.get('analysis') and len(existing_data['analysis']) > 0:
                        need_analysis = False
            
            if need_analysis:
                all_tasks.append((exercise_id, resource))
    
    print(f"Total exercises to analyze: {len(all_tasks)}")
    print(f"Skipping {total_exercises - len(all_tasks)} already analyzed exercises")
    
    # 并行处理
    num_threads = 5
    progress_queue = Queue()
    threads = []
    
    def worker():
        while True:
            try:
                exercise_id, resource = task_queue.get(timeout=1)
                process_exercise(exercise_id, resource, analyzer, builder, output_dir, progress_queue)
                task_queue.task_done()
                time.sleep(0.5)
            except:
                break
    
    task_queue = Queue()
    for task in all_tasks:
        task_queue.put(task)
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    # 监控进度
    analyzed_count = 0
    skipped_count = 0
    error_count = 0
    total_tasks = len(all_tasks)
    
    while any(t.is_alive() for t in threads) or not progress_queue.empty():
        while not progress_queue.empty():
            progress = progress_queue.get()
            if progress['type'] == 'analyzed':
                analyzed_count += 1
                print(f"  [分析完成] {progress['exercise_id']} - {progress['title'][:30]}")
            elif progress['type'] == 'skipped':
                skipped_count += 1
            elif progress['type'] == 'error':
                error_count += 1
                print(f"  [分析失败] {progress['exercise_id']} - {progress['error']}")
        
        if analyzed_count + skipped_count > 0:
            progress = (analyzed_count + skipped_count) / total_tasks * 100
            print(f"\r进度: {progress:.1f}% ({analyzed_count + skipped_count}/{total_tasks})", end='')
        
        time.sleep(1)
    
    for t in threads:
        t.join()
    
    print("\n\nAnalysis completed!")
    print("Analyzed:", analyzed_count)
    print("Skipped (already analyzed):", skipped_count)
    print("Errors:", error_count)
    print("Total processed:", analyzed_count + skipped_count)
    print("\nResults saved to:", output_dir)

if __name__ == "__main__":
    analyze_and_save_exercises()
