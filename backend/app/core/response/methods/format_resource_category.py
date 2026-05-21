import logging
from .._shared import *

logger = logging.getLogger(__name__)


class _FormatResourceCategoryMixin:
    def _format_resource_category(
        self,
        category_name: str,
        resources: List[Dict[str, Any]],
        icon: str,
        scenario: str = "search",
        state: Any = None
    ) -> str:
        """
        格式化资源分类 - 改进版
        增强结果呈现，标注资源匹配的主题信息

        Args:
            category_name: 分类名称
            resources: 资源列表
            icon: 图标
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景

        Returns:
            格式化后的文本
        """
        logger.warning(f"\n{'='*80}")
        logger.warning(f"🔍 [格式化入口] category_name='{category_name}', resources_count={len(resources)}")
        logger.warning(f"{'='*80}\n")
        
        response_parts = [f"\n【{category_name}】\n"]

        if not resources:
            logger.warning(f"⚠️ [格式化调试] {category_name} 资源列表为空")
            return "\n".join(response_parts)
        
        logger.warning(f"🔍 [格式化调试] {category_name} 原始资源数: {len(resources)}")
        for i, res in enumerate(resources):
            logger.warning(f"   [{i+1}] title='{res.get('title', '')[:30]}', has_title={bool(res.get('title'))}, has_content={bool(res.get('content'))}, has_source={bool(res.get('source'))}, relevance={res.get('relevance', 0):.3f}")

        # 过滤掉相似度过低的资源
        filtered_resources = self._filter_by_relevance(resources, state, category_name)
        logger.warning(f"🔍 [格式化调试] {category_name} 过滤后资源数: {len(filtered_resources)}")

        # 检测是否为分别查询
        user_input = self._get_state_value(state, "user_input", "")
        print(f"[DEBUG] user_input = '{user_input}'")
        is_separate_query = any(keyword in user_input for keyword in ["分别", "各自", "分开"])
        print(f"[DEBUG] is_separate_query = {is_separate_query}")
        
        # 检测是否为多主题查询
        has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及", "、"])
        print(f"[DEBUG] has_multi_themes = {has_multi_themes}")
        print(f"[DEBUG] filtered_resources count = {len(filtered_resources)}")
        
        if is_separate_query and has_multi_themes:
            # 分别查询模式：按主题分组显示资源
            print(f"📋 检测到分别查询，按主题分组显示资源")
            
            # 按主题分组资源
            theme_resources = {}
            for resource in filtered_resources:
                # 获取资源匹配的主题
                matched_themes = resource.get("matched_themes", [])
                print(f"[DEBUG] resource title={resource.get('meta', {}).get('title', 'unknown')}, matched_themes={matched_themes}")
                if not matched_themes:
                    print(f"[DEBUG] resource has no matched_themes, skipping")
                    continue
                
                for theme in matched_themes:
                    if theme not in theme_resources:
                        theme_resources[theme] = []
                    theme_resources[theme].append(resource)
            
            # 对每个主题的资源进行排序
            for theme, theme_items in theme_resources.items():
                # 按相关性排序
                theme_items.sort(key=lambda x: (-x.get('relevance', 0), -x.get('is_core_match', False)))
                
                # 显示该主题的资源
                response_parts.append(f"\n📋 【主题：{theme}】（{len(theme_items)}个）：\n")
                
                # 每个主题最多显示5个资源
                for resource in theme_items[:5]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        else:
            # 普通查询模式：按优先级分组显示资源
            
            # ========== 安全去重（不影响准确性） ==========
            filtered_resources = self._remove_duplicate_resources(filtered_resources)
            
            # V10.0：基于全局综合得分排序
            globally_sorted_resources = self._sort_resources_globally(filtered_resources)
            
            # V10.0：使用用户反馈优化排序
            feedback_optimized_resources = self._optimize_ranking_with_feedback(globally_sorted_resources)
            
            # V11.3：直接使用决策中心的优先级层级进行分类，不再使用动态聚类
            # 按优先级层级分组
            priority_groups = {
                4: [],  # 核心主题匹配
                3: [],  # 相关主题匹配
                2: [],  # 扩展主题匹配
                1: [],  # 提及主题匹配
                0: []   # 无匹配
            }
            
            for resource in feedback_optimized_resources:
                priority_level = resource.get("priority_level", 0)
                priority_groups[priority_level].append(resource)
            
            # 按优先级顺序显示资源
            priority_names = {
                4: "核心主题匹配",
                3: "相关主题匹配",
                2: "扩展主题匹配",
                1: "提及主题匹配",
                0: "其他资源"
            }
            
            priority_icons = {
                4: "⭐",
                3: "📌",
                2: "📎",
                1: "💡",
                0: "📄"
            }
            
            for level in [4, 3, 2, 1, 0]:
                if priority_groups[level]:
                    # 教学大纲只显示核心主题匹配（priority_level=4），跳过其他级别
                    is_syllabus = category_name == "教学大纲" or any(
                        r.get("resource_type", "") == "syllabus" or "syllabus" in str(r.get("resource_type", "")).lower() 
                        for r in priority_groups[level]
                    )
                    if is_syllabus and level != 4:
                        continue
                    
                    icon_emoji = priority_icons[level]
                    category_label = priority_names[level]
                    response_parts.append(f"\n{icon_emoji} 【{category_label}】（{len(priority_groups[level])}个）：\n")
                    for resource in priority_groups[level][:self.max_display_per_group]:
                        self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)

        # 如果过滤掉了资源，添加提示
        if len(filtered_resources) < len(resources):
            filtered_count = len(resources) - len(filtered_resources)
            response_parts.append(f"\n💡 已隐藏{filtered_count}条相似度较低的资源")

        return "\n".join(response_parts)
    
    def _remove_duplicate_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        安全去重 - 仅基于唯一标识，不影响准确性
        
        Args:
            resources: 资源列表
            
        Returns:
            去重后的资源列表（保证不丢失有效资源）
        """
        if not resources:
            return resources
        
        seen_identities = set()
        unique_resources = []
        
        for resource in resources:
            resource_type = resource.get('resource_type', '')
            is_syllabus = resource_type == 'syllabus' or 'syllabus' in str(resource_type).lower()
            
            # 教学大纲资源：使用主题+章节作为唯一标识（避免同一章节在不同主题中被误判为重复）
            if is_syllabus:
                topic = resource.get('topic', '')
                chapter = resource.get('chapter', '')
                identity = f"syllabus_{topic}_{chapter}"
            else:
                identity = self._get_resource_identity(resource)
            
            if identity:
                if identity not in seen_identities:
                    seen_identities.add(identity)
                    unique_resources.append(resource)
            else:
                unique_resources.append(resource)
        
        if len(unique_resources) < len(resources):
            print(f"   📊 安全去重完成：原始 {len(resources)} 条，去重后 {len(unique_resources)} 条")
        
        return unique_resources
    
    def _get_resource_identity(self, resource: Dict[str, Any]) -> str:
        """
        获取资源的唯一标识（安全版本）
        
        优先使用以下字段生成唯一标识：
        1. id - 数据库ID
        2. source_file - 源文件路径
        3. filename - 文件名
        4. url/link - 资源链接
        5. question - 题干内容（用于区分同一文件的不同习题）
        
        Args:
            resource: 资源字典
            
        Returns:
            资源唯一标识字符串，如果无法生成则返回空字符串
        """
        if not isinstance(resource, dict):
            return ""
        
        id_fields = ["id", "source_file", "filename", "url", "link", "source"]
        
        # 【V65.3改进】先获取基础ID
        base_id = ""
        for field in id_fields:
            value = resource.get(field, "")
            if value:
                base_id = str(value).strip()
                break
        
        # 如果没有基础ID，尝试从meta中获取
        if not base_id:
            meta = resource.get('meta', {})
            if isinstance(meta, dict):
                for field in id_fields:
                    value = meta.get(field, "")
                    if value:
                        base_id = str(value).strip()
                        break
        
        # 【V65.3改进】如果是习题资源，添加question字段以区分同一文件的不同习题
        question = resource.get('question', '')
        if not question:
            # 尝试从metadata中提取题干
            metadata = resource.get('metadata', {})
            if isinstance(metadata, dict):
                question = metadata.get('题干', '')
        
        # 如果有题干，将其哈希值加入ID以确保不同习题有不同ID
        if question and base_id:
            return f"{base_id} | {hash(question)}"
        elif base_id:
            return base_id
        
        # 如果仍然没有ID，使用document或content
        document = resource.get('document', '') or resource.get('content', '')
        if document:
            return str(document)[:200].strip()
        
        return ""
