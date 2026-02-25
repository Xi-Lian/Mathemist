"""
查询智能预处理模块

职责：
- 清洗和标准化用户查询
- 提取关键词和核心概念
- 处理LaTeX数学公式
- 支持模糊匹配
- 生成多种检索策略的查询文本
- 查询分类（概念型、方法型、资源型、问题型、混合型）
- 查询明确度计算
"""

import re
from typing import List, Dict, Any, Set
import logging
from ..config.resource_type_config import (
    get_all_user_types,
    get_standard_name,
    normalize_resource_types
)

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """模糊匹配器"""
    
    def __init__(self):
        """初始化模糊匹配器"""
        # 常见拼写错误映射
        self.typo_map = {
            "函书": "函数",
            "方程试": "方程式",
            "不等试": "不等式",
            "指树": "指数",
            "对树": "对数",
            "倒树": "导数",
            "积份": "积分",
            "极现": "极限",
            "三角函书": "三角函数",
            "二次函书": "二次函数",
            "园": "圆",
            "三交形": "三角形",
            "平形": "平行",
            "垂值": "垂直",
            "相试": "相似",
            "全登": "全等",
            "概律": "概率",
            "统记": "统计"
        }
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        计算Levenshtein编辑距离
        
        Args:
            s1: 字符串1
            s2: 字符串2
            
        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def correct_typos(self, text: str) -> str:
        """
        纠正常见拼写错误
        
        Args:
            text: 输入文本
            
        Returns:
            纠正后的文本
        """
        corrected = text
        for typo, correct in self.typo_map.items():
            corrected = corrected.replace(typo, correct)
        return corrected
    
    def fuzzy_match_keywords(self, query: str, keywords: List[str], max_distance: int = 2) -> List[str]:
        """
        模糊匹配关键词
        
        Args:
            query: 查询文本
            keywords: 关键词列表
            max_distance: 最大编辑距离
            
        Returns:
            匹配的关键词列表
        """
        matches = []
        
        for keyword in keywords:
            if keyword in query:
                if keyword not in matches:
                    matches.append(keyword)
                continue
            
            if len(keyword) >= 3:
                query_words = re.findall(r'[\w\u4e00-\u9fff]+', query)
                for q_word in query_words:
                    if len(q_word) >= 2:
                        distance = self.levenshtein_distance(q_word, keyword)
                        if distance <= max_distance and distance < len(keyword):
                            if keyword not in matches:
                                matches.append(keyword)
                                logger.debug(f"模糊匹配: {q_word} -> {keyword} (距离: {distance})")
        
        return matches


