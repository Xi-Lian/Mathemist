from .._shared import *


class _FormatResourcesByDomainMixin:
    def _format_resources_by_domain(
        self,
        resources: List[Dict[str, Any]],
        icon: str,
        category_name: str,
        scenario: str = "search",
        state: Any = None
    ) -> List[str]:
        """
        V10.0：分层展示机制，从"最优解"思维转向"全面性"思维
        
        改进：
        - 明确展示不同级别的资源
        - 保留更多有价值的资源
        - 提供渐进式的资源浏览体验
        """
        response_parts = []
        
        # 先按相关性排序所有资源
        sorted_resources = sorted(
            resources,
            key=lambda x: (
                -x.get('relevance', 0),  # 相关性优先
                -x.get('is_core_match', False),
                -x.get('matched_theme_count', 0)
            )
        )
        
        # 将资源按领域分类（使用V9.0的领域分类）
        domain_resources = {}
        for resource in sorted_resources:
            # 使用V9.0计算的领域，而不是自己分类
            domain = resource.get('domain', '其他')
            if domain not in domain_resources:
                domain_resources[domain] = []
            domain_resources[domain].append(resource)
        
        # 动态确定领域显示顺序：
        # 1. 首先根据用户查询的核心主题确定优先领域
        # 2. 然后按该领域最高相关性资源排序
        query = ""
        if state:
            query = self._get_state_value(state, "user_input", "")
        priority_domains = self._get_priority_domains(query)
        
        domain_max_relevance = {}
        domain_avg_relevance = {}
        for domain, domain_res_list in domain_resources.items():
            if domain_res_list:
                domain_max_relevance[domain] = max(r.get('relevance', 0) for r in domain_res_list)
                domain_avg_relevance[domain] = sum(r.get('relevance', 0) for r in domain_res_list) / len(domain_res_list)
        
        # 排序函数：优先领域 > 最高相关性 > 平均相关性 > 领域名称
        def domain_sort_key(domain):
            priority = -100 if domain in priority_domains else 0
            return (priority, -domain_max_relevance.get(domain, 0), -domain_avg_relevance.get(domain, 0), domain)
        
        # 按优先级排序领域
        domain_order = sorted(
            domain_resources.keys(),
            key=domain_sort_key
        )
        
        # 如果没有资源，使用默认顺序
        if not domain_order:
            domain_order = ["一般函数", "三角函数", "具体函数", "其他"]

        # 按动态排序后的领域顺序显示资源
        for domain in domain_order:
            if domain not in domain_resources or not domain_resources[domain]:
                continue

            # V11.2：为每个领域内的资源按决策中心的优先级层级分类
            priority_resources = {
                4: [],  # 核心主题匹配
                3: [],  # 相关主题匹配
                2: [],  # 扩展主题匹配
                1: [],  # 提及主题匹配
                0: []   # 无匹配
            }
            
            # 分类资源（使用决策中心的priority_level）
            for resource in domain_resources[domain]:
                priority_level = resource.get('priority_level', 0)
                priority_resources[priority_level].append(resource)
            
            # V11.2：显示核心主题匹配资源（优先级4）
            if priority_resources[4]:
                if domain == "一般函数":
                    response_parts.append("\n⭐ 【一般函数】核心主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n⭐ 【三角函数】核心主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n⭐ 【具体函数】核心主题匹配：\n")
                else:
                    response_parts.append(f"\n⭐ 【{domain}】核心主题匹配：\n")
                
                for resource in priority_resources[4]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示相关主题匹配资源（优先级3）
            if priority_resources[3]:
                if domain == "一般函数":
                    response_parts.append("\n📌 【一般函数】相关主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n📌 【三角函数】相关主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n📌 【具体函数】相关主题匹配：\n")
                else:
                    response_parts.append(f"\n📌 【{domain}】相关主题匹配：\n")
                
                for resource in priority_resources[3]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示扩展主题匹配资源（优先级2）
            if priority_resources[2]:
                if domain == "一般函数":
                    response_parts.append("\n📎 【一般函数】扩展主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n📎 【三角函数】扩展主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n📎 【具体函数】扩展主题匹配：\n")
                else:
                    response_parts.append(f"\n📎 【{domain}】扩展主题匹配：\n")
                
                for resource in priority_resources[2]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示提及主题匹配资源（优先级1）
            if priority_resources[1]:
                if domain == "一般函数":
                    response_parts.append("\n💡 【一般函数】提及主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n💡 【三角函数】提及主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n💡 【具体函数】提及主题匹配：\n")
                else:
                    response_parts.append(f"\n💡 【{domain}】提及主题匹配：\n")
                
                for resource in priority_resources[1]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        
        return response_parts
