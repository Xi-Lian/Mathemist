from .._shared import *


class _ApplySubjectiveIntentFilterMixin:
    def _apply_subjective_intent_filter(self, metadata: Dict[str, Any], subjective_intent: Dict[str, Any], is_vague_query: bool = False) -> Dict[str, Any]:
        """
        V28.0：应用主观意图筛选（V32.0改进：支持灵活匹配）
        
        Args:
            metadata: 资源元数据
            subjective_intent: 主观意图信息
            is_vague_query: 是否是宽泛查询
        
        Returns:
            筛选结果字典，包含pass、reason和score_adjustment
        """
        # 获取资源的难度
        difficulty_str = metadata.get('难度（1-5）', '') or metadata.get('难度', '') or metadata.get('difficulty', '3')
        try:
            difficulty = int(difficulty_str)
        except (ValueError, TypeError):
            # 尝试从文本难度转换为数字
            difficulty_map = {
                '基础': 1,
                '简单': 1,
                '中等': 2,
                '一般': 2,
                '普通': 2,
                '难': 3,
                '困难': 3,
                '拔高': 4,
                '挑战': 4,
                '压轴': 5
            }
            if isinstance(difficulty_str, str):
                for key, value in difficulty_map.items():
                    if key in difficulty_str:
                        difficulty = value
                        break
                else:
                    difficulty = 3
            else:
                difficulty = 3
        
        # 获取主观意图的难度范围
        difficulty_range = subjective_intent.get('difficulty_range')
        
        if difficulty_range:
            min_difficulty, max_difficulty = difficulty_range
            
            # V32.0：宽泛查询时，放宽难度筛选
            if is_vague_query:
                # 宽泛查询 - 允许一定范围内的偏差
                tolerance = 1  # 允许1级的偏差
                
                if difficulty < min_difficulty - tolerance:
                    # 难度太低，但不过滤，只降低相关性
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}略低于要求，但宽泛查询允许',
                        'score_adjustment': 0.6
                    }
                elif difficulty > max_difficulty + tolerance:
                    # 难度太高，但不过滤，只降低相关性
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}略高于要求，但宽泛查询允许',
                        'score_adjustment': 0.6
                    }
                else:
                    # 难度在可接受范围内
                    target_difficulty = (min_difficulty + max_difficulty) / 2
                    diff_from_target = abs(difficulty - target_difficulty)
                    score_adjustment = 1.0 - (diff_from_target / 3.0)  # 最多降低33%
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}符合要求',
                        'score_adjustment': max(0.7, score_adjustment)
                    }
            else:
                # 具体查询 - 严格难度筛选
                if difficulty < min_difficulty:
                    return {
                        'pass': False,
                        'reason': f'难度{difficulty}低于要求范围[{min_difficulty}-{max_difficulty}]'
                    }
                elif difficulty > max_difficulty:
                    return {
                        'pass': False,
                        'reason': f'难度{difficulty}高于要求范围[{min_difficulty}-{max_difficulty}]'
                    }
                else:
                    target_difficulty = (min_difficulty + max_difficulty) / 2
                    diff_from_target = abs(difficulty - target_difficulty)
                    score_adjustment = 1.0 - (diff_from_target / 2.0)
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}在要求范围内',
                        'score_adjustment': max(0.5, score_adjustment)
                    }
        
        # 没有难度要求，默认通过
        return {'pass': True, 'reason': '无难度要求'}