class QueryPreprocessor:
    """查询预处理器"""
    
    def __init__(self):
        """初始化查询预处理器"""
        self.fuzzy_matcher = FuzzyMatcher()
        self.math_synonyms = {
            "函数": ["函数", "function"],
            "方程": ["方程", "equation"],
            "不等式": ["不等式", "inequality"],
            "指数": ["指数", "指数函数", "exponent"],
            "对数": ["对数", "对数函数", "logarithm"],
            "导数": ["导数", "微分", "derivative"],
            "积分": ["积分", "integral"],
            "极限": ["极限", "limit"],
            "三角函数": ["三角函数", "三角", "trigonometric"],
            "二次函数": ["二次函数", "抛物线", "quadratic"],
            "圆": ["圆", "circle"],
            "三角形": ["三角形", "triangle"],
            "平行": ["平行", "parallel"],
            "垂直": ["垂直", "perpendicular"],
            "相似": ["相似", "similar"],
            "全等": ["全等", "congruent"],
            "概率": ["概率", "probability"],
            "统计": ["统计", "statistics"]
        }
        
        self.math_keywords = {
            "函数": ["函数", "定义域", "值域", "单调性", "奇偶性", "周期性", "图像"],
            "方程": ["方程", "解", "根", "求解", "解方程"],
            "不等式": ["不等式", "解集", "解不等式"],
            "指数": ["指数", "幂", "底数", "指数函数"],
            "对数": ["对数", "真数", "底数", "对数函数"],
            "导数": ["导数", "切线", "斜率", "极值", "最值", "单调"],
            "积分": ["积分", "面积", "体积", "原函数"],
            "极限": ["极限", "趋近", "无穷小", "无穷大"],
            "几何": ["几何", "图形", "形状", "位置", "距离", "角度"]
        }
        
        # 指令词定义
        self.instruction_words = {
            "resource_retrieval": ["推送", "给", "找", "推荐", "有没有", "我要", "帮我找", "想要", "需要"],
            "content_generation": ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
        }
        
        # 完整主题词定义
        self.complete_themes = [
            "函数的概念", "函数的表示法", "函数的性质", "函数的应用",
            "指数函数", "指数函数的概念", "指数函数的图像和性质", "指数函数的应用",
            "对数函数", "对数函数的概念", "对数函数的图像和性质", "对数函数的应用",
            "三角函数", "三角函数的概念", "三角函数的图像与性质", "三角函数的应用",
            "幂函数", "幂函数的图像和性质", "幂函数的应用",
            "二次函数", "二次函数的图像和性质", "二次函数的应用",
            "诱导公式", "三角恒等变换", "函数的零点", "二分法",
            "任意角", "弧度制", "同角三角函数的基本关系", "函数模型的应用"
        ]
    
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
        
        logger.info(f"✅ 查询预处理完成")
        logger.info(f"   清洗后: {result['cleaned_query']}")
        logger.info(f"   关键词: {result['keywords']}")
        logger.info(f"   核心概念: {result['core_concepts']}")
        logger.info(f"   LaTeX表达式: {len(result['latex_expressions'])}个")
        logger.info(f"   查询类型: {result['query_type']}")
        logger.info(f"   查询明确度: {result['clarity']:.2f}")
        logger.info(f"   意图分析: {result['intent']}")
        
        return result
    
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
    
    def _calculate_query_clarity(self, query: str, core_concepts: List[str], intent: Dict[str, Any]) -> float:
        """
        计算查询明确度（0-1）
        """
        clarity = 0.0
        
        if core_concepts:
            clarity += 0.3
        
        if intent["resource_types"]:
            clarity += 0.2
        
        qualifier_words = ["二次", "指数", "对数", "三角", "一元", "二元", "偏导", "定积分", "不定积分"]
        for word in qualifier_words:
            if word in query:
                clarity += 0.2
                break
        
        query_length = len(query)
        if 10 <= query_length <= 30:
            clarity += 0.2
        elif query_length > 30:
            clarity += 0.1
        
        if "$" in query or "\\(" in query or "\\[" in query:
            clarity += 0.1
        
        return min(1.0, clarity)
    
    def _identify_instruction_type(self, query: str) -> str:
        """
        识别指令类型
        
        Args:
            query: 查询文本
            
        Returns:
            指令类型: "resource_retrieval", "content_generation", 或空字符串
        """
        # 优先识别资源获取类指令
        for keyword in self.instruction_words["resource_retrieval"]:
            if keyword in query:
                logger.info(f"识别到资源获取指令: {keyword}")
                return "resource_retrieval"
        
        # 然后识别内容生成类指令
        for keyword in self.instruction_words["content_generation"]:
            if keyword in query:
                logger.info(f"识别到内容生成指令: {keyword}")
                return "content_generation"
        
        # 没有识别到明确指令
        return ""
    
    def _extract_complete_theme(self, query: str) -> str:
        """
        提取完整主题
        
        Args:
            query: 查询文本
            
        Returns:
            完整主题字符串
        """
        # 按长度降序排序，优先匹配更长的主题
        sorted_themes = sorted(self.complete_themes, key=len, reverse=True)
        
        for theme in sorted_themes:
            if theme in query:
                logger.info(f"识别到完整主题: {theme}")
                return theme
        
        # 如果没有识别到完整主题，返回空
        return ""
    
    def _extract_topic_after_instruction(self, query: str, instruction_type: str) -> str:
        """
        提取指令词后的主题
        
        Args:
            query: 查询文本
            instruction_type: 指令类型
            
        Returns:
            提取的主题
        """
        # 移除指令词
        processed_query = query
        
        if instruction_type == "resource_retrieval":
            for keyword in self.instruction_words["resource_retrieval"]:
                if keyword in processed_query:
                    processed_query = processed_query.replace(keyword, "").strip()
        elif instruction_type == "content_generation":
            for keyword in self.instruction_words["content_generation"]:
                if keyword in processed_query:
                    processed_query = processed_query.replace(keyword, "").strip()
        
        # 提取完整主题
        complete_theme = self._extract_complete_theme(processed_query)
        if complete_theme:
            return complete_theme
        
        # 如果没有完整主题，提取核心概念
        concepts = self._extract_core_concepts(processed_query)
        if concepts:
            return concepts[0]
        
        return ""
    
    def _extract_intent(self, original_query: str, cleaned_query: str, core_concepts: List[str]) -> Dict[str, Any]:
        """
        提取查询意图 - 四维分析
        """
        intent = {
            "topic": "",
            "resource_types": [],
            "operation": "",
            "quality": "",
            "instruction_type": ""
        }
        
        # 1. 识别指令类型
        instruction_type = self._identify_instruction_type(original_query)
        intent["instruction_type"] = instruction_type
        
        # 2. 提取主题（排除指令词的影响）
        if instruction_type:
            # 从指令词后的内容中提取主题
            topic = self._extract_topic_after_instruction(original_query, instruction_type)
        else:
            # 没有指令词，直接提取主题
            complete_theme = self._extract_complete_theme(original_query)
            if complete_theme:
                topic = complete_theme
            elif core_concepts:
                topic = core_concepts[0]
            else:
                topic = ""
        
        intent["topic"] = topic
        
        # 3. 提取资源类型
        # 首先，使用统一的资源类型配置来提取资源类型
        all_user_types = get_all_user_types()
        
        for user_type in all_user_types:
            if user_type in original_query:
                # 规范化为标准名称
                standard_name = get_standard_name(user_type)
                if standard_name not in intent["resource_types"]:
                    intent["resource_types"].append(standard_name)
                    logger.info(f"识别到资源类型: {user_type} -> {standard_name}")
        
        # 如果统一配置中没有找到，再用备用的模式匹配（保持兼容性）
        if not intent["resource_types"]:
            resource_type_patterns = {
                "courseware": ["课件", "ppt", "幻灯片"],
                "lesson_plan": ["教案", "教学设计", "导学案"],
                "exercise": ["习题", "题目", "练习题", "试题", "题"],
                "lesson_case": ["课例", "视频", "课堂实录", "公开课"],
                "ggb": ["ggb", "GGB", "geogebra", "几何画板"],
                "syllabus": ["教学大纲", "大纲", "课程标准"],
                "theory": ["理论", "知识点", "概念"]
            }
            
            for resource_type, keywords in resource_type_patterns.items():
                for keyword in keywords:
                    if keyword in original_query:
                        # 这里提取的是数据库类型，我们需要将它映射到标准名称
                        # 从DB类型到标准名称的映射
                        db_to_std = {
                            "lesson_plan": "教案",
                            "courseware": "课件",
                            "lesson_case": "课例",
                            "exercise": "习题",
                            "ggb": "GGB",
                            "syllabus": "教学大纲",
                            "theory": "理论"
                        }
                        standard_name = db_to_std.get(resource_type, resource_type)
                        if standard_name not in intent["resource_types"]:
                            intent["resource_types"].append(standard_name)
                            logger.info(f"备用模式识别资源类型: {resource_type} -> {standard_name}")
                        break
        
        # 4. 提取操作类型
        operation_patterns = {
            "学习": ["学习", "学", "了解", "理解", "掌握"],
            "备课": ["备课", "准备", "教学设计"],
            "出题": ["出题", "组题", "命题", "找题"],
            "练习": ["练习", "做题", "训练", "巩固"],
            "复习": ["复习", "回顾", "总结"],
            "预习": ["预习", "提前学"]
        }
        
        for operation, keywords in operation_patterns.items():
            for keyword in keywords:
                if keyword in original_query:
                    intent["operation"] = operation
                    break
            if intent["operation"]:
                break
        
        # 5. 提取质量要求
        quality_patterns = {
            "基础": ["基础", "简单", "容易", "入门"],
            "中等": ["中等", "一般", "普通"],
            "拔高": ["拔高", "难", "困难", "挑战", "培优", "提高"],
            "优秀": ["优秀", "精品", "优质", "获奖", "名师"]
        }
        
        for quality, keywords in quality_patterns.items():
            for keyword in keywords:
                if keyword in original_query:
                    intent["quality"] = quality
                    break
            if intent["quality"]:
                break
        
        return intent
    
    def _clean_query(self, query: str) -> str:
        """
        清洗查询文本
        """
        if not query:
            return ""
        
        cleaned = re.sub(r'\s+', ' ', query.strip())
        cleaned = re.sub(r'\$.*?\$', '', cleaned)
        cleaned = re.sub(r'\\\[.*?\\\]', '', cleaned)
        cleaned = re.sub(r'\\\(.*?\\\)', '', cleaned)
        cleaned = re.sub(r'[^\w\u4e00-\u9fff，。？！,.!?]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_latex(self, query: str) -> List[str]:
        """
        提取LaTeX表达式
        """
        latex_expressions = []
        latex_expressions.extend(re.findall(r'\$(.*?)\$', query))
        latex_expressions.extend(re.findall(r'\\\((.*?)\\\)', query))
        latex_expressions.extend(re.findall(r'\\\[(.*?)\\\]', query))
        
        cleaned_expressions = []
        for expr in latex_expressions:
            cleaned = self._clean_latex_expression(expr)
            if cleaned:
                cleaned_expressions.append(cleaned)
        
        return cleaned_expressions
    
    def _clean_latex_expression(self, expr: str) -> str:
        """
        清理LaTeX表达式，提取关键数学信息
        """
        if not expr:
            return ""
        
        cleaned = re.sub(r'\s+', '', expr.strip())
        cleaned = re.sub(r'\\left|\\right', '', cleaned)
        cleaned = re.sub(r'\\frac', '/', cleaned)
        cleaned = re.sub(r'\\cdot', '*', cleaned)
        cleaned = re.sub(r'\\times', '*', cleaned)
        cleaned = re.sub(r'\\div', '/', cleaned)
        cleaned = re.sub(r'\\pm', '±', cleaned)
        cleaned = re.sub(r'\\neq', '≠', cleaned)
        cleaned = re.sub(r'\\leq', '≤', cleaned)
        cleaned = re.sub(r'\\geq', '≥', cleaned)
        cleaned = re.sub(r'\\infty', '∞', cleaned)
        cleaned = re.sub(r'\\alpha', 'α', cleaned)
        cleaned = re.sub(r'\\beta', 'β', cleaned)
        cleaned = re.sub(r'\\gamma', 'γ', cleaned)
        cleaned = re.sub(r'\\delta', 'δ', cleaned)
        cleaned = re.sub(r'\\theta', 'θ', cleaned)
        cleaned = re.sub(r'\\pi', 'π', cleaned)
        cleaned = re.sub(r'\\sin', 'sin', cleaned)
        cleaned = re.sub(r'\\cos', 'cos', cleaned)
        cleaned = re.sub(r'\\tan', 'tan', cleaned)
        cleaned = re.sub(r'\\log', 'log', cleaned)
        cleaned = re.sub(r'\\ln', 'ln', cleaned)
        cleaned = re.sub(r'\\sqrt', '√', cleaned)
        cleaned = re.sub(r'\\sum', '∑', cleaned)
        cleaned = re.sub(r'\\int', '∫', cleaned)
        cleaned = re.sub(r'\\lim', 'lim', cleaned)
        cleaned = cleaned.replace('{', '').replace('}', '')
        
        return cleaned
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        提取关键词
        """
        keywords = []
        
        for concept, terms in self.math_keywords.items():
            for term in terms:
                if term in query and term not in keywords:
                    keywords.append(term)
        
        if not keywords:
            words = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
            keywords = words[:5]
        
        return keywords
    
    def _extract_core_concepts(self, query: str) -> List[str]:
        """
        提取核心概念
        """
        concepts = []
        
        for concept, terms in self.math_keywords.items():
            for term in terms:
                if term in query and concept not in concepts:
                    concepts.append(concept)
                    break
        
        return concepts
    
    def _generate_search_versions(self, preprocess_result: Dict[str, Any]) -> List[str]:
        """
        生成多种检索版本
        """
        versions = []
        
        original = preprocess_result["original_query"]
        cleaned = preprocess_result["cleaned_query"]
        keywords = preprocess_result["keywords"]
        concepts = preprocess_result["core_concepts"]
        latex = preprocess_result["latex_expressions"]
        
        if original:
            versions.append(original)
        
        if cleaned and cleaned != original:
            versions.append(cleaned)
        
        if keywords:
            versions.append(" ".join(keywords))
        
        if concepts:
            versions.append(" ".join(concepts))
        
        if keywords and concepts:
            versions.append(" ".join(keywords + concepts))
        
        if latex:
            versions.append(" ".join(latex))
        
        if keywords and latex:
            versions.append(" ".join(keywords + latex))
        
        unique_versions = []
        seen = set()
        for v in versions:
            if v and v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        return unique_versions[:8]
    
    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """
        使用同义词扩展查询
        """
        expanded_queries = [query]
        
        for term, synonyms in self.math_synonyms.items():
            if term in query:
                for syn in synonyms:
                    if syn != term:
                        expanded = query.replace(term, syn)
                        if expanded not in expanded_queries:
                            expanded_queries.append(expanded)
        
        return expanded_queries


_query_preprocessor = None


def get_query_preprocessor() -> QueryPreprocessor:
    """
    获取查询预处理器单例
    """
    global _query_preprocessor
    if _query_preprocessor is None:
        _query_preprocessor = QueryPreprocessor()
    return _query_preprocessor
