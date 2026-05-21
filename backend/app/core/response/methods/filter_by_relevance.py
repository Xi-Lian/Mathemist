import logging
from .._shared import *

logger = logging.getLogger(__name__)


class _FilterByRelevanceMixin:
    def _filter_by_relevance(self, resources: List[Dict[str, Any]], state: Any = None, category_name: str = '') -> List[Dict[str, Any]]:
        """
        V10.0：平滑的渐进式展示，替代“悬崖式”截断
            
        改进：
        - 移除40%下跌截断机制
        - 基于分级阈值的平滑过滤
        - 保留更多有价值的资源
        - V315.0修复：多主题查询时确保每个主题都有公平的资源展示机会
            
        Args:
            resources: 资源列表
            
        Returns:
            过滤后的资源列表
        """
        logger.warning(f"🔍 [过滤调试] 开始过滤，原始资源数: {len(resources)}")
        if not resources:
            return []
            
        # 打印所有资源的详细信息
        for i, res in enumerate(resources):
            logger.warning(f"   [{i+1}] title='{res.get('title', '')[:30]}', relevance={res.get('relevance', 0):.3f}, is_core_match={res.get('is_core_match', False)}, priority_level={res.get('priority_level', 0)}, matched_themes={res.get('matched_themes', [])}")
        
        # 分级展示阈值
        thresholds = {
            'core': 0.7,    # 核心资源 - V316.0降低阈值，展示更多核心资源
            'high': 0.5,    # 高相关资源 - V316.0降低阈值
            'medium': 0.3,  # 中等相关资源 - V316.0降低阈值
            'low': 0.05     # 低相关资源 - V316.0降低阈值，确保更多资源不被过滤
        }
        
        # 每个级别的最大展示数量
        max_counts = {
            'core': 10,    # 核心资源最多10个
            'high': 15,    # 高相关资源最多15个
            'medium': 10,  # 中等相关资源最多10个
            'low': 5       # 低相关资源最多5个
        }
        
        # V315.0改进：先按主题分组，确保每个主题都有公平的资源展示机会
        # 优化：使用集合进行快速去重检查
        theme_resources = {}
        theme_seen = {}  # 记录每个主题下已添加的资源ID
        
        def get_resource_id(resource):
            """获取资源唯一标识，用于去重"""
            # 【V65.3改进】优先使用question字段区分同一文件的不同习题
            question = resource.get('question', '')
            if not question:
                # 尝试从metadata中提取题干
                metadata = resource.get('metadata', {})
                if isinstance(metadata, dict):
                    question = metadata.get('题干', '')
            
            # 如果有题干，将其加入ID以确保不同习题有不同ID
            base_id = resource.get('id', resource.get('filename', resource.get('source', str(id(resource)))))
            if question:
                return f"{base_id} | {hash(question)}"
            return base_id
        
        for resource in resources:
            resource_id = get_resource_id(resource)
            matched_themes = resource.get('matched_themes', [])
            if not matched_themes:
                # 没有匹配主题的资源单独处理
                if 'unknown' not in theme_resources:
                    theme_resources['unknown'] = []
                    theme_seen['unknown'] = set()
                if resource_id not in theme_seen['unknown']:
                    theme_seen['unknown'].add(resource_id)
                    theme_resources['unknown'].append(resource)
            else:
                for theme in matched_themes:
                    if theme not in theme_resources:
                        theme_resources[theme] = []
                        theme_seen[theme] = set()
                    if resource_id not in theme_seen[theme]:
                        theme_seen[theme].add(resource_id)
                        theme_resources[theme].append(resource)
        
        print(f"[DEBUG] V315.0 按主题分组: {list(theme_resources.keys())}")
        
        # V43.2改进：检测用户是否有明确的教学用途意图
        user_input = self._get_state_value(state, "user_input", "") if state else ""
        logger.warning(f"[过滤调试] user_input='{user_input}'")
        user_intent = None
        if user_input:
            if '复习' in user_input or '总结' in user_input or '回顾' in user_input:
                user_intent = '复习课'
            elif '练习' in user_input or '习题' in user_input or '训练' in user_input:
                user_intent = '练习课'
            elif '新授' in user_input or '新课' in user_input:
                user_intent = '新授课'
        
        logger.warning(f"[过滤调试] user_intent={user_intent}")
        
        # V43.2改进：如果用户有明确意图，实施教学用途降级过滤
        # 但是，对于习题资源，不应该应用降级过滤，因为习题本身就是用于练习的
        if user_intent and category_name != '习题资源':
            logger.warning(f"[过滤调试] V43.2 检测到用户意图: {user_intent}，实施降级过滤")
            filtered_resources = self._apply_teaching_use_fallback_filter(resources, user_intent)
            logger.warning(f"[过滤调试] V43.2 降级过滤后资源数量: {len(filtered_resources)}")
            
            # 【V63.7改进】对过滤后的资源排序：优先使用overall_score（方案A的V63.6排序结果），否则使用relevance
            filtered_resources.sort(
                key=lambda x: (-
                    x.get('overall_score', x.get('relevance', 0)),  # 【V63.7改进】优先使用overall_score
                    -x.get('is_core_match', False),
                    -x.get('priority_level', 0),
                    -x.get('matched_theme_count', 0)
                )
            )
            
            return filtered_resources
        
        # 对每个主题的资源分别进行分级过滤
        filtered_resources = []
        logger.warning(f"[过滤调试] 开始按主题分组过滤，主题数: {len(theme_resources)}")
        
        for theme, theme_items in theme_resources.items():
            logger.warning(f"[过滤调试] V315.0 处理主题 '{theme}'，资源数量: {len(theme_items)}")
            
            # 【V63.7改进】对该主题的资源排序：优先使用overall_score（方案A的V63.6排序结果），否则使用relevance
            sorted_items = sorted(
                theme_items,
                key=lambda x: (-
                    x.get('overall_score', x.get('relevance', 0)),  # 【V63.7改进】优先使用overall_score
                    -x.get('is_core_match', False),
                    -x.get('matched_theme_count', 0)
                )
            )
            
            # 为每个主题分配公平的配额（按主题数量均分）
            num_themes = max(len(theme_resources), 1)
            theme_max_counts = {
                'core': max(1, max_counts['core'] // num_themes),
                'high': max(2, max_counts['high'] // num_themes),
                'medium': max(2, max_counts['medium'] // num_themes),
                'low': max(1, max_counts['low'] // num_themes)
            }
            
            theme_level_counts = {
                'core': 0, 'high': 0, 'medium': 0, 'low': 0
            }
            
            for resource in sorted_items:
                relevance = resource.get('relevance', 0)
                is_core_match = resource.get('is_core_match', False)
                priority_level = resource.get('priority_level', 0)
                matched_theme_count = resource.get('matched_theme_count', 0)
                title = resource.get('meta', {}).get('title', resource.get('title', '未知'))[:30]

                # 确定资源级别
                if relevance >= thresholds['core'] or is_core_match:
                    level = 'core'
                elif relevance >= thresholds['high'] or priority_level >= 3:
                    level = 'high'
                elif relevance >= thresholds['medium'] or priority_level >= 2:
                    level = 'medium'
                elif relevance >= thresholds['low'] or priority_level >= 1 or matched_theme_count > 0:
                    level = 'low'
                else:
                    if matched_theme_count > 0:
                        level = 'low'
                    else:
                        logger.warning(f"    ⚠️ 资源 '{title}' 被过滤：relevance={relevance}")
                        continue

                logger.warning(f"    [调试] 资源 '{title}' 判定为级别 '{level}': relevance={relevance}, is_core_match={is_core_match}, priority_level={priority_level}, theme_max_counts[level]={theme_max_counts[level]}, theme_level_counts[level]={theme_level_counts[level]}")
                
                # 检查该级别的资源数量是否达到该主题的配额
                if theme_level_counts[level] < theme_max_counts[level]:
                    filtered_resources.append(resource)
                    theme_level_counts[level] += 1
                    logger.warning(f"    ✅ 主题'{theme}' 资源 '{title}' 进入级别 '{level}'")
                else:
                    logger.warning(f"    ❌ 主题'{theme}' 资源 '{title}' 级别 '{level}' 配额已满（{theme_level_counts[level]}/{theme_max_counts[level]}）")
        
        # 【V63.7改进】最后排序：优先使用overall_score（方案A的V63.6排序结果），否则使用relevance
        filtered_resources.sort(
            key=lambda x: (-
                x.get('overall_score', x.get('relevance', 0)),  # 【V63.7改进】优先使用overall_score
                -x.get('is_core_match', False),
                -x.get('priority_level', 0),
                -x.get('matched_theme_count', 0)
            )
        )
        
        logger.warning(f"[过滤调试] V315.0 过滤后资源总数: {len(filtered_resources)}")
        return filtered_resources
    
    def _apply_teaching_use_fallback_filter(self, resources: List[Dict[str, Any]], user_intent: str) -> List[Dict[str, Any]]:
        """
        V43.2：实施教学用途降级过滤
        
        规则：
        1. 优先返回复习课课件
        2. 如果没有复习课，但有练习课 → 只返回练习课（不返回新授课）
        3. 如果复习课和练习课都没有 → 才返回新授课
        
        Args:
            resources: 资源列表
            user_intent: 用户意图（复习课/练习课/新授课）
        
        Returns:
            过滤后的资源列表
        """
        if not resources:
            return []
        
        # 定义降级优先级
        fallback_priority = {
            '复习课': ['复习课', '练习课', '习题课', '新授课'],
            '练习课': ['练习课', '习题课', '新授课'],
            '习题课': ['习题课', '练习课', '新授课'],
            '新授课': ['新授课'],
        }
        
        # 获取允许的降级目标
        allowed_targets = fallback_priority.get(user_intent, [])
        
        # 按优先级分组资源
        priority_groups = {}
        for target in allowed_targets:
            priority_groups[target] = []
        
        for resource in resources:
            teaching_use = resource.get('teaching_use', '')
            logger.warning(f"    [V43.2调试] 资源 title='{resource.get('title', '')[:30]}', teaching_use='{teaching_use}'")
            
            # 检查资源属于哪个优先级
            for target in allowed_targets:
                if target in teaching_use:
                    priority_groups[target].append(resource)
                    logger.warning(f"    [V43.2调试] 资源匹配到 '{target}'")
                    break
        
        # 按优先级顺序选择资源
        for target in allowed_targets:
            logger.warning(f"    [V43.2调试] 检查优先级 '{target}'，资源数: {len(priority_groups[target])}")
            if priority_groups[target]:
                logger.warning(f"[DEBUG] V43.2 找到 {target} 资源 {len(priority_groups[target])} 个，使用此级别")
                return priority_groups[target]
        
        # 如果没有任何匹配的资源，返回空列表
        logger.warning(f"[DEBUG] V43.2 未找到任何符合降级策略的资源，allowed_targets={allowed_targets}")
        return []
