from .._shared import *


class _ReclassifyByRelevanceMixin:
    def _reclassify_by_relevance(self, all_resources: List[Dict[str, Any]], core_theme: str = "") -> Dict[str, Any]:
        """
        按相关性重新分类资源（V8.1新增）
        V55.0改进：为每种资源类型单独计算阈值，避免组合查询时某些资源类型被过滤
        
        Args:
            all_resources: 已按相关性排序的所有资源列表
            core_theme: 核心主题
        
        Returns:
            分类后的资源字典（按相关性分组）
        """
        # 初始化分类
        classified = {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "exercise_resources": [],
            "visualization_examples": [],
            "general_resources": [],
            "courseware_resources": [],
            "lesson_case_resources": [],
            "ggb_resources": [],
            "syllabus_resources": [],
            "_hidden_resources": [],
            "_hidden_count": 0,
            "_total_count": 0
        }
        
        # V55.0改进：为每种资源类型单独计算阈值
        # 首先按资源类型分组
        resources_by_category = {}
        for resource in all_resources:
            category = resource.get("_category")
            
            # 如果没有_category属性，尝试从资源类型推断
            if not category:
                resource_type = resource.get('metadata', {}).get('resource_type', '')
                category_map = {
                    "lesson_plan": "lesson_plan_patterns",
                    "visualization": "visualization_examples",
                    "exercise": "exercise_resources",
                    "courseware": "courseware_resources",
                    "lesson_case": "lesson_case_resources",
                    "ggb": "ggb_resources",
                    "syllabus": "syllabus_resources",
                    "theory": "theory_resources"
                }
                category = category_map.get(resource_type, "theory_resources")
            
            if category not in resources_by_category:
                resources_by_category[category] = []
            resources_by_category[category].append(resource)
        
        # V55.0改进：为每种资源类型单独计算阈值
        # V61.0改进：提高阈值下限，确保资源相关性
        category_thresholds = {}
        for category, resources in resources_by_category.items():
            if resources:
                # 按相关性排序
                resources_sorted = sorted(resources, key=lambda x: -x.get('relevance', 0))
                max_relevance = resources_sorted[0].get('relevance', 0)
                
                # 根据最高相关性动态调整阈值
                if max_relevance > 0.80:
                    threshold = 0.60 * max_relevance
                elif max_relevance > 0.60:
                    threshold = 0.50 * max_relevance
                elif max_relevance > 0.40:
                    threshold = 0.40 * max_relevance
                elif max_relevance > 0.20:
                    threshold = 0.30 * max_relevance
                else:
                    threshold = 0.35 * max_relevance
                
                # V61.0改进：提高下限，确保资源相关性
                threshold = max(threshold, 0.30)
                
                category_thresholds[category] = threshold
                print(f"   📊 V55.0 {category}阈值：最高相关性{max_relevance:.1%}，阈值{threshold:.1%}")
        
        # V55.0改进：使用各自资源类型的阈值进行过滤
        for resource in all_resources:
            relevance = resource.get('relevance', 0)
            category = resource.get("_category")
            
            # 如果没有_category属性，尝试从资源类型推断
            if not category:
                resource_type = resource.get('metadata', {}).get('resource_type', '')
                category_map = {
                    "lesson_plan": "lesson_plan_patterns",
                    "visualization": "visualization_examples",
                    "exercise": "exercise_resources",
                    "courseware": "courseware_resources",
                    "lesson_case": "lesson_case_resources",
                    "ggb": "ggb_resources",
                    "syllabus": "syllabus_resources",
                    "theory": "theory_resources"
                }
                category = category_map.get(resource_type, "theory_resources")
            
            # 检查资源是否包含核心主题
            metadata = resource.get('metadata', {})
            content = resource.get('content', '') or metadata.get('content', '')
            title = metadata.get('title', '')
            
            # 检查资源是否包含与概率相关的关键词
            contains_probability_theme = False
            probability_keywords = ["概率", "概率的性质", "概率的基本性质"]
            for keyword in probability_keywords:
                if keyword in content or keyword in title or keyword in str(metadata):
                    contains_probability_theme = True
                    break
            
            contains_core_theme = core_theme and (core_theme in content or core_theme in title or core_theme in str(metadata))
            
            # 使用各自资源类型的阈值
            threshold = category_thresholds.get(category, 0.10)
            
            if relevance >= threshold or contains_core_theme or contains_probability_theme:
                if category in classified:
                    classified[category].append(resource)
                    if (contains_core_theme or contains_probability_theme) and relevance < threshold:
                        print(f"   ✅ 保留（包含核心主题）：'{title}' (相关性: {relevance:.2f} < {threshold:.2f})")
            else:
                # 低相关性资源放入隐藏资源
                classified["_hidden_resources"].append(resource)
        
        # 更新计数
        classified["_hidden_count"] = len(classified["_hidden_resources"])
        classified["_total_count"] = len(all_resources)
        
        total_kept = sum(len(resources) for key, resources in classified.items() 
                        if isinstance(resources, list) and not key.startswith('_'))
        print(f"   ✅ V55.0分类完成：保留{total_kept}个资源，隐藏{classified['_hidden_count']}个资源")
        
        return classified
