from .._shared import *


class _AdjustRetrievalCountMixin:
    def _adjust_retrieval_count(self, query: str, detected_intents: List[Dict[str, Any]], base_count: int, resource_types: List[str] = None) -> int:
        """
        根据检测到的意图动态调整检索数量
        
        Args:
            query: 用户查询
            detected_intents: 检测到的意图列表
            base_count: 基础检索数量
            
        Returns:
            调整后的检索数量
        """
        adjusted_count = base_count
        
        # 根据意图优先级调整数量
        if detected_intents:
            max_priority = max(i["priority"] for i in detected_intents)
            
            # V90.2修复：对于课件查询，使用更低的检索数量
            is_courseware_query = any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types))
            
            # 高优先级意图增加检索数量
            if max_priority >= 10:  # 证明题、应用题等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件高优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 700)
                    print(f"   🔍 V51.0高优先级意图: 增加检索数量到 {adjusted_count}")
            elif max_priority >= 9:  # 单调性、奇偶性等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件中等优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 600)
                    print(f"   🔍 V51.0中等优先级意图: 增加检索数量到 {adjusted_count}")
            elif max_priority >= 8:  # 难度、年级等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件普通优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 500)
                    print(f"   🔍 V51.0普通优先级意图: 增加检索数量到 {adjusted_count}")
        
        # 特殊处理：应用题和生活应用查询
        has_application_intent = any(i["name"] in ["application_problem", "trig_application", "quadratic_application"] for i in detected_intents)
        if has_application_intent:
            adjusted_count = max(adjusted_count, 800)
            print(f"   🔍 V51.0应用题查询: 进一步增加检索数量到 {adjusted_count}")
        
        # 特殊处理：组合查询（多个高优先级意图）
        high_priority_intents = [i for i in detected_intents if i["priority"] >= 9]
        # V90.1修复：对于课件查询，不要使用过高的检索数量
        is_courseware_query = any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types))
        if len(high_priority_intents) >= 2 and not is_courseware_query:
            adjusted_count = max(adjusted_count, 900)
            print(f"   🔍 V51.0组合查询: 进一步增加检索数量到 {adjusted_count}")
        elif len(high_priority_intents) >= 2 and is_courseware_query:
            # 对于课件查询，使用较低的检索数量
            # V90.2修复：进一步降低课件检索数量，避免ChromaDB错误
            adjusted_count = max(adjusted_count, 200)
            print(f"   🔍 V90.2课件组合查询: 使用检索数量 {adjusted_count}")
        
        # V54.0改进：对于教案/课件/教学大纲等非习题资源的查询，增加检索数量
        # 因为这些资源在向量空间中的分布与习题资源不同，需要检索更多结果才能找到相关资源
        non_exercise_keywords = ['教案', '课件', '教学大纲', '课例', '教学设计']
        print(f"   🔍 V54.0调试 - 查询: {query}, non_exercise_keywords: {non_exercise_keywords}, resource_types: {resource_types}")
        
        # V67.0改进：检查resource_types参数，而不仅仅是查询文本
        is_non_exercise_query = False
        if any(keyword in query for keyword in non_exercise_keywords):
            is_non_exercise_query = True
        elif resource_types:
            # 检查resource_types中是否包含非习题资源类型
            non_exercise_types = ['教案', '课件', '教学大纲', '课例', '教学设计', 'GGB', 'GeoGebra']
            if any(rt in non_exercise_types for rt in resource_types):
                is_non_exercise_query = True
        
        if is_non_exercise_query:
            # V70.0改进：进一步增加非习题资源的检索数量
            # V75.0改进：对于课件资源，使用更高的检索数量
            # V90.0修复：修复ChromaDB错误，将课件检索数量降低到合理范围
            # V90.1修复：进一步降低课件检索数量，避免ChromaDB错误
            if any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types)):
                adjusted_count = max(adjusted_count, 300)  # V90.1修复：将课件检索数量进一步降低到300
                print(f"   🔍 V90.1课件资源查询: 使用检索数量 {adjusted_count}")
            else:
                adjusted_count = max(adjusted_count, 500)  # V90.0修复：将其他非习题资源检索数量降低到500
                print(f"   🔍 V54.0非习题资源查询: 增加检索数量到 {adjusted_count}")
        else:
            print(f"   🔍 V54.0调试 - 查询不包含非习题关键词，不增加检索数量")
        
        return adjusted_count
