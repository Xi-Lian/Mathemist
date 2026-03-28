"""
V9.2 主题匹配器 - 智能权重优化版

核心改进：
1. 统一主题识别和领域分类：领域分类由核心主题决定
2. 三级主题分类：核心主题、相关主题、提及主题
3. 动态领域排序：根据用户查询调整领域顺序
4. 严格主题匹配：区分不同主题的核心意图
5. 智能推荐方向：区分向下推荐（父→子）和向上推荐（子→父）
6. 领域距离控制：引入领域距离概念，避免跨领域过度推荐
7. 相关主题阈值：设置展示阈值，过滤低相关性结果
8. 主题关键词优化：定义核心关键词和排除词，提高匹配精度
9. 权重因子优化：将二元过滤器改为连续权重，避免过滤过度
10. 动态阈值调整：根据主题分布和查询明确度自动调整
11. 分级展示机制：替代二元展示决策，保留扩展内容
12. 联合计算优化：使用加权平均替代简单相乘
13. 保持V9.1的所有优势
"""

from typing import List, Dict, Any, Optional
from .theme_matcher import ThemeMatcher

class ThemeMatcherV90:
    """V9.2 主题匹配器"""
    
    def __init__(self):
        self.v82 = ThemeMatcher()
        
        # 相关主题展示阈值（基础值）
        self.base_related_theme_threshold = 0.5
        
        # 分级展示配置
        self.display_levels = {
            "core": {"min_score": 0.8, "max_items": 10, "description": "核心资源"},
            "related": {"min_score": 0.5, "max_items": 15, "description": "相关资源"},
            "extended": {"min_score": 0.3, "max_items": 10, "description": "扩展资源"},
            "candidate": {"min_score": 0.1, "max_items": 5, "description": "候选资源"}
        }
        
        # 权重因子配置
        self.weight_factors = {
            "threshold": 0.4,      # 阈值因子权重
            "exclusion": 0.2,      # 排除词因子权重
            "domain": 0.2,         # 领域距离因子权重
            "direction": 0.2       # 方向控制因子权重
        }
        
        # 主题到领域的映射关系
        self.theme_domain_map = {
            # 一般函数领域
            "函数的概念": "一般函数",
            "函数的表示法": "一般函数",
            "函数的基本性质": "一般函数",
            "函数的单调性": "一般函数",
            "函数的奇偶性": "一般函数",
            "函数的周期性": "一般函数",
            "函数的应用": "一般函数",
            
            # 具体函数领域
            "指数函数": "具体函数",
            "对数函数": "具体函数",
            "幂函数": "具体函数",
            "二次函数": "具体函数",
            "指数函数的应用": "具体函数",
            "对数函数的应用": "具体函数",
            "幂函数的应用": "具体函数",
            "二次函数的应用": "具体函数",
            
            # 三角函数领域
            "三角函数": "三角函数",
            "正弦函数": "三角函数",
            "余弦函数": "三角函数",
            "正切函数": "三角函数",
            "三角恒等变换": "三角函数",
            "三角函数的性质": "三角函数",
            "三角函数的应用": "三角函数",
        }
        
        # 领域距离定义
        self.domain_distance = {
            # 同一具体主题：距离0
            ("函数的概念", "函数的概念"): 0,
            ("函数的应用", "函数的应用"): 0,
            ("指数函数", "指数函数"): 0,
            ("指数函数的应用", "指数函数的应用"): 0,
            ("对数函数", "对数函数"): 0,
            ("对数函数的应用", "对数函数的应用"): 0,
            ("幂函数", "幂函数"): 0,
            ("幂函数的应用", "幂函数的应用"): 0,
            ("二次函数", "二次函数"): 0,
            ("二次函数的应用", "二次函数的应用"): 0,
            ("三角函数", "三角函数"): 0,
            ("三角函数的应用", "三角函数的应用"): 0,
            
            # 同一函数类型的应用主题：距离0.5
            ("指数函数", "指数函数的应用"): 0.5,
            ("指数函数的应用", "指数函数"): 0.5,
            ("对数函数", "对数函数的应用"): 0.5,
            ("对数函数的应用", "对数函数"): 0.5,
            ("幂函数", "幂函数的应用"): 0.5,
            ("幂函数的应用", "幂函数"): 0.5,
            ("二次函数", "二次函数的应用"): 0.5,
            ("二次函数的应用", "二次函数"): 0.5,
            ("三角函数", "三角函数的应用"): 0.5,
            ("三角函数的应用", "三角函数"): 0.5,
            
            # 同一分支的不同具体主题：距离1
            ("指数函数", "对数函数"): 1,
            ("指数函数", "幂函数"): 1,
            ("指数函数", "二次函数"): 1,
            ("对数函数", "幂函数"): 1,
            ("对数函数", "指数函数"): 1,
            ("对数函数", "二次函数"): 1,
            ("幂函数", "指数函数"): 1,
            ("幂函数", "对数函数"): 1,
            ("幂函数", "二次函数"): 1,
            ("二次函数", "指数函数"): 1,
            ("二次函数", "对数函数"): 1,
            ("二次函数", "幂函数"): 1,
            
            # 同一分支的不同应用主题：距离1
            ("指数函数的应用", "对数函数的应用"): 1,
            ("指数函数的应用", "幂函数的应用"): 1,
            ("指数函数的应用", "二次函数的应用"): 1,
            ("对数函数的应用", "幂函数的应用"): 1,
            ("对数函数的应用", "指数函数的应用"): 1,
            ("对数函数的应用", "二次函数的应用"): 1,
            ("幂函数的应用", "指数函数的应用"): 1,
            ("幂函数的应用", "对数函数的应用"): 1,
            ("幂函数的应用", "二次函数的应用"): 1,
            ("二次函数的应用", "指数函数的应用"): 1,
            ("二次函数的应用", "对数函数的应用"): 1,
            ("二次函数的应用", "幂函数的应用"): 1,
            
            # 同一大类下的不同分支：距离2
            ("指数函数", "三角函数"): 2,
            ("对数函数", "三角函数"): 2,
            ("幂函数", "三角函数"): 2,
            ("二次函数", "三角函数"): 2,
            ("三角函数", "指数函数"): 2,
            ("三角函数", "对数函数"): 2,
            ("三角函数", "幂函数"): 2,
            ("三角函数", "二次函数"): 2,
            
            # 应用主题与其他分支的距离：距离2
            ("指数函数的应用", "三角函数"): 2,
            ("对数函数的应用", "三角函数"): 2,
            ("幂函数的应用", "三角函数"): 2,
            ("二次函数的应用", "三角函数"): 2,
            ("三角函数的应用", "指数函数"): 2,
            ("三角函数的应用", "对数函数"): 2,
            ("三角函数的应用", "幂函数"): 2,
            ("三角函数的应用", "二次函数"): 2,
            
            # 不同大类：距离3
            ("函数的概念", "指数函数"): 3,
            ("函数的概念", "对数函数"): 3,
            ("函数的概念", "幂函数"): 3,
            ("函数的概念", "二次函数"): 3,
            ("函数的概念", "三角函数"): 3,
            ("函数的应用", "指数函数"): 3,
            ("函数的应用", "对数函数"): 3,
            ("函数的应用", "幂函数"): 3,
            ("函数的应用", "二次函数"): 3,
            ("函数的应用", "三角函数"): 3,
        }
        
        # 主题层级关系（父主题 -> 子主题）
        # V24.3改进：添加一次函数层级
        self.theme_hierarchy = {
            "函数的概念": ["指数函数的概念", "对数函数的概念", "幂函数的概念", "二次函数的概念", "一次函数的概念", "三角函数的概念"],
            "函数的性质": ["函数的单调性", "函数的奇偶性", "函数的周期性", "指数函数的性质", "对数函数的性质", "幂函数的性质", "二次函数的性质", "一次函数的性质", "三角函数的性质"],
            "指数函数": ["指数函数的概念", "指数函数的性质", "指数函数的应用"],
            "对数函数": ["对数函数的概念", "对数函数的性质", "对数函数的应用"],
            "幂函数": ["幂函数的概念", "幂函数的性质", "幂函数的应用"],
            "二次函数": ["二次函数的概念", "二次函数的性质", "二次函数的应用"],
            "一次函数": ["一次函数的概念", "一次函数的性质", "一次函数的应用"],
            "三角函数": ["正弦函数", "余弦函数", "正切函数", "三角函数的概念", "三角函数的性质"],
        }
        
        # 主题排除词定义（用于提高匹配精度）
        # V18.0改进：增加一次函数的排除词配置，优化排除词检查逻辑
        self.theme_exclusion_words = {
            "指数函数": ["对数", "log", "ln", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "对数函数": ["指数", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "幂函数": ["指数", "对数", "log", "ln", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "二次函数": ["指数", "对数", "log", "ln", "幂函数", "三角", "sin", "cos", "tan", "正比例", "反比例"],
            "一次函数": ["指数", "对数", "log", "ln", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例"],
            "三角函数": ["指数", "对数", "log", "ln", "幂函数", "二次", "正比例", "反比例", "一次函数"],
            "函数的概念": ["指数函数", "对数函数", "幂函数", "二次函数", "三角函数", "一次函数"],
            "函数的单调性": ["诱导公式", "三角恒等变换", "弧度制", "任意角", "对数运算", "指数运算"],
            "函数的奇偶性": ["诱导公式", "三角恒等变换", "弧度制", "任意角", "对数运算", "指数运算"],
            "函数的周期性": ["诱导公式", "三角恒等变换", "弧度制", "任意角", "对数运算", "指数运算"],
            "指数函数的应用": ["对数", "log", "ln", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "对数函数的应用": ["指数", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "幂函数的应用": ["指数", "对数", "log", "ln", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例", "一次函数"],
            "二次函数的应用": ["指数", "对数", "log", "ln", "幂函数", "三角", "sin", "cos", "tan", "正比例", "反比例"],
            "一次函数的应用": ["指数", "对数", "log", "ln", "幂函数", "二次", "三角", "sin", "cos", "tan", "正比例", "反比例"],
            "三角函数的应用": ["指数", "对数", "log", "ln", "幂函数", "二次", "正比例", "反比例", "一次函数"],
        }
        
        # 语义关联映射（相关概念 -> 核心主题）
        self.semantic_mappings = {
            # 二次函数相关
            "抛物线": "二次函数",
            "抛物线的图像": "二次函数",
            "y=ax²+bx+c": "二次函数",
            "开口向上": "二次函数",
            "开口向下": "二次函数",
            "顶点坐标": "二次函数",
            "对称轴": "二次函数",
            
            # 指数函数相关
            "指数增长": "指数函数",
            "指数衰减": "指数函数",
            "放射性衰变": "指数函数",
            "复利计算": "指数函数",
            "人口增长": "指数函数",
            
            # 三角函数相关
            "周期性变化": "三角函数",
            "正弦": "三角函数",
            "余弦": "三角函数",
            "正切": "三角函数",
            "波形图": "三角函数",
            "周期函数": "三角函数",
            
            # 函数性质相关
            "图像对称性": "函数的奇偶性",
            "对称性": "函数的奇偶性",
            "对称函数": "函数的奇偶性",
            
            # 方程相关
            "方程求解": "函数的零点",
            "解方程": "函数的零点",
            "方程根": "函数的零点",
            
            # 应用相关
            "实际应用": "函数的应用",
            "生活应用": "函数的应用",
            "数学建模": "函数的应用",
            "对数应用": "对数函数的应用",
            "指数应用": "指数函数的应用",
            "三角应用": "三角函数的应用",
            "二次应用": "二次函数的应用",
            "幂应用": "幂函数的应用",
            "函数应用": "函数的应用",
        }
        
        # 概念层级关系模型
        self.concept_hierarchy = {
            "函数": {
                "子概念": ["函数的概念", "函数的表示法", "函数的性质", "具体函数"],
                "相关概念": ["方程", "不等式", "代数式"]
            },
            "函数的概念": {
                "子概念": ["函数定义", "定义域", "值域", "对应关系"],
                "相关概念": ["映射", "集合"]
            },
            "函数的性质": {
                "子概念": ["单调性", "奇偶性", "周期性", "最值"],
                "相关概念": ["极限", "连续"]
            },
            "具体函数": {
                "子概念": ["指数函数", "对数函数", "幂函数", "二次函数", "一次函数", "三角函数"],
                "相关概念": ["反函数", "复合函数"]
            },
            "指数函数": {
                "子概念": ["指数幂运算", "指数函数图像", "指数函数性质"],
                "相关概念": ["对数函数", "幂函数", "二次函数"]
            },
            "对数函数": {
                "子概念": ["对数运算", "对数函数图像", "对数函数性质"],
                "相关概念": ["指数函数", "幂函数", "二次函数"]
            },
            "幂函数": {
                "子概念": ["幂运算", "幂函数图像", "幂函数性质"],
                "相关概念": ["指数函数", "对数函数", "二次函数"]
            },
            "二次函数": {
                "子概念": ["二次方程", "二次函数图像", "二次函数性质"],
                "相关概念": ["指数函数", "对数函数", "幂函数"]
            },
            "三角函数": {
                "子概念": ["正弦函数", "余弦函数", "正切函数", "诱导公式"],
                "相关概念": ["三角恒等式", "解三角形"]
            }
        }
        
        # 概念重要性权重
        self.concept_importance = {
            "函数": 1.0,
            "函数的概念": 0.9,
            "函数的表示法": 0.8,
            "函数的性质": 0.9,
            "单调性": 0.85,
            "奇偶性": 0.85,
            "周期性": 0.85,
            "具体函数": 0.8,
            "指数函数": 0.9,
            "对数函数": 0.9,
            "幂函数": 0.85,
            "二次函数": 0.9,
            "三角函数": 0.9,
            "正弦函数": 0.85,
            "余弦函数": 0.85,
            "正切函数": 0.85
        }
    
    def calculate_precise_match(
        self,
        query: str,
        lesson_title: str,
        lesson_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        V10.0：多维度评估，解决"单点依赖"问题
        
        改进：
        - 引入多维度评估指标
        - 综合考虑资源质量、完整性等因素
        - 实现更全面的资源评估
        """
        # 解析教案结构
        structured = self._parse_lesson_plan(lesson_content)
        
        # V11.3：添加调试日志，检查教案解析结果
        print(f"\n📊 教案解析结果:")
        print(f"  - 教学目标长度: {len(structured.get('objectives', ''))}")
        print(f"  - 重难点长度: {len(structured.get('key_points', ''))}")
        print(f"  - 教学过程长度: {len(structured.get('process', ''))}")
        print(f"  - 完整内容长度: {len(structured.get('full_content', ''))}")
        
        # 提取查询主题
        query_themes = self._extract_query_themes(query)
        
        # 匹配主题
        core_theme = None
        related_themes = []
        mentioned_themes = []
        max_match_score = 0.0
        match_explanations = []
        all_matches = []
        
        for theme in query_themes:
            # 使用精准匹配计算
            match_result = self._match_single_theme_precise(
                theme, structured, lesson_title, lesson_content, query_themes, metadata
            )
            
            if match_result:
                match_level = match_result["level"]
                match_score = match_result["score"]
                all_matches.append(match_result)
                
                if match_level == "core":
                    core_theme = match_result["theme"]
                    match_explanations.append(f"{match_result['theme']}(核心主题)")
                elif match_level == "related":
                    related_themes.append(match_result["theme"])
                    match_explanations.append(f"{match_result['theme']}(相关主题)")
                else:
                    mentioned_themes.append(match_result["theme"])
                    match_explanations.append(f"{match_result['theme']}(提及主题)")
                
                # 更新最大匹配分数
                if match_score > max_match_score:
                    max_match_score = match_score
        
        # 计算动态阈值
        core_theme_count = 1 if core_theme else 0
        dynamic_threshold = self._calculate_dynamic_threshold(query, core_theme_count)
        
        # 确定匹配级别和相关性分数
        if core_theme:
            match_level = "core"
            # 核心主题：0.85-0.95
            relevance_score = 0.85 + (max_match_score - 0.85) * 0.5 if max_match_score > 0.85 else 0.85
            should_show = True
        elif related_themes:
            # V9.2：应用动态阈值过滤
            # 计算相关主题的平均分数
            avg_related_score = max_match_score  # 简化计算
            
            if avg_related_score >= dynamic_threshold:
                match_level = "related"
                # 相关主题：0.60-0.80
                relevance_score = 0.60 + max_match_score * 0.2
                should_show = True
            else:
                # 低于阈值，降级为扩展主题
                match_level = "extended"
                # 扩展主题：0.30-0.55
                relevance_score = 0.30 + max_match_score * 0.25
                should_show = relevance_score > 0.3
                # 将相关主题移到提及主题
                mentioned_themes.extend([t for t in related_themes])
                related_themes = []
        elif mentioned_themes:
            match_level = "mentioned"
            # 提及主题：0.30-0.55
            relevance_score = 0.30 + max_match_score * 0.25
            should_show = relevance_score > 0.4  # 提高提及主题的阈值，确保只返回更相关的资源
        else:
            # 未匹配到主题
            match_level = "none"
            relevance_score = 0.0
            should_show = False
        
        # 确定展示级别
        display_level = self._get_display_level(relevance_score)
        
        # 确定领域分类
        domain = self._determine_domain(core_theme, related_themes, lesson_title, lesson_content)
        
        # V10.0：计算多维度评估指标
        resource_quality = self._calculate_resource_quality(lesson_title, lesson_content, structured)
        content_completeness = self._calculate_content_completeness(structured)
        teaching_value = self._calculate_teaching_value(structured)
        comprehensiveness = self._calculate_comprehensiveness(structured)
        
        # V11.3：添加调试日志，显示多维度评估指标
        print(f"\n📈 多维度评估指标:")
        print(f"  - 资源质量: {resource_quality:.2f}")
        print(f"  - 内容完整性: {content_completeness:.2f}")
        print(f"  - 教学价值: {teaching_value:.2f}")
        print(f"  - 综合性: {comprehensiveness:.2f}")
        
        # V11.0：计算概念层级因子（取所有匹配主题的平均值）
        concept_hierarchy_factor = 0.5  # 默认值
        if all_matches:
            hierarchy_factors = []
            for match in all_matches:
                matched_theme = match["theme"]
                # 计算查询主题与匹配主题之间的层级关系
                factor = self._calculate_concept_hierarchy_factor(query_themes[0] if query_themes else "", matched_theme)
                hierarchy_factors.append(factor)
            if hierarchy_factors:
                concept_hierarchy_factor = sum(hierarchy_factors) / len(hierarchy_factors)
        
        # 计算综合得分
        overall_score = self._calculate_overall_score(relevance_score, resource_quality, content_completeness, teaching_value, comprehensiveness)
        
        # 基于综合得分更新展示级别
        display_level = self._get_display_level(overall_score)
        # V61.0改进：提高阈值，确保资源相关性
        should_show = overall_score > 0.30 and relevance_score > 0.30
        
        explanation = f"匹配级别: {match_level}, 展示级别: {display_level}, " + "; ".join(match_explanations) if match_explanations else "未匹配到主题"
        
        return {
            "relevance_score": round(relevance_score, 2),
            "overall_score": round(overall_score, 2),  # V10.0：综合得分
            "matched_themes": [core_theme] if core_theme else related_themes + mentioned_themes,
            "core_theme": core_theme,
            "related_themes": related_themes,
            "mentioned_themes": mentioned_themes,
            "is_core_match": bool(core_theme),
            "match_level": match_level,
            "domain": domain,
            "explanation": explanation,
            "should_show": should_show,
            "display_level": display_level,
            # V10.0：多维度评估指标
            "resource_quality": round(resource_quality, 2),
            "content_completeness": round(content_completeness, 2),
            "teaching_value": round(teaching_value, 2),
            "comprehensiveness": round(comprehensiveness, 2),
            # V11.0：概念层级因子
            "concept_hierarchy_factor": round(concept_hierarchy_factor, 2)
        }
    
    def _match_single_theme_precise(
        self,
        theme: str,
        structured: Dict[str, str],
        lesson_title: str,
        lesson_content: str,
        query_themes: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        V11.6：连续匹配度评估，替代刚性判断
        
        改进：
        - 从刚性次数要求改为连续匹配度评估
        - 支持同一主题的多种表达方式
        - 实现平滑的匹配级别过渡
        - V11.6：区分"一般函数概念"和"具体函数概念"
        - V27.0：添加metadata参数，支持路径冲突检测
        - V61.0：在匹配之前先检查路径冲突
        
        Returns:
            包含匹配结果的字典，或None
        """
        # V62.0改进：导入re模块用于正则表达式匹配
        import re
        
        # V61.0改进：在匹配之前先检查路径冲突
        # V62.0改进：修复路径冲突检测逻辑，避免"第四章"同时匹配指数和对数章节
        if metadata and metadata.get('source_file'):
            source_file = metadata.get('source_file', '')
            
            # V62.0改进：检查是否在三角函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配5.4、5.5、5.6章节
            trigonometry_pattern = r'教案[\\\/]第五章[^\\\/]*[\\\/](5\.4|5\.5|5\.6|5-4|5-5|5-6|三角函数)[\\\/]'
            is_in_trigonometry_chapter = bool(re.search(trigonometry_pattern, source_file))
            
            # 检查当前主题是否与三角函数相关
            trigonometry_keywords = ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]
            current_theme_is_trig = any(trig_keyword in theme for trig_keyword in trigonometry_keywords)
            
            # 如果资源在三角函数章节，但当前主题不是三角函数，则存在路径冲突
            if is_in_trigonometry_chapter and not current_theme_is_trig:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在三角函数章节，但主题 '{theme}' 不是三角函数")
                return None
            
            # V62.0改进：检查是否在二次函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配2.3章节
            quadratic_pattern = r'教案[\\\/](第二章|2\.3|2-3|二次函数)[\\\/]'
            is_in_quadratic_chapter = bool(re.search(quadratic_pattern, source_file))
            
            # 检查当前主题是否与二次函数相关
            quadratic_keywords = ["二次函数", "抛物线", "顶点", "对称轴"]
            current_theme_is_quadratic = any(quad_keyword in theme for quad_keyword in quadratic_keywords)
            
            # 如果资源在二次函数章节，但当前主题不是二次函数，则存在路径冲突
            if is_in_quadratic_chapter and not current_theme_is_quadratic:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在二次函数章节，但主题 '{theme}' 不是二次函数")
                return None
            
            # V62.0改进：检查是否在指数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.1和4.2章节
            exponential_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.1|4\.2|4-1|4-2|指数函数)[\\\/]'
            is_in_exponential_chapter = bool(re.search(exponential_pattern, source_file))
            
            # 检查当前主题是否与指数函数相关
            exponential_keywords = ["指数函数", "指数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            
            # 如果资源在指数函数章节，但当前主题不是指数函数，则存在路径冲突
            if is_in_exponential_chapter and not current_theme_is_exponential:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在指数函数章节，但主题 '{theme}' 不是指数函数")
                return None
            
            # V62.0改进：检查是否在对数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.3和4.4章节
            logarithmic_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.3|4\.4|4-3|4-4)[\\\/]'
            is_in_logarithmic_chapter = bool(re.search(logarithmic_pattern, source_file))
            
            # 检查当前主题是否与对数函数相关
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在对数函数章节，但当前主题不是对数函数，则存在路径冲突
            if is_in_logarithmic_chapter and not current_theme_is_logarithmic:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在对数函数章节，但主题 '{theme}' 不是对数函数")
                return None
        
        # 提取主题关键词（包括变体和同义词）
        theme_keywords = self._extract_theme_keywords(theme)
        
        # 0. 严格检查标题匹配（标题必须包含完整主题词）
        title_lower = lesson_title.lower()
        theme_lower = theme.lower()
        
        # V11.6：判断是否是"一般函数概念"
        specific_function_types = ["指数", "对数", "幂", "三角", "正弦", "余弦", "正切", "反三角", "二次"]
        is_general_function_concept = theme.startswith("函数的")
        is_specific_function_concept = any(theme.startswith(ft) or (ft in theme and "函数" in theme) for ft in specific_function_types)
        
        # V11.6：检查标题是否包含"具体函数概念"
        title_has_specific_function = any(ft in title_lower for ft in specific_function_types)
        
        # 标题完全匹配或包含完整主题词
        if theme_lower in title_lower:
            # V11.6：如果主题是"一般函数概念"，而标题包含"具体函数概念"，则降级匹配
            if is_general_function_concept and not is_specific_function_concept and title_has_specific_function:
                # 例如："函数的概念"不应该匹配"三角函数的概念"
                # 降级为相关主题匹配
                base_score = 0.70
                weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "related",
                    "score": final_score,
                    "evidence": ["标题包含相关概念（具体函数概念）"]
                }
            
            # 计算权重因子
            # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
            final_score = 0.95 * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "core",
                "score": final_score,
                "evidence": ["标题完全匹配"]
            }
        
        # 检查标题是否包含主题的核心关键词或变体
        core_keywords = self._get_theme_variants(theme)
        for keyword in core_keywords:
            if keyword.lower() in title_lower:
                # V11.6：如果主题是"一般函数概念"，而标题包含"具体函数概念"，则降级匹配
                if is_general_function_concept and not is_specific_function_concept and title_has_specific_function:
                    base_score = 0.65
                    # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
                    weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                    # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
                    if weight_factor == 0.0:
                        return None
                    hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                    final_score = base_score * weight_factor * hierarchy_factor
                    return {
                        "theme": theme,
                        "level": "related",
                        "score": final_score,
                        "evidence": ["标题包含相关概念（具体函数概念）"]
                    }
                
                # 计算权重因子
                # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
                weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
                if weight_factor == 0.0:
                    return None
                # 计算概念层级因子
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                final_score = 0.90 * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "core",
                    "score": final_score,
                    "evidence": ["标题核心词匹配"]
                }
        
        # 1. 检查教学目标（核心主题）- 连续评估
        objectives = structured.get("objectives", "")
        core_matches = self._count_keyword_matches(theme_keywords, objectives)
        
        if core_matches >= 3:
            # 高匹配度：核心主题
            base_score = 0.88
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "core",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        elif core_matches == 2:
            # 中等匹配度：强相关主题
            base_score = 0.75
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        elif core_matches == 1:
            # 弱匹配度：相关主题
            base_score = 0.70
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        
        # 2. 检查教学重难点（相关主题）- 连续评估
        key_points = structured.get("key_points", "")
        important_matches = self._count_keyword_matches(theme_keywords, key_points)
        
        if important_matches >= 3:
            # 高匹配度：相关主题
            base_score = 0.75
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        elif important_matches == 2:
            # 中等匹配度：相关主题
            base_score = 0.65
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        elif important_matches == 1:
            # 弱匹配度：提及主题
            base_score = 0.50
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        
        # 3. 检查教学过程（提及主题）- 连续评估
        process = structured.get("process", "")
        process_matches = self._count_keyword_matches(theme_keywords, process)
        
        if process_matches >= 8:
            # 高匹配度：相关主题
            base_score = 0.60
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        elif process_matches >= 5:
            # 中等匹配度：提及主题
            base_score = 0.45
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        elif process_matches >= 2:
            # 弱匹配度：提及主题
            base_score = 0.35
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        
        # 4. 检查主题层级关系（相关主题）- V10.0：连续评估
        if self._is_related_theme(theme, lesson_title, lesson_content):
            # 计算领域距离因子
            distance_factor = self._calculate_domain_distance_factor(theme, lesson_title, lesson_content)
            
            # V10.0：方向控制作为权重因子
            direction_factor = self._calculate_direction_factor(theme, lesson_title, lesson_content)
            
            # 计算综合权重因子
            weight_factor = (distance_factor + direction_factor) / 2
            
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            
            # 计算概念层级因子
            lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
            if lesson_theme:
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_theme)
            else:
                hierarchy_factor = 1.0
            
            if self._is_downward_recommendation(theme, lesson_title, lesson_content):
                base_score = 0.60
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "related",
                    "score": final_score,  # 应用权重因子
                    "evidence": ["主题层级关系匹配（向下推荐）"]
                }
            else:
                # 向上推荐（子→父）：作为权重因子
                base_score = 0.40
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "mentioned",
                    "score": final_score,  # 应用权重因子
                    "evidence": ["主题层级关系匹配（向上推荐）"]
                }
        
        return None
    
    def _determine_domain(self, core_theme: Optional[str], related_themes: List[str], lesson_title: str, lesson_content: str) -> str:
        """
        根据核心主题和相关主题确定领域
        
        优先级：
        1. 核心主题对应的领域
        2. 相关主题中最相关的领域
        3. 标题和内容分析
        4. 默认领域（其他）
        """
        # 1. 核心主题对应的领域
        if core_theme:
            domain = self.theme_domain_map.get(core_theme)
            if domain:
                return domain
        
        # 2. 相关主题中最相关的领域
        for theme in related_themes:
            domain = self.theme_domain_map.get(theme)
            if domain:
                return domain
        
        # 3. 标题和内容分析
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # 检查三角函数相关
        if any(keyword in full_text for keyword in ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]):
            return "三角函数"
        
        # 检查具体函数相关
        if any(keyword in full_text for keyword in ["指数函数", "对数函数", "幂函数"]):
            return "具体函数"
        
        # 检查一般函数相关
        if any(keyword in full_text for keyword in ["函数的概念", "函数的表示法", "函数的性质", "单调性", "奇偶性", "周期性"]):
            return "一般函数"
        
        # 4. 默认领域
        return "其他"
    
    def _is_related_theme(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.1：检查主题是否与教案内容相关（基于主题层级关系）
        
        改进：区分推荐方向
        - 向下推荐（父→子）：允许
        - 向上推荐（子→父）：需要额外检查
        """
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # 检查主题是否在层级关系中
        for parent_theme, child_themes in self.theme_hierarchy.items():
            if theme == parent_theme:
                # 检查是否包含子主题（向下推荐）
                for child_theme in child_themes:
                    if child_theme.lower() in full_text:
                        return True
            elif theme in child_themes:
                # 检查是否包含父主题（向上推荐）
                if parent_theme.lower() in full_text:
                    return True
        
        return False
    
    def _contains_exclusion_words(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.2：检查文本中是否包含主题的排除词
        
        注意：此方法已被 _calculate_exclusion_factor 替代
        """
        return False
    
    def _calculate_domain_distance_factor(self, theme: str, lesson_title: str, lesson_content: str) -> float:
        """
        V9.1：计算领域距离因子
        
        领域距离定义：
        - 距离0：同一具体主题，因子1.0
        - 距离1：同一分支的不同具体主题，因子0.8
        - 距离2：同一大类下的不同分支，因子0.5
        - 距离3：不同大类，因子0.2
        
        用于降低跨领域推荐的相关性分数
        """
        # 提取教案的主题
        lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
        
        if not lesson_theme:
            return 1.0  # 无法确定主题，不降低分数
        
        # 查找领域距离
        distance = self.domain_distance.get((theme, lesson_theme))
        
        if distance is None:
            return 1.0  # 没有定义距离，不降低分数
        
        # 根据距离返回因子
        distance_factors = {
            0: 1.0,
            1: 0.8,
            2: 0.5,
            3: 0.2
        }
        
        return distance_factors.get(distance, 1.0)
    
    def _extract_lesson_theme(self, lesson_title: str, lesson_content: str) -> Optional[str]:
        """
        V9.1：从教案中提取主题
        
        用于计算领域距离
        """
        # 尝试从标题中提取主题
        title_lower = lesson_title.lower()
        
        # 检查常见主题
        # V24.4改进：添加一次函数
        common_themes = [
            "指数函数", "对数函数", "幂函数", "三角函数", "二次函数", "一次函数",
            "函数的概念", "函数的单调性", "函数的奇偶性", "函数的周期性"
        ]
        
        for theme in common_themes:
            if theme in title_lower:
                return theme
        
        # 如果标题中没有，尝试从内容中提取
        content_lower = lesson_content.lower()
        for theme in common_themes:
            if theme in content_lower:
                return theme
        
        return None
    
    def _is_downward_recommendation(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.2：判断是否为向下推荐（父→子）
        
        向下推荐：用户查询父主题，推荐子主题（更具体的内容）
        向上推荐：用户查询子主题，推荐父主题（更泛化的内容）
        """
        # 提取教案的主题
        lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
        
        if not lesson_theme:
            return True  # 无法确定，默认允许
        
        # 检查是否为父子关系
        for parent_theme, child_themes in self.theme_hierarchy.items():
            if theme == parent_theme and lesson_theme in child_themes:
                # 向下推荐：父主题查询，子主题教案
                return True
            elif theme in child_themes and lesson_theme == parent_theme:
                # 向上推荐：子主题查询，父主题教案
                return False
        
        # 不是父子关系，默认允许
        return True
    
    def _calculate_weight_factor(self, theme: str, lesson_title: str, lesson_content: str, query_themes: List[str] = None, metadata: Dict[str, Any] = None) -> float:
        """
        V9.2：计算综合权重因子 - 改进版
        
        使用加权平均替代简单相乘，避免分数衰减过快
        
        改进：
        - 如果排除词因子为0.0，直接返回0.0，过滤掉不相关的资源
        - V27.0：添加metadata参数，支持路径冲突检测
        
        Args:
            theme: 当前主题
            lesson_title: 教案标题
            lesson_content: 教案内容
            query_themes: 查询的主题列表，用于过滤与其他查询主题相关的排除词
            metadata: 资源元数据，包含source_file等信息
        
        Returns:
            float: 综合权重因子 (0.0-1.0)
        """
        # 计算各个因子
        exclusion_factor = self._calculate_exclusion_factor(theme, lesson_title, lesson_content, query_themes, metadata)
        
        # 如果排除词因子为0.0，直接返回0.0，过滤掉不相关的资源
        if exclusion_factor == 0.0:
            return 0.0
        
        domain_factor = self._calculate_domain_distance_factor(theme, lesson_title, lesson_content)
        direction_factor = self._calculate_direction_factor(theme, lesson_title, lesson_content)
        
        # 使用加权平均计算综合因子
        weight_factor = (
            self.weight_factors["exclusion"] * exclusion_factor +
            self.weight_factors["domain"] * domain_factor +
            self.weight_factors["direction"] * direction_factor
        )
        
        return weight_factor
    
    def _calculate_overall_score(self, relevance_score: float, resource_quality: float, content_completeness: float, teaching_value: float, comprehensiveness: float) -> float:
        """
        V10.0：计算综合得分
        V62.0改进：当relevance_score为0时，overall_score也应该为0
        
        Args:
            relevance_score: 相关性分数
            resource_quality: 资源质量
            content_completeness: 内容完整性
            teaching_value: 教学价值
            comprehensiveness: 综合性
            
        Returns:
            综合得分
        """
        # V62.0改进：如果相关性分数为0，则综合得分也为0
        if relevance_score == 0.0:
            return 0.0
        
        # 权重配置
        weights = {
            "relevance": 0.4,      # 相关性权重
            "quality": 0.2,        # 资源质量权重
            "completeness": 0.15,  # 内容完整性权重
            "teaching": 0.15,      # 教学价值权重
            "comprehensive": 0.1   # 综合性权重
        }
        
        # 计算加权和
        total_score = (
            relevance_score * weights["relevance"] +
            resource_quality * weights["quality"] +
            content_completeness * weights["completeness"] +
            teaching_value * weights["teaching"] +
            comprehensiveness * weights["comprehensive"]
        )
        
        return total_score
    
    def _calculate_resource_quality(self, lesson_title: str, lesson_content: str, structured: Dict[str, str]) -> float:
        """
        V10.0：计算资源质量
        
        基于标题质量、内容长度、结构完整性等因素
        """
        score = 0.0
        
        # 标题质量（长度、专业性）
        if lesson_title and len(lesson_title) >= 5:
            score += 0.3
        
        # 内容长度
        content_length = len(lesson_content)
        if content_length > 1000:
            score += 0.3
        elif content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.1
        
        # 结构完整性
        structure_score = 0.0
        if structured.get("objectives"):
            structure_score += 0.1
        if structured.get("key_points"):
            structure_score += 0.1
        if structured.get("process"):
            structure_score += 0.1
        score += structure_score
        
        # 确保分数在0-1之间
        return min(1.0, score)
    
    def _calculate_content_completeness(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算内容完整性
        
        基于各章节内容的完整性
        """
        score = 0.0
        
        # 教学目标完整性
        objectives = structured.get("objectives", "")
        if objectives:
            if len(objectives) > 200:
                score += 0.3
            elif len(objectives) > 100:
                score += 0.2
            else:
                score += 0.1
        
        # 教学重难点完整性
        key_points = structured.get("key_points", "")
        if key_points:
            if len(key_points) > 150:
                score += 0.3
            elif len(key_points) > 75:
                score += 0.2
            else:
                score += 0.1
        
        # 教学过程完整性
        process = structured.get("process", "")
        if process:
            if len(process) > 500:
                score += 0.4
            elif len(process) > 250:
                score += 0.3
            elif len(process) > 100:
                score += 0.2
            else:
                score += 0.1
        
        # 确保分数在0-1之间
        return min(1.0, score)
    
    def _calculate_teaching_value(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算教学价值
        
        基于教学目标的明确性、重难点的突出程度等
        """
        score = 0.0
        
        # 教学目标明确性
        objectives = structured.get("objectives", "")
        if objectives:
            # 检查是否包含具体的学习目标
            if any(keyword in objectives for keyword in ["理解", "掌握", "应用", "学会", "了解"]):
                score += 0.4
            else:
                score += 0.2
        
        # 重难点突出程度
        key_points = structured.get("key_points", "")
        if key_points:
            # 检查是否明确标注重点和难点
            if any(keyword in key_points for keyword in ["重点", "难点", "关键"]):
                score += 0.3
            else:
                score += 0.15
        
        # 教学过程的详细程度
        process = structured.get("process", "")
        if process:
            # 检查是否包含具体的教学步骤
            if any(keyword in process for keyword in ["步骤", "环节", "活动", "练习"]):
                score += 0.3
            else:
                score += 0.15
        
        # 确保分数在0-1之间
        return min(1.0, score)
    
    def _calculate_comprehensiveness(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算综合性
        
        基于内容的全面性、涵盖的知识点等
        """
        score = 0.0
        
        # 内容全面性
        content_parts = 0
        if structured.get("objectives"):
            content_parts += 1
        if structured.get("key_points"):
            content_parts += 1
        if structured.get("process"):
            content_parts += 1
        
        # 根据内容部分数量计算分数
        if content_parts == 3:
            score += 0.6
        elif content_parts == 2:
            score += 0.4
        elif content_parts == 1:
            score += 0.2
        
        # 检查是否包含多个教学环节
        process = structured.get("process", "")
        if process:
            # 简单判断：检查是否包含多个段落或环节
            if process.count('\n') >= 3:
                score += 0.4
            elif process.count('\n') >= 1:
                score += 0.2
        
        # 确保分数在0-1之间
        return min(1.0, score)
    
    def _calculate_concept_hierarchy_factor(self, query_theme: str, lesson_theme: str) -> float:
        """
        V10.0：计算概念层级关系因子
        
        Args:
            query_theme: 查询主题
            lesson_theme: 教案主题
            
        Returns:
            层级关系因子 (0.0-1.0)
        """
        # 完全匹配
        if query_theme == lesson_theme:
            return 1.0
        
        # 检查是否为子概念
        if query_theme in self.concept_hierarchy:
            if lesson_theme in self.concept_hierarchy[query_theme].get("子概念", []):
                return 0.9  # 子概念匹配
        
        # 检查是否为父概念
        for parent, info in self.concept_hierarchy.items():
            if query_theme in info.get("子概念", []) and parent == lesson_theme:
                return 0.7  # 父概念匹配
        
        # 检查是否为相关概念
        if query_theme in self.concept_hierarchy:
            if lesson_theme in self.concept_hierarchy[query_theme].get("相关概念", []):
                return 0.6  # 相关概念匹配
        
        # 无层级关系
        return 0.5
    
    def _calculate_exclusion_factor(self, theme: str, lesson_title: str, lesson_content: str, query_themes: List[str] = None, metadata: Dict[str, Any] = None) -> float:
        """
        V18.0：计算排除词因子 - 智能版
        
        如果包含排除词，返回0.0的因子，直接排除
        
        V18.0改进：
        1. 对于组合查询（如"二次函数和一次函数"），不过滤掉查询主题相关的排除词
        2. 对于单一主题查询，严格过滤掉包含其他主题关键词的资源
        3. 增加对习题内容的智能分析，避免误过滤
        4. V27.0：添加路径冲突检测，根据文件路径中的章节信息判断主题冲突
        
        Args:
            theme: 当前主题
            lesson_title: 教案标题
            lesson_content: 教案内容
            query_themes: 查询的主题列表，用于过滤与其他查询主题相关的排除词
            metadata: 资源元数据，包含source_file等信息
        
        Returns:
            float: 排除词因子 (0.0-1.0)
        """
        exclusion_words = self.theme_exclusion_words.get(theme, [])
        if not exclusion_words:
            return 1.0
        
        # V62.0改进：导入re模块用于正则表达式匹配
        import re
        
        # V62.0改进：路径冲突检测
        # 检查文件路径中的章节信息，判断是否存在主题冲突
        if metadata and metadata.get('source_file'):
            source_file = metadata.get('source_file', '')
            
            # V62.0改进：检查是否在三角函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配5.4、5.5、5.6章节
            trigonometry_pattern = r'教案[\\\/]第五章[^\\\/]*[\\\/](5\.4|5\.5|5\.6|5-4|5-5|5-6|三角函数)[\\\/]'
            is_in_trigonometry_chapter = bool(re.search(trigonometry_pattern, source_file))
            
            # 检查当前主题是否与三角函数相关
            trigonometry_keywords = ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]
            current_theme_is_trig = any(trig_keyword in theme for trig_keyword in trigonometry_keywords)
            
            # 如果资源在三角函数章节，但当前主题不是三角函数，则存在路径冲突
            if is_in_trigonometry_chapter and not current_theme_is_trig:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在三角函数章节，但主题 '{theme}' 不是三角函数")
                return 0.0
            
            # V62.0改进：检查是否在二次函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配2.3章节
            quadratic_pattern = r'教案[\\\/](第二章|2\.3|2-3|二次函数)[\\\/]'
            is_in_quadratic_chapter = bool(re.search(quadratic_pattern, source_file))
            
            # 检查当前主题是否与二次函数相关
            quadratic_keywords = ["二次函数", "抛物线", "顶点", "对称轴"]
            current_theme_is_quadratic = any(quad_keyword in theme for quad_keyword in quadratic_keywords)
            
            # 如果资源在二次函数章节，但当前主题不是二次函数，则存在路径冲突
            if is_in_quadratic_chapter and not current_theme_is_quadratic:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在二次函数章节，但主题 '{theme}' 不是二次函数")
                return 0.0
            
            # V62.0改进：检查是否在指数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.1和4.2章节
            exponential_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.1|4\.2|4-1|4-2|指数函数)[\\\/]'
            is_in_exponential_chapter = bool(re.search(exponential_pattern, source_file))
            
            # 检查当前主题是否与指数函数相关
            exponential_keywords = ["指数函数", "指数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            
            # 如果资源在指数函数章节，但当前主题不是指数函数，则存在路径冲突
            if is_in_exponential_chapter and not current_theme_is_exponential:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在指数函数章节，但主题 '{theme}' 不是指数函数")
                return 0.0
            
            # V62.0改进：检查是否在对数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.3和4.4章节
            logarithmic_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.3|4\.4|4-3|4-4)[\\\/]'
            is_in_logarithmic_chapter = bool(re.search(logarithmic_pattern, source_file))
            
            # 检查当前主题是否与对数函数相关
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在对数函数章节，但当前主题不是对数函数，则存在路径冲突
            if is_in_logarithmic_chapter and not current_theme_is_logarithmic:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在对数函数章节，但主题 '{theme}' 不是对数函数")
                return 0.0
        
        # V18.0改进：智能过滤排除词
        # 对于组合查询，如果排除词是查询主题之一，则不过滤
        filtered_exclusion_words = []
        if query_themes:
            for word in exclusion_words:
                # 检查排除词是否是查询主题之一
                is_query_theme = False
                for query_theme in query_themes:
                    if word in query_theme or query_theme in word:
                        is_query_theme = True
                        break
                
                if not is_query_theme:
                    filtered_exclusion_words.append(word)
        else:
            filtered_exclusion_words = exclusion_words
        
        print(f"      🔍 主题 '{theme}' 的排除词: {exclusion_words}")
        print(f"      🔍 查询主题: {query_themes}")
        print(f"      🔍 过滤后的排除词: {filtered_exclusion_words}")
        
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # V54.2改进：根据资源类型调整排除词检查策略
        # 教案、课件、GGB等不同类型的资源应该有不同的检查策略
        resource_type = metadata.get('resource_type', 'unknown') if metadata else 'unknown'
        is_lesson_plan = resource_type == 'lesson_plan' or '教案' in lesson_title or '教学设计' in lesson_title or '导学案' in lesson_title
        is_courseware = resource_type == 'courseware' or '课件' in lesson_title or 'PPT' in lesson_title
        is_ggb = resource_type == 'ggb' or 'GGB' in lesson_title or 'GeoGebra' in lesson_title
        is_syllabus = resource_type == 'syllabus' or '教学大纲' in lesson_title or '大纲' in lesson_title
        is_lesson_case = resource_type == 'lesson_case' or '课例' in lesson_title or '教学案例' in lesson_title
        is_exercise = resource_type == 'exercise' or '习题' in lesson_title or '题目' in lesson_title
        
        # V63.1改进：根据资源类型调整章节路径检查
        # 不同类型的资源可能有不同的路径格式
        is_in_correct_chapter = False
        if metadata and metadata.get('source_file'):
            source_file = metadata.get('source_file', '')
            
            # 检查是否在指数函数章节（4.1或4.2）
            # V63.0修复：使用更简单的正则表达式，避免[^\/]*不匹配中文和空格的问题
            # V63.1改进：支持不同资源类型的路径格式
            exponential_patterns = [
                r'教案.*4\.[12].*指数函数',
                r'课件.*4\.[12].*指数函数',
                r'GGB.*4\.[12].*指数函数',
                r'课例.*4\.[12].*指数函数',
                r'教学大纲.*4\.[12].*指数函数'
            ]
            
            logarithmic_patterns = [
                r'教案.*4\.[34].*对数函数',
                r'课件.*4\.[34].*对数函数',
                r'GGB.*4\.[34].*对数函数',
                r'课例.*4\.[34].*对数函数',
                r'教学大纲.*4\.[34].*对数函数'
            ]
            
            is_in_exponential_chapter = any(bool(re.search(pattern, source_file)) for pattern in exponential_patterns)
            is_in_logarithmic_chapter = any(bool(re.search(pattern, source_file)) for pattern in logarithmic_patterns)
            
            # 检查当前主题
            exponential_keywords = ["指数函数", "指数"]
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在正确的章节路径中，标记为正确章节
            if is_in_exponential_chapter and current_theme_is_exponential:
                is_in_correct_chapter = True
                print(f"      ✅ V63.0章节匹配：资源在指数函数章节，主题也是指数函数，放宽排除词检查")
            elif is_in_logarithmic_chapter and current_theme_is_logarithmic:
                is_in_correct_chapter = True
                print(f"      ✅ V63.0章节匹配：资源在对数函数章节，主题也是对数函数，放宽排除词检查")
        
        # V18.0改进：对于习题资源，进行更智能的排除词检查
        # 检查是否包含任何排除词
        for word in filtered_exclusion_words:
            if word.lower() in full_text:
                # V61.0改进：严格检查教案资源的排除词
                # V63.0改进：如果资源在正确的章节路径中，放宽排除词检查
                # V63.1改进：根据资源类型调整排除词检查策略
                if is_lesson_plan:
                    # 如果排除词在标题中，直接排除（即使在正确章节也排除）
                    if word.lower() in lesson_title.lower():
                        print(f"      ⚠️ V61.0教案资源严格过滤：'{lesson_title}' 标题包含排除词 '{word}'，直接排除")
                        return 0.0
                    
                    # V63.0改进：如果资源在正确的章节路径中，放宽排除词检查
                    if is_in_correct_chapter:
                        print(f"      ✅ V63.0放宽检查：'{lesson_title}' 在正确章节路径中，包含排除词 '{word}' 但允许通过")
                        continue
                    
                    # 如果排除词在内容中，检查是否是主要知识点
                    # 通过检查排除词周围的上下文判断
                    # 简单判断：如果排除词出现次数较多，说明是主要知识点
                    word_count = full_text.lower().count(word.lower())
                    if word_count >= 3:
                        print(f"      ⚠️ V61.0教案资源严格过滤：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，排除")
                        return 0.0
                elif is_courseware or is_ggb or is_syllabus or is_lesson_case:
                    # 对于课件、GGB、教学大纲、课例资源，更宽松地处理排除词
                    # 这些资源类型通常包含多个主题的内容
                    print(f"      ✅ V63.1放宽检查：'{lesson_title}' 是{resource_type}资源，包含排除词 '{word}' 但允许通过")
                    continue
                elif is_exercise:
                    # V18.0改进：对于习题资源，进行更智能的排除词检查
                    # 对于习题资源，检查排除词是否是主要知识点
                    # 通过检查排除词出现的次数来判断
                    word_count = full_text.lower().count(word.lower())
                    if word_count >= 2:
                        print(f"      ⚠️ V18.0习题资源过滤：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，排除")
                        return 0.0
                    else:
                        print(f"      ✅ V18.0习题资源放宽检查：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，允许通过")
                        continue
                
                # V18.0改进：对于组合查询，如果资源同时包含查询主题的关键词，则不过滤
                if query_themes and len(query_themes) > 1:
                    # 检查资源是否包含查询主题的关键词
                    has_query_theme_keyword = False
                    for query_theme in query_themes:
                        if query_theme.lower() in full_text:
                            has_query_theme_keyword = True
                            break
                    
                    if has_query_theme_keyword:
                        print(f"      ✅ V18.0智能过滤：'{lesson_title}' 包含排除词 '{word}'，但同时包含查询主题关键词，允许通过")
                        continue
                
                # 包含排除词，返回0.0的因子，直接排除
                print(f"      ⚠️ 排除：'{lesson_title}' 包含排除词 '{word}' (主题: {theme})")
                return 0.0
        
        return 1.0
    
    def _calculate_direction_factor(self, theme: str, lesson_title: str, lesson_content: str) -> float:
        """
        V9.2：计算方向控制因子
        
        向下推荐（父→子）：1.0
        向上推荐（子→父）：0.6
        其他：1.0
        
        Returns:
            float: 方向控制因子 (0.6-1.0)
        """
        if self._is_downward_recommendation(theme, lesson_title, lesson_content):
            return 1.0  # 向下推荐，不降低分数
        else:
            return 0.6  # 向上推荐，适度降低分数
    
    def _calculate_dynamic_threshold(self, query: str, core_theme_count: int) -> float:
        """
        V9.2：计算动态阈值
        
        根据查询明确度和核心主题数量自动调整阈值
        
        Args:
            query: 用户查询
            core_theme_count: 核心主题数量
        
        Returns:
            float: 动态调整后的阈值
        """
        # 基础阈值
        threshold = self.base_related_theme_threshold
        
        # 根据核心主题数量调整
        if core_theme_count == 0:
            # 没有核心主题，降低阈值以展示更多相关内容
            threshold -= 0.1
        elif core_theme_count >= 3:
            # 核心主题较多，提高阈值以保证质量
            threshold += 0.1
        
        # 根据查询长度判断明确度
        query_length = len(query)
        if query_length >= 10:
            # 查询较长，比较明确，提高阈值
            threshold += 0.05
        elif query_length <= 4:
            # 查询较短，比较泛化，降低阈值
            threshold -= 0.05
        
        # 确保阈值在合理范围内
        threshold = max(0.3, min(0.7, threshold))
        
        return threshold
    
    def _get_display_level(self, score: float) -> str:
        """
        V9.2：根据分数确定展示级别
        
        Args:
            score: 相关性分数
        
        Returns:
            str: 展示级别 (core/related/extended/candidate)
        """
        if score >= self.display_levels["core"]["min_score"]:
            return "core"
        elif score >= self.display_levels["related"]["min_score"]:
            return "related"
        elif score >= self.display_levels["extended"]["min_score"]:
            return "extended"
        elif score >= self.display_levels["candidate"]["min_score"]:
            return "candidate"
        else:
            return "none"
    
    def _extract_theme_keywords(self, theme: str) -> List[str]:
        """提取主题关键词"""
        # 主题到关键词的映射
        theme_keyword_map = {
            "函数的概念": ["函数的概念", "函数定义", "函数的三要素", "定义域", "值域", "对应关系"],
            "函数的表示法": ["函数的表示法", "表示法", "解析法", "列表法", "图像法"],
            "函数的单调性": ["单调性", "单调递增", "单调递减", "增函数", "减函数"],
            "函数的奇偶性": ["奇偶性", "奇函数", "偶函数", "对称性"],
            "函数的周期性": ["周期性", "周期函数", "最小正周期"],
            "函数的应用": ["函数的应用", "应用", "实际应用", "生活应用", "数学建模"],
            "函数的零点": ["函数的零点", "零点", "方程求解", "解方程", "方程根"],
            "指数函数": ["指数函数", "指数", "指数幂", "指数增长", "指数衰减", "放射性衰变"],
            "对数函数": ["对数函数", "对数", "对数运算"],
            "幂函数": ["幂函数", "幂"],
            "三角函数": ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan", "周期性变化", "波形"],
            "正弦函数": ["正弦函数", "正弦", "sin"],
            "余弦函数": ["余弦函数", "余弦", "cos"],
            "正切函数": ["正切函数", "正切", "tan"],
            "二次函数": ["二次函数", "抛物线", "顶点", "对称轴", "开口", "二次"],
        }
        
        # 返回主题对应的关键词列表，如果没有则返回主题本身
        keywords = theme_keyword_map.get(theme, [theme])
        return keywords
    
    def _get_theme_variants(self, theme: str) -> List[str]:
        """
        V11.7：动态获取主题的变体和同义词
        
        支持同一主题的多种表达方式，提高匹配灵活性
        动态提取核心概念，避免静态映射的局限性
        
        V11.7改进：
        - 更严格地控制"一般函数概念"的变体生成
        - "函数的概念"只生成明确相关的变体，不生成"函数"等过于宽泛的变体
        - 区分"一般函数概念"和"具体函数概念"
        
        Args:
            theme: 主题名称
            
        Returns:
            主题变体列表
        """
        # 主题变体映射（仅保留一些特殊的、难以动态处理的映射）
        theme_variants = {
            "函数的概念": ["函数概念", "函数定义", "函数的定义", "函数的基本概念"],
            "函数的单调性": ["函数单调性", "单调性", "函数的增减性", "函数的增减"],
            "函数的奇偶性": ["函数奇偶性", "奇偶性", "函数的对称性", "函数对称性"],
            "函数的周期性": ["函数周期性", "周期性", "函数的周期"],
            "函数的应用": ["函数应用", "应用", "实际应用", "生活应用", "数学建模", "函数模型"],
            "函数的零点": ["函数零点", "零点", "方程求解", "解方程", "方程根", "方程的解"],
            "正弦函数": ["sin函数", "sin", "正弦"],
            "余弦函数": ["cos函数", "cos", "余弦"],
            "正切函数": ["tan函数", "tan", "正切"],
            "二次函数": ["二次函数", "抛物线", "二次", "一元二次"],
            "指数函数": ["指数函数", "指数", "指数增长", "指数衰减"],
            "对数函数": ["对数函数", "对数", "log", "ln"],
            "幂函数": ["幂函数", "幂", "幂运算"],
            "三角函数": ["三角函数", "三角", "正弦", "余弦", "正切", "sin", "cos", "tan"],
        }
        
        # 提取核心关键词
        core_variants = theme_variants.get(theme, [])
        
        # 自动生成一些变体
        auto_variants = []
        
        # V11.7：区分"一般函数概念"和"具体函数概念"
        # 具体函数类型列表
        specific_function_types = ["指数", "对数", "幂", "三角", "正弦", "余弦", "正切", "反三角", "二次"]
        
        # 判断是否是"一般函数概念"（如"函数的概念"、"函数的性质"）
        is_general_function_concept = False
        if theme.startswith("函数的"):
            # 检查是否是"函数的概念"、"函数的性质"等一般概念
            # 而不是"指数函数的概念"等具体概念
            is_general_function_concept = True
        
        # 判断是否是"具体函数概念"（如"指数函数的概念"）
        is_specific_function_concept = False
        matched_func_type = None
        for func_type in specific_function_types:
            if theme.startswith(func_type) or (func_type in theme and "函数" in theme):
                is_specific_function_concept = True
                matched_func_type = func_type
                break
        
        # V11.7：动态提取核心概念
        # 常见的后缀模式，移除这些后缀可以得到核心概念
        suffix_patterns = [
            "的概念", "的概念与意义",
            "的性质", "的性质与应用",
            "的图像", "的图像与性质",
            "的定义", "的定义域",
            "的运算", "的运算法则",
            "的应用", "的应用举例",
            "的公式", "的公式推导"
        ]
        
        # 尝试移除后缀，提取核心概念
        for suffix in suffix_patterns:
            if theme.endswith(suffix):
                core_concept = theme[:-len(suffix)]
                
                # V11.7：只有"具体函数概念"才添加核心概念作为变体
                # "一般函数概念"不添加核心概念作为变体（避免"函数的概念" -> "函数"）
                if is_specific_function_concept and matched_func_type:
                    auto_variants.append(core_concept)
                    
                    # 同时生成带后缀的变体
                    for other_suffix in suffix_patterns:
                        if other_suffix != suffix:
                            auto_variants.append(core_concept + other_suffix)
                break
        
        # V11.7：处理"具体函数"相关的主题
        if is_specific_function_concept and matched_func_type:
            # 添加函数类型作为变体
            auto_variants.append(matched_func_type + "函数")
            # 添加不带"函数"的变体
            auto_variants.append(matched_func_type)
        
        # V11.7：对于"一般函数概念"，移除"的"字生成变体
        # 对于其他主题，也移除"的"字生成变体
        if "的" in theme:
            # V11.7：对于"一般函数概念"，确保变体不包含"函数"单独出现
            if is_general_function_concept:
                variant = theme.replace("的", "")
                # 如果变体不是"函数"，才添加
                if variant != "函数":
                    auto_variants.append(variant)
            else:
                auto_variants.append(theme.replace("的", ""))
        
        # V11.7：移除"函数"后缀（仅对非一般函数概念）
        if theme.endswith("函数") and not is_general_function_concept:
            auto_variants.append(theme[:-2])
        
        # V11.7：移除"函数的"前缀（仅对一般函数概念，但不添加"概念"作为变体）
        # 不执行此操作，避免"函数的概念" -> "概念"
        
        # 合并并去重
        all_variants = list(set(core_variants + auto_variants))
        
        # 确保返回的变体不为空
        if not all_variants:
            return [theme]
        
        return all_variants
    
    def _count_keyword_matches(self, keywords: List[str], text: str) -> int:
        """计算关键词在文本中的匹配次数"""
        if not text:
            return 0
        
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            count += text_lower.count(keyword.lower())
        return count
    
    def _parse_lesson_plan(self, content: str) -> Dict[str, str]:
        """
        V11.4：增强教案结构解析的鲁棒性，支持表格格式
        
        改进：
        - 支持多种章节标题表述方式
        - 处理混合格式和无明确章节划分的情况
        - 提高解析的灵活性和准确性
        - 支持表格格式的内容（Markdown表格）
        - 合并"教学重点"和"教学难点"
        """
        structured = {
            "objectives": "",
            "key_points": "",
            "process": "",
            "full_content": content
        }
        
        if not content:
            return structured
        
        lines = content.split('\n')
        current_section = None
        section_content = []
        in_table = False
        table_buffer = []
        
        # V11.4：章节标题关键词列表（增强版）
        section_keywords = {
            "objectives": [
                "教学目标", "学习目标", "教学目的", "学习目的", "课程目标",
                "目标", "教学要求", "学习要求", "教学任务", "学习任务",
                "课程目标", "教学目标与核心素养"
            ],
            "key_points": [
                "教学重难点", "重难点", "重点难点", "教学重点", "教学难点",
                "重点", "难点", "关键", "核心", "重点内容", "难点内容",
                "教学重点：", "教学难点："
            ],
            "process": [
                "教学过程", "教学实施", "教学步骤", "教学环节", "教学活动",
                "过程", "实施", "步骤", "环节", "活动", "教学流程", "教学安排"
            ]
        }
        
        # V11.4：章节标题模式匹配函数（增强版）
        # V53.8改进：支持Markdown格式（**标题**）
        def match_section(line):
            line_lower = line.lower().strip()
            
            # V53.8改进：去除Markdown格式标记
            line_clean = line_lower.replace('**', '').replace('*', '').replace('#', '').strip()
            
            # 特殊处理：如果同时包含"教学重点"和"教学难点"，识别为key_points
            if "教学重点" in line_lower and "教学难点" in line_lower:
                return "key_points"
            
            # 特殊处理：单独的"教学重点"或"教学难点"
            if "教学重点" in line_lower or "教学难点" in line_lower:
                return "key_points"
            
            for section, keywords in section_keywords.items():
                for keyword in keywords:
                    # V53.8改进：同时检查原始行和去除Markdown格式后的行
                    if keyword in line_lower or keyword in line_clean:
                        # 检查是否是标题（通常标题会有特殊标记或格式）
                        # 简单判断：包含关键词且长度较短
                        if len(line_clean) < 30 or any(mark in line for mark in ["：", ":", "、", "\t", " " * 4, "**"]):
                            return section
            return None
        
        # V11.4：用于合并"教学重点"和"教学难点"的内容
        key_points_parts = []
        
        # V11.4：解析表格行的函数
        def parse_table_row(line):
            """解析Markdown表格行，提取单元格内容"""
            if '|' not in line:
                return None
            # 分割表格单元格
            cells = [cell.strip() for cell in line.split('|')]
            # 过滤空单元格
            cells = [cell for cell in cells if cell]
            return cells
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # V11.4：检测表格开始/结束
            if '|' in line_stripped:
                if not in_table:
                    in_table = True
                    table_buffer = []
                table_buffer.append(line_stripped)
                continue
            else:
                if in_table:
                    # 表格结束，处理表格内容
                    in_table = False
                    # 解析表格内容
                    for table_line in table_buffer:
                        cells = parse_table_row(table_line)
                        if cells and len(cells) >= 2:
                            # 检查第一列是否是章节标题
                            first_col = cells[0].lower()
                            matched = match_section(first_col)
                            if matched:
                                # 将表格内容分配给对应章节
                                content_text = ' '.join(cells[1:])
                                if matched == "key_points":
                                    key_points_parts.append(content_text)
                                else:
                                    if structured[matched]:
                                        structured[matched] += '\n' + content_text
                                    else:
                                        structured[matched] = content_text
                    table_buffer = []
            
            # 识别章节标题（非表格行）
            matched_section = match_section(line_stripped)
            if matched_section:
                # 保存当前章节内容
                if current_section and section_content:
                    content_text = '\n'.join(section_content)
                    if current_section == "key_points":
                        key_points_parts.append(content_text)
                    else:
                        structured[current_section] = content_text
                # 开始新章节
                current_section = matched_section
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # 保存最后一个章节
        if current_section and section_content:
            content_text = '\n'.join(section_content)
            if current_section == "key_points":
                key_points_parts.append(content_text)
            else:
                structured[current_section] = content_text
        
        # V11.4：合并所有key_points部分
        if key_points_parts:
            structured["key_points"] = '\n'.join(key_points_parts)
        
        # V10.0：处理无明确章节划分的情况
        if not any([structured["objectives"], structured["key_points"], structured["process"]]):
            # 整个内容作为教学过程
            structured["process"] = content
        
        # V10.0：处理章节内容不完整的情况
        if not structured["objectives"]:
            # 尝试从内容中提取目标相关内容
            objectives_patterns = ["目标", "要求", "任务"]
            objectives_content = []
            for line in lines:
                line_lower = line.lower()
                if any(pattern in line_lower for pattern in objectives_patterns):
                    objectives_content.append(line)
            if objectives_content:
                structured["objectives"] = '\n'.join(objectives_content)
        
        return structured
    
    def _extract_query_themes(self, query: str) -> List[str]:
        """
        从查询中提取主题
        严格区分不同主题的核心意图
        """
        # 使用简单的主题提取逻辑
        themes = []
        
        # 常见的数学主题模式（精确匹配）
        # V24.2改进：添加一次函数主题
        # V31.0改进：调整主题顺序，具体函数主题优先于函数性质主题
        # V53.7改进：添加宽泛主题识别
        theme_patterns = [
            # 具体函数主题（优先匹配）
            "指数函数", "对数函数", "幂函数", "二次函数", "一次函数",
            "三角函数", "正弦函数", "余弦函数", "正切函数",
            
            # 具体函数的细分主题
            "指数函数的概念", "对数函数的概念", "幂函数的概念", "三角函数的概念", "二次函数的概念", "一次函数的概念",
            "指数函数的性质", "对数函数的性质", "幂函数的性质", "三角函数的性质", "二次函数的性质", "一次函数的性质",
            "指数函数的应用", "对数函数的应用", "幂函数的应用", "三角函数的应用", "二次函数的应用", "一次函数的应用",
            
            # 函数性质主题（次要匹配）
            "函数的概念", "函数的表示法", "函数的单调性", "函数的奇偶性", "函数的周期性",
            "函数的应用", "函数的零点"
        ]
        
        # V53.7改进：宽泛主题列表
        broad_themes = ["函数", "数学", "代数", "几何", "统计", "概率"]
        
        query_lower = query.lower()
        
        # 1. 优先匹配更具体的主题
        # 按长度排序，长的主题优先匹配
        sorted_patterns = sorted(theme_patterns, key=len, reverse=True)
        
        for pattern in sorted_patterns:
            if pattern in query_lower:
                themes.append(pattern)
                # 避免重复匹配
                query_lower = query_lower.replace(pattern, "")
        
        # 2. 如果没有匹配到主题，检查宽泛主题
        if not themes:
            for broad_theme in broad_themes:
                if broad_theme in query_lower:
                    themes.append(broad_theme)
                    print(f"🔗 宽泛主题识别: '{broad_theme}'")
                    break
        
        # 3. 检查是否是资源类型查询（如"教案"、"教学大纲"、"课件"等）
        resource_type_keywords = ["教案", "教学大纲", "课件", "课例视频", "ggb", "习题", "练习题", "题目"]
        resource_type_match = None
        for keyword in resource_type_keywords:
            if keyword in query_lower:
                resource_type_match = keyword
                break
        
        # 4. 如果是资源类型查询且没有匹配到主题，使用资源类型作为主题
        if not themes and resource_type_match:
            themes.append(resource_type_match)
            print(f"🔗 资源类型查询识别: '{resource_type_match}'")
        
        # 5. 如果没有匹配到主题，使用语义关联映射
        if not themes:
            # 检查语义关联
            for concept, core_theme in self.semantic_mappings.items():
                if concept in query_lower:
                    themes.append(core_theme)
                    print(f"🔗 语义关联: '{concept}' -> '{core_theme}'")
                    break
        
        # 6. 如果仍然没有匹配到任何主题，使用查询本身作为主题
        if not themes:
            themes.append(query)
            print(f"🔗 使用查询作为主题: '{query}'")
        
        return themes

# 全局实例
theme_matcher_v90 = None

def get_theme_matcher_v90() -> ThemeMatcherV90:
    """获取V9.0主题匹配器实例（单例模式）"""
    global theme_matcher_v90
    if theme_matcher_v90 is None:
        theme_matcher_v90 = ThemeMatcherV90()
    return theme_matcher_v90
