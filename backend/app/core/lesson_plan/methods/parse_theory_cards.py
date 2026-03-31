from .._shared import *


class _ParseTheoryCardsMixin:
    def _parse_theory_cards(self) -> Dict[str, Dict[str, str]]:
        """
        解析理论卡片，建立结构化索引
        
        Returns:
            理论卡片索引字典，格式为：
            {
                "理论卡片1": {
                    "name": "建构主义学习理论",
                    "core_view": "学习是学习者主动建构知识的过程，不是被动接受信息的过程。",
                    "applicable_links": "新知探究、小组合作、自主学习",
                    "applicable_methods": "探究式、合作学习",
                    "applicable_content": "概念教学、问题解决",
                    "teaching_inspiration": "设置问题情境，引导学生自主探究，通过协作学习建构知识体系。"
                },
                ...
            }
        """
        import re
        index = {}
        
        # 匹配理论卡片的正则表达式（支持表格格式）
        # 格式: | **理论卡片一：建构主义学习理论** |
        #       +----------------------------------+
        #       | **核心观点** | 内容 |
        #       +----------------------------------+
        #       | **教学启发** | 内容 |
        #       +----------------------------------+
        #       | **适用环节** | 内容 |
        #       +----------------------------------+
        
        # 匹配理论卡片标题
        card_pattern = r"\| \*\*理论卡片([一二三四五六七八九十]+)：([^\|]+)\*\*\s*\|"
        
        # 查找所有理论卡片
        card_matches = list(re.finditer(card_pattern, self.theory_cards, re.DOTALL))
        
        for i, card_match in enumerate(card_matches):
            card_number_chinese = card_match.group(1)
            card_name = card_match.group(2).strip()
            
            # 转换中文数字为阿拉伯数字
            chinese_to_arabic = {
                "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
                "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"
            }
            card_number = chinese_to_arabic.get(card_number_chinese, str(i + 1))
            
            # 获取当前理论卡片的完整内容（直到下一个理论卡片或文件结束）
            start_pos = card_match.start()
            end_pos = card_matches[i + 1].start() if i + 1 < len(card_matches) else len(self.theory_cards)
            card_content = self.theory_cards[start_pos:end_pos]
            
            # 提取核心观点
            core_view = ""
            core_view_match = re.search(r"\|\s*\*\*核心观点\*\*\s*\|\s*([^\|]+)\s*\|", card_content, re.DOTALL)
            if core_view_match:
                core_view = core_view_match.group(1).strip()
                # 清理多余的内容
                core_view = re.sub(r'\^\[\d+\]', '', core_view)  # 移除引用标记
                core_view = re.sub(r'\s+', ' ', core_view)  # 规范化空格
            
            # 提取适用环节
            applicable_links = ""
            applicable_links_match = re.search(r"\|\s*\*\*适用环节\*\*\s*\|\s*([^\|]+)\s*\|", card_content, re.DOTALL)
            if applicable_links_match:
                applicable_links = applicable_links_match.group(1).strip()
            
            # 提取教学启发（提取所有相关内容）
            teaching_inspiration = ""
            teaching_inspiration_elements = []
            
            # 查找教学启发表格部分
            teaching_inspiration_section = re.search(r"\|\s*\*\*教学启发\*\*\s*\|.*?\+(?:-+\+)+.*?\|(?:\s*\|.*?)+", card_content, re.DOTALL)
            if teaching_inspiration_section:
                teaching_inspiration_text = teaching_inspiration_section.group(0)
                
                # 提取教学启发表格中的标题行（第一行）
                title_match = re.search(r"\|\s*\*\*教学启发\*\*\s*\|.*\|", teaching_inspiration_text, re.DOTALL)
                if title_match:
                    title_line = title_match.group(0)
                    # 提取所有标题（如"情境的真实性"、"脚手架式的引导"），排除"教学启发"本身
                    titles = re.findall(r"\*\*([^*]+)\*\*", title_line)
                    teaching_inspiration_elements = [title.strip() for title in titles if title.strip() and title.strip() != "教学启发"]
                
                # 提取教学启发表格中的内容行（第二行）
                content_match = re.search(r"\|\s+.*?\|.*?\|.*?\|", teaching_inspiration_text, re.DOTALL)
                if content_match:
                    content_line = content_match.group(0)
                    # 提取所有内容
                    contents = re.findall(r"\|\s+([^|]+?)\s*\|", content_line)
                    teaching_inspiration = " ".join([content.strip() for content in contents if content.strip()])
                    # 清理多余的内容
                    teaching_inspiration = re.sub(r'\^\[\d+\]', '', teaching_inspiration)
                    teaching_inspiration = re.sub(r'\s+', ' ', teaching_inspiration)
            
            # 如果没有提取到教学启发要素，尝试从教学启发文本中提取
            if not teaching_inspiration_elements and teaching_inspiration:
                teaching_inspiration_elements = self._parse_teaching_inspiration_elements(teaching_inspiration)
            
            # 提取适用教学方法（基于理论名称和核心观点）
            applicable_methods = self._extract_applicable_methods(card_name, core_view)
            
            # 提取适用内容类型（基于理论名称和核心观点）
            applicable_content = self._extract_applicable_content(card_name, core_view)
            
            card_key = f"理论卡片{card_number}"
            index[card_key] = {
                "name": card_name,
                "core_view": core_view,
                "applicable_links": applicable_links,
                "applicable_methods": applicable_methods,
                "applicable_content": applicable_content,
                "teaching_inspiration": teaching_inspiration,
                "teaching_inspiration_elements": teaching_inspiration_elements
            }
        
        print(f"✅ 成功解析 {len(index)} 个理论卡片")
        return index
