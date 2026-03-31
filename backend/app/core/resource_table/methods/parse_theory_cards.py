from .._shared import *


class _ParseTheoryCardsMixin:
    def parse_theory_cards(self) -> List[Dict[str, str]]:
        """
        解析理论卡片
        
        Returns:
            理论卡片列表
        """
        theory_cards = []
        
        # 在理论卡片文件夹中查找理论卡片
        theory_folder = self.learning_resource_path / '理论卡片'
        
        if theory_folder.exists():
            for md_file in theory_folder.rglob('*.md'):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    item = {
                        'resource_type': 'theory',
                        'source_file': str(md_file.relative_to(self.learning_resource_path)),
                        'title': md_file.stem,
                        'content': content
                    }
                    theory_cards.append(item)
                    
                    logger.info(f"解析理论卡片: {md_file.name}")
                    
                except Exception as e:
                    logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 在教案文件夹中查找理论卡片（向后兼容）
        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if lesson_plan_folder.exists():
            for md_file in lesson_plan_folder.rglob('*.md'):
                if '理论卡片' in md_file.name:
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        item = {
                            'resource_type': 'theory',
                            'source_file': str(md_file.relative_to(self.learning_resource_path)),
                            'title': md_file.stem,
                            'content': content
                        }
                        theory_cards.append(item)
                        
                        logger.info(f"解析理论卡片: {md_file.name}")
                        
                    except Exception as e:
                        logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 解析优秀教案共性整合文档
        theory_file = lesson_plan_folder / '优秀教案共性整合（最终版）.md'
        if theory_file.exists():
            try:
                with open(theory_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                item = {
                    'resource_type': 'theory',
                    'source_file': str(theory_file.relative_to(self.learning_resource_path)),
                    'title': theory_file.stem,
                    'content': content
                }
                theory_cards.append(item)
                
                logger.info(f"解析优秀教案共性整合文档")
                
            except Exception as e:
                logger.error(f"解析优秀教案共性整合文档失败: {e}")
        
        logger.info(f"解析理论卡片完成，共{len(theory_cards)}条记录")
        return theory_cards
