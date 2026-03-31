from .._shared import *


class _ClassifyQueryTypeMixin:
    def _classify_query_type(self, original_query: str, intent: Dict[str, Any], core_concepts: List[str]) -> str:
        """
        对查询进行分类
        
        查询类型：
        - 概念型："什么是指数函数" "导数的定义"
        - 方法型："怎么解一元二次方程" "求导步骤"
        - 资源型："三角函数课件" "数列教案"
        - 问题型："这道题怎么做" "某年高考题"
        - 混合型：多个特征同时出现
        """
        type_scores = {
            "concept": 0,
            "method": 0,
            "resource": 0,
            "problem": 0
        }
        
        concept_patterns = ["什么是", "是什么", "定义", "概念", "介绍", "讲解", "说明"]
        for pattern in concept_patterns:
            if pattern in original_query:
                type_scores["concept"] += 2
                break
        
        method_patterns = ["怎么", "如何", "怎样", "步骤", "方法", "解法", "技巧", "规律", "推导", "证明"]
        for pattern in method_patterns:
            if pattern in original_query:
                type_scores["method"] += 2
                break
        
        if intent["resource_types"]:
            type_scores["resource"] += 3
        
        problem_patterns = ["题怎么做", "怎么做题", "这道题", "解题", "题目", "例题", "高考题", "中考题", "练习题"]
        for pattern in problem_patterns:
            if pattern in original_query:
                type_scores["problem"] += 2
                break
        
        max_score = max(type_scores.values())
        
        high_score_types = [t for t, s in type_scores.items() if s >= 2]
        if len(high_score_types) >= 2:
            return "混合型"
        
        if max_score == 0:
            if core_concepts:
                return "概念型"
            else:
                return "混合型"
        
        type_map = {
            "concept": "概念型",
            "method": "方法型",
            "resource": "资源型",
            "problem": "问题型"
        }
        return type_map[max(type_scores, key=type_scores.get)]
