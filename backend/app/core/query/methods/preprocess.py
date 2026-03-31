from .._shared import *


class _PreprocessMixin:
    def preprocess(self, query: str) -> Dict[str, Any]:
        """
        预处理用户查询 - 增强的意图理解版+查询分类
        
        Args:
            query: 原始用户查询
            
        Returns:
            预处理结果字典
        """
        logger.info(f"📝 开始预处理查询: {query}")
        
        result = {
            "original_query": query,
            "cleaned_query": "",
            "keywords": [],
            "core_concepts": [],
            "latex_expressions": [],
            "search_versions": [],
            "intent": {
                "topic": "",
                "resource_types": [],
                "operation": "",
                "quality": ""
            },
            "query_type": "",
            "clarity": 0.0
        }
        
        corrected_query = self.fuzzy_matcher.correct_typos(query)
        if corrected_query != query:
            logger.info(f"🔧 模糊纠错: {query} -> {corrected_query}")
            query = corrected_query
        
        result["latex_expressions"] = self._extract_latex(query)
        cleaned = self._clean_query(query)
        result["cleaned_query"] = cleaned
        
        all_possible_keywords = []
        for concept, terms in self.math_keywords.items():
            all_possible_keywords.extend(terms)
        
        result["keywords"] = self._extract_keywords(cleaned)
        fuzzy_keywords = self.fuzzy_matcher.fuzzy_match_keywords(cleaned, all_possible_keywords)
        for kw in fuzzy_keywords:
            if kw not in result["keywords"]:
                result["keywords"].append(kw)
                logger.info(f"🎯 模糊匹配添加关键词: {kw}")
        
        result["core_concepts"] = self._extract_core_concepts(cleaned)
        result["intent"] = self._extract_intent(query, cleaned, result["core_concepts"])
        result["query_type"] = self._classify_query_type(query, result["intent"], result["core_concepts"])
        result["clarity"] = self._calculate_query_clarity(query, result["core_concepts"], result["intent"])
        result["search_versions"] = self._generate_search_versions(result)
        
        # V33.0改进：处理上下文查询
        if self.context_history and "最近讲了" in query or "最近学了" in query:
            context_enhanced = self._enhance_with_context(query, result)
            if context_enhanced:
                result["context_enhanced"] = context_enhanced
                logger.info(f"🔄 V33.0上下文增强: {context_enhanced}")
        
        # 更新上下文历史
        self._update_context_history(query, result)
        
        logger.info(f"✅ 查询预处理完成")
        logger.info(f"   清洗后: {result['cleaned_query']}")
        logger.info(f"   关键词: {result['keywords']}")
        logger.info(f"   核心概念: {result['core_concepts']}")
        logger.info(f"   LaTeX表达式: {len(result['latex_expressions'])}个")
        logger.info(f"   查询类型: {result['query_type']}")
        logger.info(f"   查询明确度: {result['clarity']:.2f}")
        logger.info(f"   意图分析: {result['intent']}")
        
        return result
