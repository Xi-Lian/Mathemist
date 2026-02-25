"""
测试教案文件的解析过程
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_table_parser import ResourceTableParser


def test_lesson_plan_parsing():
    """测试教案文件的解析"""
    print("=" * 80)
    print("测试教案文件的解析")
    print("=" * 80)
    
    # 获取正确的learning_resource路径
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    learning_resource_path = project_root / 'learning_resource'
    
    print(f"\n📂 Learning Resource路径: {learning_resource_path}")
    
    parser = ResourceTableParser(str(learning_resource_path))
    
    print(f"\n🔍 解析教案资源...")
    lesson_plans = parser.parse_lesson_plan_tables()
    
    print(f"\n📊 总解析到的教案数: {len(lesson_plans)}")
    
    print(f"\n🔍 查找包含4.2的教案:")
    count_42 = 0
    
    for i, lp in enumerate(lesson_plans):
        source_file = lp.get('source_file', '')
        if '4.2' in source_file:
            count_42 += 1
            print(f"\n{'=' * 80}")
            print(f"✅ 找到4.2教案 #{count_42}:")
            print(f"索引: {i}")
            print(f"源文件: {source_file}")
            print(f"标题: {lp.get('title', 'N/A')}")
            if 'content' in lp:
                print(f"内容预览: {lp.get('content', '')[:100]}...")
    
    print(f"\n📊 4.2教案总数: {count_42}")
    
    if count_42 == 0:
        print(f"\n❌ 没有找到任何4.2教案！让我们检查4.2文件夹中的文件:")
        
        lesson_plan_folder = learning_resource_path / '教案'
        folder_42 = lesson_plan_folder / '第四章 指数函数与对数函数' / '4.2指数函数'
        
        if folder_42.exists():
            print(f"\n📁 4.2文件夹存在: {folder_42}")
            files = list(folder_42.glob('*.md'))
            print(f"\n📄 4.2文件夹中的文件:")
            for f in files:
                print(f"   - {f.name}")
                # 检查是否包含表格
                try:
                    content = f.read_text(encoding='utf-8')
                    has_table = '|' in content
                    print(f"     包含表格: {'✓ 是' if has_table else '✗ 否'}")
                except Exception as e:
                    print(f"     读取失败: {e}")
        else:
            print(f"\n❌ 4.2文件夹不存在: {folder_42}")


if __name__ == "__main__":
    test_lesson_plan_parsing()
