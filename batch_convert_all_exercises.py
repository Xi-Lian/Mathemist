"""
批量处理所有云端习题Markdown文件
从Excel索引表中读取文件路径并转换知识点标签
"""
import os
import sys
import pandas as pd
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, 'backend')

def convert_knowledge_points(kp_str):
    """转换知识点标签格式"""
    if not kp_str or ';' not in str(kp_str):
        return kp_str
    
    parts = [p.strip() for p in str(kp_str).split(';') if p.strip()]
    
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
        
        lines = content.split('\n')
        modified_lines = []
        modified_count = 0
        
        for line in lines:
            if line.strip().startswith('#') or line.strip().startswith('| ---'):
                modified_lines.append(line)
                continue
            
            if '|' in line and ';' in line:
                cells = line.split('|')
                
                if len(cells) > 3:
                    new_cells = []
                    cell_modified = False
                    
                    for i, cell in enumerate(cells):
                        cell_stripped = cell.strip()
                        
                        math_terms = ['函数', '单调', '区间', '二次', '绝对值', '分段', '指数', '对数', 
                                     '三角', '集合', '不等式', '证明', '含参', '对称轴', '定义', 
                                     '性质', '应用', '讨论', '解不等式']
                        
                        is_kp_column = any(term in cell_stripped for term in math_terms) and ';' in cell_stripped
                        
                        if is_kp_column and ';' in cell_stripped:
                            converted = convert_knowledge_points(cell_stripped)
                            if converted != cell_stripped:
                                new_cells.append(f" {converted} ")
                                cell_modified = True
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
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return modified_count
        else:
            return 0
            
    except Exception as e:
        print(f"✗ 处理文件失败 {file_path}: {e}")
        return -1

def main():
    """主函数"""
    print("=" * 80)
    print("批量处理所有云端习题文件")
    print("=" * 80)
    
    # Excel索引表路径
    excel_files = [
        'learning_resource/函数习题_云端资源汇总表.xlsx',
        'learning_resource/概率与统计习题_云端资源汇总表.xlsx',
        'learning_resource/立体几何习题_云端资源汇总表.xlsx'
    ]
    
    total_files = 0
    total_modified = 0
    failed_files = 0
    
    for excel_path in excel_files:
        if not os.path.exists(excel_path):
            print(f"\n⚠️  文件不存在: {excel_path}")
            continue
        
        print(f"\n处理索引表: {excel_path}")
        print("-" * 80)
        
        try:
            df = pd.read_excel(excel_path)
            
            # 筛选出.md文件
            md_files = df[df['文件名'].str.endswith('.md', na=False)]
            
            print(f"  找到 {len(md_files)} 个Markdown文件")
            
            for idx, row in md_files.iterrows():
                local_path = row.get('本地完整路径', '')
                
                if not local_path or not os.path.exists(local_path):
                    continue
                
                total_files += 1
                modified_count = process_markdown_file(local_path)
                
                if modified_count > 0:
                    total_modified += 1
                    filename = os.path.basename(local_path)
                    print(f"  ✓ {filename}: 修改了 {modified_count} 行")
                elif modified_count == 0:
                    pass  # 无变化，不输出
                else:
                    failed_files += 1
                    
        except Exception as e:
            print(f"✗ 处理Excel文件失败: {e}")
    
    print("\n" + "=" * 80)
    print("处理完成统计:")
    print(f"  总文件数: {total_files}")
    print(f"  修改文件数: {total_modified}")
    print(f"  失败文件数: {failed_files}")
    print("=" * 80)

if __name__ == "__main__":
    main()
