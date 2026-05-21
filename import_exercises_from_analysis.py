#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path

# 添加 backend 到路径
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

from app.core.vector_database_builder import VectorDatabaseBuilder
from app.core.resource_table_parser import ResourceTableParser

def load_exercises_from_analysis(analysis_dir):
    """
    从分析结果目录加载习题数据
    """
    exercises = []
    analysis_dir = Path(analysis_dir)
    
    if not analysis_dir.exists():
        print(f"警告: 分析目录不存在: {analysis_dir}")
        return exercises
    
    json_files = list(analysis_dir.glob('*.json'))
    print(f"找到 {len(json_files)} 个分析文件")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 提取原始资源数据
            original_resource = data.get('original_resource', {})
            
            if original_resource:
                # 合并分析结果到资源中
                resource = original_resource.copy()
                analysis = data.get('analysis', {})
                if analysis:
                    resource['analysis'] = analysis
                
                # 确保必需字段存在
                if not resource.get('resource_type'):
                    resource['resource_type'] = 'exercise'
                if not resource.get('title'):
                    resource['title'] = data.get('title', '未知标题')
                if not resource.get('source_file'):
                    resource['source_file'] = data.get('source_file', '分析结果导入')
                
                exercises.append(resource)
                if len(exercises) % 100 == 0:
                    print(f"已加载 {len(exercises)} 条习题")
                    
        except Exception as e:
            print(f"加载文件失败 {json_file.name}: {e}")
            continue
    
    print(f"共加载 {len(exercises)} 条习题")
    return exercises

def import_exercises_to_database(exercises):
    """
    将习题导入向量数据库
    """
    if not exercises:
        print("没有可导入的习题")
        return False
    
    # 创建构建器
    builder = VectorDatabaseBuilder('learning_resource')
    client = builder.get_chroma_client()
    embedding_model = builder.get_embedding_model()
    parser = ResourceTableParser('learning_resource')
    
    print("\n开始导入习题到向量数据库...")
    
    # 按板块分组
    board_groups = {}
    for exercise in exercises:
        board = exercise.get('板块', exercise.get('board', '几何'))
        # 统一板块名称
        if '函数' in board or '代数' in board:
            board = '函数'
        elif '几何' in board:
            board = '几何'
        elif '概率' in board or '统计' in board:
            board = '概率统计'
        else:
            board = '几何'  # 默认归为几何板块
        
        if board not in board_groups:
            board_groups[board] = []
        board_groups[board].append(exercise)
    
    total_imported = 0
    
    for board_name, board_exercises in board_groups.items():
        collection_name = builder.BOARD_COLLECTION_MAPPING.get(board_name, f"math_resources_{board_name}")
        
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            print(f"创建集合: {collection_name}")
            collection = client.create_collection(collection_name)
        
        print(f"\n处理 {board_name} 板块，共 {len(board_exercises)} 条习题...")
        
        batch_documents = []
        batch_metadatas = []
        batch_ids = []
        resource_id = 0
        
        for exercise in board_exercises:
            # 格式化搜索文本
            document = parser.format_resource_for_search(exercise)
            
            # 准备元数据
            filtered_resource = {k: v for k, v in exercise.items() if k not in ['resource_type', 'source_file', 'title', 'analysis']}
            
            # 处理 analysis_json
            if 'analysis' in exercise and exercise['analysis']:
                try:
                    filtered_resource['analysis_json'] = json.dumps(exercise['analysis'], ensure_ascii=False)
                except Exception as e:
                    print(f"序列化 analysis 失败: {e}")
            
            metadata = {
                'resource_type': 'exercise',
                'source_file': exercise.get('source_file', ''),
                'title': exercise.get('title', ''),
                'board': board_name,
                **filtered_resource
            }
            
            batch_documents.append(document)
            batch_metadatas.append(metadata)
            batch_ids.append(f"{board_name}_exercise_{resource_id}")
            resource_id += 1
            
            if len(batch_documents) >= 100:
                print(f"  批量写入 {len(batch_documents)} 条...")
                embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
                collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                    embeddings=embeddings
                )
                total_imported += len(batch_documents)
                batch_documents = []
                batch_metadatas = []
                batch_ids = []
        
        if batch_documents:
            print(f"  批量写入 {len(batch_documents)} 条...")
            embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
            collection.add(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids,
                embeddings=embeddings
            )
            total_imported += len(batch_documents)
        
        print(f"{board_name} 板块导入完成")
    
    print(f"\n✅ 共导入 {total_imported} 条习题")
    return True

def main():
    print("=" * 60)
    print("从分析结果导入习题资源")
    print("=" * 60)
    
    # 加载习题数据
    analysis_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learning_resource', 'exercise_analysis')
    exercises = load_exercises_from_analysis(analysis_dir)
    
    if not exercises:
        print("没有找到可导入的习题数据")
        return
    
    # 导入到数据库
    success = import_exercises_to_database(exercises)
    
    if success:
        print("\n🎉 习题导入成功！")
    else:
        print("\n❌ 习题导入失败")

if __name__ == "__main__":
    main()
