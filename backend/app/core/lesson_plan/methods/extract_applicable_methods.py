from .._shared import *


class _ExtractApplicableMethodsMixin:
    def _extract_applicable_methods(self, theory_name: str, core_view: str) -> str:
        """
        动态提取理论适用的教学方法（基于理论名称和核心观点的关键词分析）
        
        Args:
            theory_name: 理论名称
            core_view: 理论核心观点
        
        Returns:
            适用的教学方法
        """
        import re
        
        # 从理论名称和核心观点中提取关键词
        combined_text = theory_name + " " + core_view
        
        # 定义教学方法关键词
        method_keywords = {
            "讲授式": ["讲授", "讲解", "传递", "灌输", "呈现", "示范", "演示"],
            "探究式": ["探究", "发现", "探索", "研究", "实验", "调查", "自主", "建构"],
            "合作学习": ["合作", "协作", "小组", "团队", "同伴", "互动", "交流"],
            "自主学习": ["自主", "独立", "自我", "元认知", "监控", "反思"],
            "翻转课堂": ["翻转", "课前", "课后", "预习", "复习"],
            "项目式学习": ["项目", "实践", "应用", "综合", "真实情境"],
            "混合式教学": ["混合", "多种", "多元", "综合", "多样化"]
        }
        
        # 匹配教学方法
        matched_methods = []
        for method, keywords in method_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched_methods.append(method)
                    break
        
        # 如果没有匹配到，返回"所有教学方法"
        if not matched_methods:
            return "所有教学方法"
        
        # 去重
        matched_methods = list(set(matched_methods))
        
        # 如果匹配到多个方法，返回前3个
        if len(matched_methods) > 3:
            matched_methods = matched_methods[:3]
        
        return "、".join(matched_methods)
