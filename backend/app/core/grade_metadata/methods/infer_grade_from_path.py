from .._shared import *


class _InferGradeFromPathMixin:
    def infer_grade_from_path(self, source_file: str) -> Optional[Dict[str, Any]]:
        """
        从文件路径推断年级信息
        
        Args:
            source_file: 资源文件路径（相对于learning_resource）
            
        Returns:
            年级信息字典，包含grade、grade_level等字段
        """
        if not source_file:
            return None
        
        # 标准化路径分隔符
        source_file = source_file.replace('/', '\\')
        path_lower = source_file.lower()
        
        # 1. 检查教材册别标识 - 按长度降序排序，优先匹配更长的名称
        sorted_book_keys = sorted(
            self.CHAPTER_TO_GRADE_MAPPING.keys(), 
            key=len, 
            reverse=True
        )
        
        for book_key in sorted_book_keys:
            book_key_lower = book_key.lower()
            # 检查是否在路径中出现，并且是完整的路径段
            if book_key_lower in path_lower:
                # 检查是否是完整的路径段
                # 查找book_key在路径中的所有位置
                positions = []
                start_pos = 0
                while True:
                    pos = path_lower.find(book_key_lower, start_pos)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start_pos = pos + 1
                
                # 检查每个位置是否是完整的路径段
                for pos in positions:
                    # 检查前后是否是路径分隔符或字符串边界
                    # 前边界：开始位置或路径分隔符/空格
                    has_front_boundary = pos == 0 or path_lower[pos-1] in ['\\', '/'] or path_lower[pos-1].isspace()
                    
                    # 后边界：结束位置或路径分隔符/空格/中文数字（如"第一"）
                    end_pos = pos + len(book_key_lower)
                    has_back_boundary = end_pos == len(path_lower) or \
                        path_lower[end_pos] in ['\\', '/', '.', ' '] or \
                        (end_pos < len(path_lower) and path_lower[end_pos] in ['第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'])
                    
                    is_boundary = has_front_boundary and has_back_boundary
                    
                    if is_boundary:
                        book_info = self.CHAPTER_TO_GRADE_MAPPING[book_key]
                        return {
                            'grade': book_info['grade'],
                            'grade_level': book_info['grade_level'],
                            'textbook_volume': book_key,
                            'inference_source': 'file_path',
                            'confidence': 0.9
                        }
        
        # 2. 检查章节号（如"第四章"、"4.1"）
        chapter_pattern = r'[第]?([一二三四五六七八九十1234567890]+)[章课节]'
        chapter_match = re.search(chapter_pattern, source_file)
        
        if chapter_match:
            chapter_num = chapter_match.group(1)
            # 尝试匹配各册的章节
            for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
                for chap_key in book_info['chapters'].keys():
                    if chapter_num in chap_key or chap_key in chapter_num:
                        return {
                            'grade': book_info['grade'],
                            'grade_level': book_info['grade_level'],
                            'textbook_volume': book_key,
                            'chapter': chap_key,
                            'inference_source': 'chapter_number',
                            'confidence': 0.8
                        }
        
        # 3. 特殊处理：检查路径中是否包含年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in path_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'path_keyword',
                        'confidence': 0.75
                    }
        
        return None
