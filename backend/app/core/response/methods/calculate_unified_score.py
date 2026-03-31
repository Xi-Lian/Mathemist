from .._shared import *


class _CalculateUnifiedScoreMixin:
    def _calculate_unified_score(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        V11.0：统一决策中心 - 综合所有评估信息计算最终得分
        
        决策规则：
        1. 优先级层级（决定基础分区间）：
           - 精确匹配：0.90-1.00
           - 直接相关：0.75-0.89
           - 间接相关：0.60-0.74
           - 背景提及：0.40-0.59
        
        2. 在同一优先级内，综合以下因素调整分数：
           - 相关性分数（向量相似度）
           - 概念距离因子（层级关系）
           - 资源质量指标
           - 多维度评估指标
        
        Args:
            resource: 资源字典
            
        Returns:
            包含最终得分和决策信息的字典
        """
        # 提取关键信息
        match_level = resource.get("match_level", "none")
        is_core_match = resource.get("is_core_match", False)
        relevance = resource.get("relevance", resource.get("relevance_score", 0))
        
        # V11.2：提取多维度评估指标（使用0.0作为默认值，以反映真实的计算结果）
        resource_quality = resource.get("resource_quality", 0.0)
        content_completeness = resource.get("content_completeness", 0.0)
        teaching_value = resource.get("teaching_value", 0.0)
        comprehensiveness = resource.get("comprehensiveness", 0.0)
        
        # V11.2：提取概念层级信息（使用0.5作为默认值，表示中性）
        concept_hierarchy_factor = resource.get("concept_hierarchy_factor", 0.5)
        
        # ===== 第一步：确定优先级层级和基础分 =====
        # V11.1：修复优先级层级定义，与主题匹配器的输出保持一致
        if match_level == "core" or is_core_match:
            # 第一优先级：核心主题匹配（精确命中用户查询）
            priority_level = 4
            base_score_min = 0.90
            base_score_max = 1.00
            priority_name = "核心主题匹配"
        elif match_level == "related":
            # 第二优先级：相关主题匹配（同一概念的不同方面）
            priority_level = 3
            base_score_min = 0.75
            base_score_max = 0.89
            priority_name = "相关主题匹配"
        elif match_level == "extended":
            # 第三优先级：扩展主题匹配（同一领域的不同概念）
            priority_level = 2
            base_score_min = 0.60
            base_score_max = 0.74
            priority_name = "扩展主题匹配"
        elif match_level == "mentioned":
            # 第四优先级：提及主题匹配（仅作为背景提及）
            priority_level = 1
            base_score_min = 0.40
            base_score_max = 0.59
            priority_name = "提及主题匹配"
        else:
            # 无匹配
            priority_level = 0
            base_score_min = 0.0
            base_score_max = 0.39
            priority_name = "无匹配"
        
        # ===== 第二步：计算调整因子 =====
        # 相关性因子（在基础分区间内调整）
        relevance_factor = relevance * 0.3  # 贡献最多30%的调整
        
        # 概念距离因子（层级关系）
        hierarchy_adjustment = (concept_hierarchy_factor - 0.5) * 0.2  # 贡献±10%的调整
        
        # 资源质量因子
        quality_score = (
            resource_quality * 0.3 +
            content_completeness * 0.25 +
            teaching_value * 0.25 +
            comprehensiveness * 0.2
        )
        quality_factor = (quality_score - 0.5) * 0.2  # 贡献±10%的调整
        
        # ===== 第三步：计算最终得分 =====
        # 在基础分区间内进行调整
        score_range = base_score_max - base_score_min
        adjustment = (relevance_factor + hierarchy_adjustment + quality_factor) * score_range
        final_score = base_score_min + score_range * 0.5 + adjustment
        
        # 确保分数在合理范围内
        final_score = max(base_score_min, min(base_score_max, final_score))
        
        # ===== 第四步：记录决策信息 =====
        decision_info = {
            "priority_level": priority_level,
            "priority_name": priority_name,
            "base_score_range": [base_score_min, base_score_max],
            "relevance_factor": round(relevance_factor, 3),
            "hierarchy_adjustment": round(hierarchy_adjustment, 3),
            "quality_factor": round(quality_factor, 3),
            "final_score": round(final_score, 3)
        }
        
        return {
            "final_score": final_score,
            "priority_level": priority_level,
            "priority_name": priority_name,
            "decision_info": decision_info
        }
