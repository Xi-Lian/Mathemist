from .._shared import *


class _CheckThemeRelevanceWithLlmMixin:
    def _check_theme_relevance_with_llm(self, theme: str, doc: str, meta: Dict[str, Any]) -> bool:
        """
        使用LLM动态判断资源是否与主题相关
        
        Args:
            theme: 主题名称
            doc: 资源内容
            meta: 资源元数据
        
        Returns:
            是否相关
        """
        try:
            # 获取模型
            model = model_config.get_model("intent")
            
            # 构建提示词 - V13.0：更灵活的主题判断
            prompt = ChatPromptTemplate.from_template("""
你是一个数学教育资源评估专家。请判断以下资源是否与指定主题相关。

主题：{theme}

资源信息：
- 标题：{title}
- 内容摘要：{content}
- 知识点：{knowledge_points}

请判断该资源是否与主题"{theme}"相关。

主题定义：
- **指数函数**：形如 $y = a^x$（$a>0$ 且 $a \neq 1$）的函数，涉及指数运算、指数增长/衰减、指数方程/不等式
- **对数函数**：形如 $y = \log_a x$（$a>0$ 且 $a \neq 1$）的函数，涉及对数运算、对数方程/不等式
- **幂函数**：形如 $y = x^a$ 的函数，涉及幂运算
- **二次函数**：形如 $y = ax^2 + bx + c$（$a \neq 0$）的函数，涉及抛物线、顶点、对称轴
- **三角函数**：涉及 sin、cos、tan 等三角函数
- **三角恒等变换**：涉及三角函数的恒等变形，如诱导公式、和角公式、差角公式、二倍角公式等

判断标准：
1. 资源的主要内容是否明确涉及该主题的核心概念和方法
2. 资源是否包含该主题的典型特征和关键词
3. 资源是否属于该主题的知识体系

排除标准：
- 如果资源只涉及函数的基本概念（如定义域、值域、单调性、奇偶性）而没有特定主题的内容，判断为**不相关**
- 如果资源涉及的是正比例函数、反比例函数、一次函数等初等函数，判断为**不相关**
- 如果资源的主要内容和知识点与目标主题完全无关，判断为**不相关**

注意：
- 资源中可能包含多个主题的内容，只要主要内容涉及目标主题，就应该判断为**相关**
- 不要因为资源中包含其他主题的关键词就判断为**不相关**，除非这些关键词是主要内容

请只返回"相关"或"不相关"，不要返回其他内容。
""")
            
            # 提取资源信息
            title = meta.get("title", "未知标题")
            content = doc[:500] if len(doc) > 500 else doc  # 只取前500字符
            knowledge_points = meta.get("知识点", "")
            
            # 构建链
            chain = prompt | model | StrOutputParser()
            
            # 调用LLM
            result = chain.invoke({
                "theme": theme,
                "title": title,
                "content": content,
                "knowledge_points": knowledge_points
            })
            
            # 解析结果
            result = result.strip()
            is_relevant = "相关" in result
            
            print(f"      🔍 LLM判断：'{title}' 与主题 '{theme}' -> {result}")
            
            return is_relevant
            
        except Exception as e:
            print(f"      ⚠️ LLM判断失败: {e}，默认不相关")
            # 如果LLM判断失败，默认不相关，避免误匹配
            return False
