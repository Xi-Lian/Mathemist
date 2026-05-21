#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.vector_database_builder import VectorDatabaseBuilder, QianWenExerciseAnalyzer

def analyze_single_exercise(analyzer, builder, resource, resource_type, exercise_id, output_dir, lock):
    """分析单个习题（线程安全）"""
    output_file = os.path.join(output_dir, f"{exercise_id}.json")
    
    try:
        processed_resource = builder._resolve_image_paths(resource)
        analysis = analyzer.analyze_exercise(processed_resource)
        
        result = {
            'exercise_id': exercise_id,
            'resource_type': resource_type,
            'title': resource.get('title', ''),
            'source_file': resource.get('source_file', ''),
            'analysis': analysis,
            'original_resource': resource,
            'analyzed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with lock:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return exercise_id, 'analyzed', result['title'][:30] if result['title'] else "Untitled"
    
    except Exception as e:
        return exercise_id, 'error', str(e)

def analyze_and_save_exercises_parallel(max_workers=5):
    """
    并行分析所有习题并保存结果到JSON文件
    """
    print("=" * 60)
    print("Parallel Analyzing exercises (Fast Mode)")
    print("=" * 60)
    
    output_dir = os.path.join(os.path.dirname(__file__), 'learning_resource', 'exercise_analysis')
    os.makedirs(output_dir, exist_ok=True)
    
    api_key = 'sk-2a32172dcc1740aabdec41e74119b426'
    analyzer = QianWenExerciseAnalyzer(api_key)
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
    print(f"Total exercises found: {total_exercises}")
    
    tasks = []
    lock = threading.Lock()
    
    for resource_type, resources in exercise_resources.items():
        for i, resource in enumerate(resources):
            source_file = resource.get('source_file', '')
            title = resource.get('title', '')
            exercise_id = f"{resource_type}_{i}_{hash(source_file + title) % 100000}"
            output_file = os.path.join(output_dir, f"{exercise_id}.json")
            
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if existing_data.get('analysis') and len(existing_data['analysis']) > 0:
                            continue
                except:
                    pass
                os.remove(output_file)
            
            tasks.append((analyzer, builder, resource, resource_type, exercise_id, output_dir, lock))
    
    print(f"\n待分析任务: {len(tasks)}")
    print(f"使用 {max_workers} 线程并行处理...")
    
    analyzed_count = 0
    skipped_count = total_exercises - len(tasks)
    error_count = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_single_exercise, *args) for args in tasks]
        
        for future in as_completed(futures):
            exercise_id, status, info = future.result()
            
            if status == 'analyzed':
                analyzed_count += 1
                print(f"  [分析完成] {exercise_id} - {info}")
            elif status == 'error':
                error_count += 1
                print(f"  [分析失败] {exercise_id} - {info}")
            
            if (analyzed_count + skipped_count + error_count) % 50 == 0:
                progress = (analyzed_count + skipped_count + error_count) / total_exercises * 100
                elapsed = time.time() - start_time
                print(f"\n进度: {progress:.1f}% ({analyzed_count + skipped_count + error_count}/{total_exercises})")
                print(f"已分析: {analyzed_count}, 已跳过: {skipped_count}, 错误: {error_count}")
                print(f"耗时: {elapsed:.1f}秒")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("Analysis completed!")
    print(f"Analyzed: {analyzed_count}")
    print(f"Skipped (already analyzed): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {analyzed_count + skipped_count + error_count}")
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Average speed: {(analyzed_count + skipped_count + error_count) / elapsed:.2f} exercises/sec")
    print("\nResults saved to:", output_dir)

if __name__ == "__main__":
    analyze_and_save_exercises_parallel(max_workers=5)
