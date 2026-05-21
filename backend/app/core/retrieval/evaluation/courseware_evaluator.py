"""
课件评估器 - 基于内容、文件名、教学用途三个字段的灵活评分系统

特点：
1. 动态权重：根据查询类型和字段可用性自动调整权重
2. 智能降级：某字段缺失时，重新分配权重到其他字段
3. 上下文感知：理解用户意图，针对性评分
"""

from typing import Dict, List, Optional, Tuple
import re


class CoursewareEvaluator:
    """课件评估器"""
    
    def __init__(self):
        # 默认权重配置
        self.default_weights = {
            'filename': 0.30,
            'teaching_use': 0.25,
            'content': 0.45
        }
        self.base_vector_weight = 0.20
    
    def evaluate(
        self, 
        metadata: Dict, 
        doc: str, 
        distance: float,
        core_theme: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Tuple[float, bool, Dict]:
        """
        综合评估课件资源
        
        Returns:
            (最终得分, 是否展示, 评分详情)
        """
        
        # 提取三个核心字段
        filename = metadata.get('文件名', '') or metadata.get('title', '')
        title = metadata.get('title', '')
        description = metadata.get('描述', '') or metadata.get('摘要', '')  # V41.8: 添加描述字段
        teaching_use = metadata.get('教学用途', '') or metadata.get('teaching_use', '')
        content = doc or metadata.get('内容', '')
        
        # V41.8改进：系统性方案 - 多字段联合检查
        # 不再依赖单一字段，而是检查所有相关字段
        # 只要任一字段包含核心主题，就认为资源可能相关
        if core_theme:
            has_core_in_any_field = False
            themes = [t.strip() for t in core_theme.split(',') if t.strip()]
            
            # 定义需要检查的相关字段（按优先级排序）
            fields_to_check = [
                ('文件名', filename),
                ('标题', title),
                ('描述', description),
            ]
            
            for field_name, field_text in fields_to_check:
                if not field_text:
                    continue
                    
                for theme in themes:
                    # Level 1：精确匹配（最高优先级）
                    pattern = r'\b' + re.escape(theme) + r'\b'
                    if re.search(pattern, field_text, re.IGNORECASE):
                        has_core_in_any_field = True
                        break
                    
                    # Level 2：模糊匹配（次优先级）
                    if theme in field_text:
                        has_core_in_any_field = True
                        break
                    
                    # Level 3：关键词组合匹配（V41.9改进）
                    # 如果主题包含多个词，检查这些词是否都出现在字段中
                    theme_words = re.split(r'[的与和及]', theme)
                    theme_words = [w.strip() for w in theme_words if len(w.strip()) > 1]
                    
                    if len(theme_words) >= 2:
                        # 检查所有关键词是否都出现在字段中
                        all_words_present = all(word in field_text for word in theme_words)
                        if all_words_present:
                            has_core_in_any_field = True
                            break
                    
                    # Level 4：部分关键词匹配（最低优先级，需要70%以上匹配）
                    if len(theme_words) >= 3:
                        matched_count = sum(1 for word in theme_words if word in field_text)
                        match_ratio = matched_count / len(theme_words)
                        
                        if match_ratio >= 0.7:  # 至少70%的关键词匹配
                            has_core_in_any_field = True
                            break
                
                if has_core_in_any_field:
                    break
            
            # 如果没有核心主题匹配，检查前3个关键词
            if not has_core_in_any_field:
                try:
                    from app.config.dynamic_config_loader import DynamicConfigLoader
                    config_loader = DynamicConfigLoader()
                    
                    for theme in themes:
                        theme_info = config_loader.get_knowledge_hierarchy().get(theme, {})
                        keywords = theme_info.get('keywords', [])
                        high_priority_keywords = keywords[:3] if len(keywords) > 3 else keywords
                        
                        # 检查所有字段
                        for field_name, field_text in fields_to_check:
                            if not field_text:
                                continue
                            for keyword in high_priority_keywords:
                                if keyword in field_text:
                                    has_core_in_any_field = True
                                    break
                            if has_core_in_any_field:
                                break
                        
                        if has_core_in_any_field:
                            break
                except:
                    pass
            
            # 如果所有相关字段都没有核心主题相关内容，直接拒绝
            if not has_core_in_any_field:
                base_relevance = max(0.0, 1.0 - (distance / 2)) if distance is not None else 0.5
                details = {
                    'base_relevance': base_relevance,
                    'filename_score': 0.0,
                    'teaching_use_score': 0.0,
                    'content_score': 0.0,
                    'weights': self.default_weights.copy(),
                    'final_score': 0.0,
                    'threshold': 0.0,
                    'should_show': False,
                    'reject_reason': '所有相关字段（文件名、标题、描述）都不包含核心主题'
                }
                return 0.0, False, details
        
        # 计算基础向量相关性
        base_relevance = max(0.0, 1.0 - (distance / 2)) if distance is not None else 0.5
        
        # 动态计算权重
        weights = self._calculate_dynamic_weights(
            filename=filename,
            teaching_use=teaching_use,
            content=content,
            query=query
        )
        
        # 分别评分三个字段
        filename_score = self._score_filename(filename, core_theme, query)
        teaching_use_score = self._score_teaching_use(teaching_use, query)
        content_score = self._score_content(content, core_theme, query, metadata)
        
        # 加权综合评分
        field_score = (
            filename_score * weights['filename'] +
            teaching_use_score * weights['teaching_use'] +
            content_score * weights['content']
        )
        
        final_score = (
            base_relevance * self.base_vector_weight +
            field_score * (1 - self.base_vector_weight)
        )
        
        # 动态阈值判断
        threshold = self._calculate_threshold(query, core_theme)
        should_show = final_score >= threshold
        
        # 构建评分详情
        details = {
            'base_relevance': base_relevance,
            'filename_score': filename_score,
            'teaching_use_score': teaching_use_score,
            'content_score': content_score,
            'weights': weights,
            'final_score': final_score,
            'threshold': threshold,
            'should_show': should_show
        }
        
        return final_score, should_show, details
    
    def _calculate_dynamic_weights(
        self, 
        filename: str, 
        teaching_use: str, 
        content: str,
        query: str
    ) -> Dict[str, float]:
        """动态计算三个字的权重"""
        weights = self.default_weights.copy()
        
        # 策略1：检测缺失字段并重新分配权重
        missing_fields = []
        if not filename or len(filename.strip()) < 2:
            missing_fields.append('filename')
        if not teaching_use or len(teaching_use.strip()) < 2:
            missing_fields.append('teaching_use')
        if not content or len(content.strip()) < 10:
            missing_fields.append('content')
        
        if missing_fields:
            missing_weight = sum(weights[field] for field in missing_fields)
            available_fields = [f for f in weights.keys() if f not in missing_fields]
            
            if available_fields:
                extra_per_field = missing_weight / len(available_fields)
                for field in available_fields:
                    weights[field] += extra_per_field
                
                for field in missing_fields:
                    weights[field] = 0.0
        
        # 策略2：根据查询意图调整权重
        query_intent = self._analyze_query_intent(query)
        
        if query_intent == 'specific_filename':
            weights['filename'] = min(0.6, weights['filename'] + 0.2)
            weights['content'] = max(0.1, weights['content'] - 0.1)
            weights['teaching_use'] = max(0.1, weights['teaching_use'] - 0.1)
        
        elif query_intent == 'specific_teaching_use':
            weights['teaching_use'] = min(0.5, weights['teaching_use'] + 0.2)
            weights['filename'] = max(0.1, weights['filename'] - 0.1)
            weights['content'] = max(0.2, weights['content'] - 0.1)
        
        elif query_intent == 'content_focused':
            weights['content'] = min(0.7, weights['content'] + 0.2)
            weights['filename'] = max(0.1, weights['filename'] - 0.1)
            weights['teaching_use'] = max(0.1, weights['teaching_use'] - 0.1)
        
        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _score_filename(self, filename: str, core_theme: str, query: str) -> float:
        """文件名字段评分 - 改进版：强化核心主题匹配"""
        if not filename:
            return 0.0
        
        score = 0.0
        has_core_theme_match = False  # 标记是否匹配到核心主题
        
        # 策略1：核心主题直接匹配（最高优先级）
        if core_theme:
            themes = [t.strip() for t in core_theme.split(',') if t.strip()]
            for theme in themes:
                # 精确匹配（单词边界）
                pattern = r'\b' + re.escape(theme) + r'\b'
                if re.search(pattern, filename, re.IGNORECASE):
                    score = max(score, 0.8)  # 从0.6提升到0.8
                    has_core_theme_match = True
                    break
                
                # 模糊匹配
                if theme in filename:
                    partial_score = 0.6 * (len(theme) / len(filename))
                    score = max(score, partial_score)
                    has_core_theme_match = True
        
        # 策略2：如果没有核心主题匹配，检查配置的关键词
        if not has_core_theme_match and core_theme:
            try:
                from app.config.dynamic_config_loader import DynamicConfigLoader
                config_loader = DynamicConfigLoader()
                
                themes = [t.strip() for t in core_theme.split(',') if t.strip()]
                for theme in themes:
                    theme_info = config_loader.get_knowledge_hierarchy().get(theme, {})
                    keywords = theme_info.get('keywords', [])
                    
                    # 只使用与核心主题高度相关的关键词（前3个）
                    high_priority_keywords = keywords[:3] if len(keywords) > 3 else keywords
                    
                    for keyword in high_priority_keywords:
                        if keyword in filename:
                            score = max(score, 0.5)  # 关键词匹配最高0.5
                            break
                    
                    if score >= 0.5:
                        break
            except:
                pass
        
        # 策略3：查询关键词匹配（辅助）
        if query:
            query_keywords = self._extract_meaningful_keywords(query)
            # 过滤掉通用词，只保留有意义的词
            meaningful_query_keywords = [kw for kw in query_keywords if kw not in ['课件', 'PPT', '幻灯片']]
            
            if meaningful_query_keywords:
                matched = sum(1 for kw in meaningful_query_keywords if kw.lower() in filename.lower())
                if matched > 0:
                    query_score = 0.2 * min(1.0, matched / max(1, len(meaningful_query_keywords)))
                    score += query_score
        
        # 策略4：如果完全没有核心主题相关匹配，给予惩罚
        if not has_core_theme_match and score < 0.3:
            # 文件名中没有任何核心主题相关的词，大幅降低分数
            score = score * 0.3  # 降至原来的30%
        
        return min(1.0, score)
    
    def _score_teaching_use(self, teaching_use: str, query: str) -> float:
        """教学用途字段评分 - V43.0改进版：实施智能降级策略"""
        if not teaching_use or len(teaching_use.strip()) < 2:
            return 0.15  # 空或太短，给很低的基础分
        
        score = 0.0
        
        # 用户意图匹配
        user_intent = self._extract_teaching_intent_from_query(query)
        
        if user_intent:
            # V43.1改进：定义降级优先级（允许最终降级到新授课）
            # 复习课 -> 练习课/习题课 -> 新授课
            fallback_priority = {
                '复习课': ['复习课', '练习课', '习题课', '新授课'],  # 允许最终降级到新授课
                '练习课': ['练习课', '习题课', '新授课'],  # 允许降级到新授课
                '习题课': ['习题课', '练习课', '新授课'],  # 允许降级到新授课
                '新授课': ['新授课'],  # 新授课不降级
            }
            
            intent_keywords_map = {
                '练习课': ['练习', '习题', '训练', '做题'],
                '复习课': ['复习', '总结', '回顾', '期末'],
                '新授课': ['新授', '新课', '引入'],
                '习题课': ['习题', '练习', '题目']
            }
            
            # 获取当前意图的关键词
            target_keywords = intent_keywords_map.get(user_intent, [])
            matched = sum(1 for kw in target_keywords if kw in teaching_use)
            
            if matched > 0:
                # 完全匹配（如teaching_use就是"练习课课件"）
                if any(kw == teaching_use for kw in target_keywords):
                    score = 0.8  # 从0.6提升到0.8
                else:
                    # 部分匹配
                    match_ratio = matched / len(target_keywords)
                    score = 0.5 + 0.3 * match_ratio  # 0.5-0.8区间
            else:
                # V43.1改进：检查是否匹配降级目标
                fallback_targets = fallback_priority.get(user_intent, [])
                is_fallback_match = any(fallback in teaching_use for fallback in fallback_targets)
                
                if is_fallback_match:
                    # 匹配到降级目标，根据降级层级给予不同分数
                    if user_intent == '复习课' and '新授课' in teaching_use:
                        # 复习课 -> 新授课（最远降级），给予较低分数
                        score = 0.3
                    elif user_intent in ['练习课', '习题课'] and '新授课' in teaching_use:
                        # 练习/习题课 -> 新授课（次远降级）
                        score = 0.35
                    else:
                        # 其他降级情况（如复习->练习）
                        score = 0.4
                else:
                    # 用户有明确意图，但课件用途不匹配且不满足降级条件 → 惩罚
                    # 例如：用户要复习课，但课件是实验课（如果有的话）
                    score = 0.1  # 很低的分数，几乎被过滤
        else:
            # 用户没有明确意图，给中等分数
            score = 0.5
        
        # 用途描述清晰度奖励
        if len(teaching_use) > 2 and len(teaching_use) < 20:
            score += 0.15  # 从0.2降低到0.15
        elif len(teaching_use) >= 20:
            score += 0.2  # 从0.3降低到0.2
        else:
            score += 0.05  # 从0.1降低到0.05
        
        return min(1.0, score)
    
    def _score_content(
        self, 
        content: str, 
        core_theme: str, 
        query: str,
        metadata: Dict
    ) -> float:
        """内容字段评分"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        score = 0.0
        
        # 知识点覆盖度
        knowledge_score = self._evaluate_knowledge_coverage(content, core_theme, metadata)
        score += knowledge_score * 0.35
        
        # 内容丰富度
        richness_score = self._evaluate_content_richness(content)
        score += richness_score * 0.30
        
        # 结构完整性
        structure_score = self._evaluate_structure_completeness(content)
        score += structure_score * 0.20
        
        # 查询相关性
        relevance_score = self._evaluate_query_relevance(content, query)
        score += relevance_score * 0.15
        
        return min(1.0, score)
    
    def _evaluate_knowledge_coverage(self, content: str, core_theme: str, metadata: Dict) -> float:
        """评估知识点覆盖度"""
        if not core_theme:
            return 0.5
        
        themes = [t.strip() for t in core_theme.split(',') if t.strip()]
        coverage_scores = []
        
        for theme in themes:
            if theme in content:
                coverage_scores.append(1.0)
                continue
            
            try:
                from app.config.dynamic_config_loader import DynamicConfigLoader
                config_loader = DynamicConfigLoader()
                theme_info = config_loader.get_knowledge_hierarchy().get(theme, {})
                keywords = theme_info.get('keywords', [])
                
                if keywords:
                    matched = sum(1 for kw in keywords if kw in content)
                    coverage_scores.append(min(1.0, matched / max(1, len(keywords))))
                else:
                    coverage_scores.append(0.3)
            except:
                coverage_scores.append(0.3)
        
        return sum(coverage_scores) / max(1, len(coverage_scores))
    
    def _evaluate_content_richness(self, content: str) -> float:
        """评估内容丰富度 - 改进版：不单纯依赖长度，考虑信息密度"""
        if not content or len(content.strip()) < 5:
            return 0.0
        
        score = 0.0
        
        # 策略1：长度评分（降低阈值，更宽容）
        length = len(content)
        if length > 2000:
            score += 0.25  # 从0.3降低到0.25
        elif length > 500:
            score += 0.20  # 从0.25降低到0.20
        elif length > 100:
            score += 0.15  # 新增100-500区间
        elif length > 20:
            score += 0.10  # 新增20-100区间（标题式课件）
        else:
            score += 0.05  # 极短内容也给基础分
        
        # 教学环节完整性
        teaching_sections = {
            '导入': ['导入', '引入', '情境'],
            '新知': ['讲解', '概念', '定义', '性质'],
            '例题': ['例题', '示例', '典例'],
            '练习': ['练习', '习题', '训练'],
            '总结': ['总结', '小结', '归纳'],
            '作业': ['作业', '课后']
        }
        
        matched_sections = 0
        for section, keywords in teaching_sections.items():
            if any(kw in content for kw in keywords):
                matched_sections += 1
        
        # 策略2：教学环节评分（降低要求，更灵活）
        if matched_sections >= 4:
            score += 0.25  # 从0.3降低到0.25
        elif matched_sections >= 2:
            score += 0.15  # 从0.2降低到0.15
        elif matched_sections >= 1:
            score += 0.08  # 新增：至少有1个环节就给分
        
        # 策略3：信息密度评估（新增）
        # 对于短内容，如果包含关键词，说明信息密度高
        if length < 100 and length > 10:
            # 计算关键词密度
            keyword_density = self._calculate_keyword_density(content)
            if keyword_density > 0.3:  # 30%以上是关键词
                score += 0.15  # 高密度短内容给予奖励
            elif keyword_density > 0.1:
                score += 0.08
        
        return min(1.0, score)
    
    def _evaluate_structure_completeness(self, content: str) -> float:
        """评估结构完整性"""
        score = 0.0
        
        if re.search(r'[一二三四五六七八九十]、|第[一二三四五六七八九十\d]+章', content):
            score += 0.4
        
        if content.count('\n') > 15:
            score += 0.3
        elif content.count('\n') > 8:
            score += 0.2
        
        if any(marker in content for marker in ['一、', '二、', '1.', '2.']):
            score += 0.3
        
        return min(1.0, score)
    
    def _evaluate_query_relevance(self, content: str, query: str) -> float:
        """评估内容与查询的相关性"""
        if not query:
            return 0.5
        
        query_terms = self._extract_meaningful_keywords(query)
        if not query_terms:
            return 0.5
        
        matched = sum(1 for term in query_terms if term in content)
        return min(1.0, matched / max(1, len(query_terms)))
    
    def _calculate_threshold(self, query: str, core_theme: str) -> float:
        """动态计算展示阈值"""
        base_threshold = 0.15
        
        if core_theme and len(core_theme) > 3:
            base_threshold += 0.05
        
        if any(kw in query for kw in ['课件', 'PPT', '幻灯片']):
            base_threshold += 0.03
        
        if any(kw in query for kw in ['练习课', '复习课', '新授课']):
            base_threshold += 0.03
        
        return min(0.30, base_threshold)
    
    def _analyze_query_intent(self, query: str) -> str:
        """分析查询意图类型"""
        if any(kw in query for kw in ['名为', '叫做', '文件名']):
            return 'specific_filename'
        elif any(kw in query for kw in ['练习课', '复习课', '新授课']):
            return 'specific_teaching_use'
        elif any(kw in query for kw in ['包含', '有...的', '带有']):
            return 'content_focused'
        else:
            return 'general'
    
    def _extract_teaching_intent_from_query(self, query: str) -> Optional[str]:
        """从查询中提取教学意图"""
        if any(kw in query for kw in ['练习', '习题', '做题']):
            return '练习课'
        elif any(kw in query for kw in ['复习', '总结', '期末']):
            return '复习课'
        elif any(kw in query for kw in ['预习', '新课', '新授']):
            return '新授课'
        return None
    
    def _extract_meaningful_keywords(self, query: str) -> List[str]:
        """提取查询中有意义的关键词"""
        stop_words = ['给我', '找', '搜索', '有没有', '需要', '想要', '请', '帮我']
        terms = re.split(r'[\s,，。；、！？]+', query)
        keywords = [term for term in terms if len(term) > 1 and term not in stop_words]
        return keywords
    
    def _calculate_keyword_density(self, content: str) -> float:
        """计算内容的关键词密度 - 用于评估短内容的信息价值"""
        if not content or len(content.strip()) < 5:
            return 0.0
        
        # 数学教学相关关键词
        math_keywords = [
            '棱柱', '棱锥', '棱台', '圆柱', '圆锥', '圆台', '球',
            '函数', '导数', '积分', '概率', '统计', '向量',
            '定义', '性质', '定理', '公式', '例题', '练习',
            '导入', '讲解', '总结', '作业', '课时'
        ]
        
        content_lower = content.lower()
        matched_count = sum(1 for kw in math_keywords if kw in content_lower)
        total_keywords = len(math_keywords)
        
        return matched_count / total_keywords if total_keywords > 0 else 0.0


# 全局单例
_courseware_evaluator = None

def get_courseware_evaluator() -> CoursewareEvaluator:
    """获取课件评估器单例"""
    global _courseware_evaluator
    if _courseware_evaluator is None:
        _courseware_evaluator = CoursewareEvaluator()
    return _courseware_evaluator
