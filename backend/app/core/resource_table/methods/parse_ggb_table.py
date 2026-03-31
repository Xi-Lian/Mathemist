from .._shared import *


class _ParseGgbTableMixin:
    def parse_ggb_table(self) -> List[Dict[str, str]]:
        """
        解析GGB资源汇总表
        支持.md和.xlsx格式
        
        Returns:
            GGB资源列表
        """
        # 首先尝试查找.md文件
        ggb_file = self.learning_resource_path / 'ggb' / 'ggb信息.md'
        
        if ggb_file.exists():
            # 解析markdown文件
            with open(ggb_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = self.parse_markdown_table(content)
            
            # 添加资源类型
            for item in data:
                item['resource_type'] = 'ggb'
            
            logger.info(f"解析GGB汇总表(md)，共{len(data)}条记录")
            return data
        
        # 如果没有.md文件，尝试.xlsx文件
        ggb_xlsx = self.learning_resource_path / 'ggb' / 'ggb信息.xlsx'
        
        if ggb_xlsx.exists():
            try:
                import pandas as pd
                
                # 读取Excel文件
                df = pd.read_excel(ggb_xlsx)
                
                # 转换为字典列表
                data = []
                i = 1
                for _, row in df.iterrows():
                    # 为GGB资源创建有效的标题
                    title_parts = []
                    if pd.notna(row.get('章节')) and row['章节'].strip():
                        title_parts.append(row['章节'].strip())
                    if pd.notna(row.get('ggb文件名')) and row['ggb文件名'].strip():
                        title_parts.append(row['ggb文件名'].strip())
                    if pd.notna(row.get('教学用途')) and row['教学用途'].strip():
                        title_parts.append(row['教学用途'].strip())
                    
                    title = ' - '.join(title_parts) if title_parts else f"GGB资源_{i}"
                    
                    item = {
                        'resource_type': 'ggb',
                        'source_file': str(ggb_xlsx.relative_to(self.learning_resource_path)),
                        'title': title,
                        **{k: str(v) if pd.notna(v) else '' for k, v in row.items()}
                    }
                    data.append(item)
                    i += 1
                
                logger.info(f"解析GGB汇总表(xlsx)，共{len(data)}条记录")
                return data
                
            except Exception as e:
                logger.error(f"解析GGB Excel文件失败: {e}")
                return []
        
        logger.warning(f"GGB汇总表不存在: {ggb_file} 或 {ggb_xlsx}")
        return []
