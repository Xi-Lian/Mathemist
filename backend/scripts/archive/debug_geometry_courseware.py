#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_geometry_courseware():
    """调试几何板块课件分类问题"""
    print("调试几何板块课件分类问题")
    print("="*60)
    
    from app.core.resource_table.service import ResourceTableParser
    from app.core.vector_database_builder import VectorDatabaseBuilder
    
    # 解析课件资源
    parser = ResourceTableParser("D:/Git_Repository/Mathemist/learning_resource")
    courseware_list = parser.parse_courseware_table()
    
    # 创建构建器
    builder = VectorDatabaseBuilder("D:/Git_Repository/Mathemist/learning_resource")
    
    # 统计立体几何课件汇总表中的资源
    geometry_coursewares = [c for c in courseware_list if c.get('source_file') == '立体几何-课件汇总.xlsx']
    print(f"立体几何-课件汇总.xlsx中的课件数量: {len(geometry_coursewares)}")
    
    # 测试每个课件的板块识别
    board_results = {}
    for courseware in geometry_coursewares[:20]:
        source_file = courseware.get('source_file', '')
        title = courseware.get('title', '')
        content = courseware.get('内容', '')
        filename = courseware.get('文件名', '')
        
        board = builder._get_resource_board(source_file, 'courseware', title)
        
        board_results[board] = board_results.get(board, 0) + 1
        
        if board != '几何':
            print(f"\n板块识别异常:")
            print(f"  source_file: {source_file}")
            print(f"  title: {title}")
            print(f"  filename: {filename}")
            print(f"  识别到的板块: {board}")
    
    print(f"\n板块识别结果统计:")
    for board, count in board_results.items():
        print(f"  {board}: {count} 条")
    
    return True

if __name__ == "__main__":
    try:
        debug_geometry_courseware()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
