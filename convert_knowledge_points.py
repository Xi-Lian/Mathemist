"""
批量修改云端习题文件中的知识点标签格式
将 "知识点1;知识点2" 改为 "知识点1的知识点2"
"""
import os
import re
from pathlib import Path

def convert_knowledge_points(kp_str):
    """
    转换知识点标签格式
    例如: "绝对值函数;单调区间" -> "绝对值函数的单调区间"
         "函数单调性;区间判断" -> "函数单调性的区间判断"
    """
    if not kp_str or ';' not in kp_str:
        return kp_str
    
    parts = [p.strip() for p in kp_str.split(';') if p.strip()]
    
    if len(parts) < 2:
        return kp_str
    
    # 将第一个知识点作为主体，后续知识点用"的"连接
    result = parts[0]
    for part in parts[1:]:
        result += f"的{part}"
    
    return result

def process_markdown_file(file_path):
    """处理单个Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 匹配表格行中的知识点标签（在 | 和 | 之间）
        # 模式：查找形如 "| ... | 知识点1;知识点2 | ..." 的部分
        lines = content.split('\n')
        modified_lines = []
        modified_count = 0
        
        for line in lines:
            # 跳过标题行和分隔线
            if line.strip().startswith('#') or line.strip().startswith('| ---'):
                modified_lines.append(line)
                continue
            
            # 只处理包含表格行的内容
            if '|' in line and ';' in line:
                # 分割表格单元格
                cells = line.split('|')
                
                # 检查是否有知识点标签列（通常是第4列，索引为3）
                if len(cells) > 3:
                    # 遍历所有单元格，查找包含分号的知识点标签
                    new_cells = []
                    cell_modified = False
                    
                    for i, cell in enumerate(cells):
                        cell_stripped = cell.strip()
                        
                        # 检查是否是知识点标签（通常包含常见数学术语）
                        math_terms = ['函数', '单调', '区间', '二次', '绝对值', '分段', '指数', '对数', 
                                     '三角', '集合', '不等式', '证明', '含参', '对称轴', '定义', 
                                     '性质', '应用', '讨论', '解不等式']
                        
                        is_kp_column = any(term in cell_stripped for term in math_terms) and ';' in cell_stripped
                        
                        if is_kp_column and ';' in cell_stripped:
                            # 转换知识点格式
                            converted = convert_knowledge_points(cell_stripped)
                            if converted != cell_stripped:
                                new_cells.append(f" {converted} ")
                                cell_modified = True
                                print(f"  修改: '{cell_stripped}' -> '{converted}'")
                            else:
                                new_cells.append(cell)
                        else:
                            new_cells.append(cell)
                    
                    if cell_modified:
                        modified_count += 1
                        modified_lines.append('|'.join(new_cells))
                    else:
                        modified_lines.append(line)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        new_content = '\n'.join(modified_lines)
        
        # 只有当内容有变化时才写入文件
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ 文件已更新: {file_path}")
            print(f"  共修改 {modified_count} 行\n")
            return True
        else:
            print(f"- 文件无变化: {file_path}\n")
            return False
            
    except Exception as e:
        print(f"✗ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("批量修改习题知识点标签格式")
    print("=" * 80)
    print("\n转换规则:")
    print("  '知识点1;知识点2' -> '知识点1的知识点2'")
    print("  '知识点1;知识点2;知识点3' -> '知识点1的知识点2的知识点3'")
    print("\n" + "=" * 80)
    
    # 测试文件
    test_file = 'temp_3-2-1.md'
    
    if os.path.exists(test_file):
        print(f"\n处理测试文件: {test_file}")
        print("-" * 80)
        process_markdown_file(test_file)
    else:
        print(f"测试文件不存在: {test_file}")
    
    print("\n" + "=" * 80)
    print("提示: 这只是一个测试脚本")
    print("如果要批量处理所有云端文件，需要:")
    print("1. 从Excel索引表中获取所有云端文件的本地路径")
    print("2. 遍历所有文件并调用 process_markdown_file()")
    print("=" * 80)

if __name__ == "__main__":
    main()
