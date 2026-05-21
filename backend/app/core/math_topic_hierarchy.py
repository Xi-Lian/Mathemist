"""
数学主题层次结构和术语词典

职责：
- 定义数学主题的层次结构（知识图谱）
- 提供主题优先级识别
- 管理相关术语和非相关术语列表
- 支持查询主题提取和权重分配
- 提供概念关系查询（父子、兄弟、属性）
"""

from typing import Dict, List, Set, Tuple
import re


class MathTopicHierarchy:
    """数学主题层次结构 - 知识图谱"""
    
    # ==================== 第一层：数学概念树（完整层次结构）====================
    
    # 数学主题层次结构（从具体到通用）
    TOPIC_HIERARCHY: Dict[str, List[str]] = {
        # 代数
        "自然数": ["代数"],
        "整数": ["代数"],
        "有理数": ["代数"],
        "实数": ["代数"],
        "复数": ["代数"],
        
        "式与方程": ["代数"],
        "整式": ["式与方程", "代数"],
        "分式": ["式与方程", "代数"],
        "根式": ["式与方程", "代数"],
        "方程": ["式与方程", "代数"],
        "方程组": ["式与方程", "代数"],
        "一元一次方程": ["方程", "式与方程", "代数"],
        "一元二次方程": ["方程", "式与方程", "代数"],
        "二元一次方程组": ["方程组", "式与方程", "代数"],
        
        "函数": ["代数"],
        "一次函数": ["函数", "代数"],
        "二次函数": ["函数", "代数"],
        "反比例函数": ["函数", "代数"],
        "幂函数": ["函数", "代数"],
        "指数函数": ["函数", "代数"],
        "对数函数": ["函数", "代数"],
        "三角函数": ["函数", "代数"],
        "正弦函数": ["三角函数", "函数", "代数"],
        "余弦函数": ["三角函数", "函数", "代数"],
        "正切函数": ["三角函数", "函数", "代数"],
        "分段函数": ["函数", "代数"],
        
        "不等式": ["代数"],
        "一元一次不等式": ["不等式", "代数"],
        "一元二次不等式": ["不等式", "代数"],
        "基本不等式": ["不等式", "代数"],
        
        "数列": ["代数"],
        "等差数列": ["数列", "代数"],
        "等比数列": ["数列", "代数"],
        "递推数列": ["数列", "代数"],
        
        # 几何
        "几何": ["数学"],
        "平面几何": ["几何"],
        "三角形": ["平面几何", "几何"],
        "四边形": ["平面几何", "几何"],
        "圆": ["平面几何", "几何"],
        "相似": ["平面几何", "几何"],
        "全等": ["平面几何", "几何"],
        
        "解析几何": ["几何"],
        "直线": ["解析几何", "几何"],
        "圆锥曲线": ["解析几何", "几何"],
        "参数方程": ["解析几何", "几何"],
        
        "立体几何": ["几何"],
        "点线面": ["立体几何", "几何"],
        "柱锥台球": ["立体几何", "几何"],
        "空间向量": ["立体几何", "几何"],
        
        # 统计与概率
        "统计与概率": ["数学"],
        "统计": ["统计与概率"],
        "数据收集": ["统计", "统计与概率"],
        "数据整理": ["统计", "统计与概率"],
        "数据分析": ["统计", "统计与概率"],
        "统计推断": ["统计", "统计与概率"],
        
        "概率": ["统计与概率"],
        "随机事件": ["概率", "统计与概率"],
        "概率模型": ["概率", "统计与概率"],
        "概率分布": ["概率", "统计与概率"],
        
        # 微积分
        "微积分": ["数学"],
        "极限": ["微积分"],
        "导数": ["微积分"],
        "积分": ["微积分"],
        "微分方程": ["微积分"],
    }
    
    # ==================== 第二层：概念关系定义 ====================
    
    # 兄弟概念（易混淆概念）
    SIBLING_TOPICS: Dict[str, List[str]] = {
        "指数函数": ["对数函数", "幂函数", "二次函数"],
        "对数函数": ["指数函数", "幂函数"],
        "二次函数": ["一次函数", "指数函数", "三角函数"],
        "三角函数": ["指数函数", "对数函数", "二次函数"],
        "正弦函数": ["余弦函数", "正切函数"],
        "导数": ["积分"],
        "积分": ["导数"],
    }
    
    # 概念属性
    TOPIC_ATTRIBUTES: Dict[str, List[str]] = {
        "指数函数": ["定义域", "值域", "单调性", "图像特征", "底数"],
        "对数函数": ["定义域", "值域", "单调性", "图像特征", "底数"],
        "二次函数": ["顶点", "对称轴", "开口方向", "判别式", "图像"],
        "三角函数": ["周期", "振幅", "相位", "图像", "变换"],
        "导数": ["几何意义", "切线斜率", "单调性", "极值"],
        "积分": ["原函数", "定积分", "不定积分", "面积"],
    }
    
    # ==================== 第三层：概念域定义 ====================
    
    CONCEPT_DOMAINS: Dict[str, Set[str]] = {
        "函数域": {
            "一次函数", "二次函数", "反比例函数", "幂函数",
            "指数函数", "对数函数", "三角函数", "正弦函数",
            "余弦函数", "正切函数", "分段函数", "函数"
        },
        "方程域": {
            "方程", "方程组", "一元一次方程", "一元二次方程",
            "二元一次方程组", "式与方程"
        },
        "几何域": {
            "几何", "平面几何", "三角形", "四边形", "圆",
            "相似", "全等", "解析几何", "直线", "圆锥曲线",
            "参数方程", "立体几何", "点线面", "柱锥台球", "空间向量"
        },
        "代数域": {
            "代数", "自然数", "整数", "有理数", "实数",
            "复数", "式与方程", "整式", "分式", "根式",
            "不等式", "一元一次不等式", "一元二次不等式", "基本不等式",
            "数列", "等差数列", "等比数列", "递推数列"
        },
        "概率统计域": {
            "统计与概率", "统计", "数据收集", "数据整理", "数据分析",
            "统计推断", "概率", "随机事件", "概率模型", "概率分布"
        },
        "微积分域": {
            "微积分", "极限", "导数", "积分", "微分方程"
        }
    }
    
    # ==================== 第四层：相关关键词扩展 ====================
    
    TOPIC_KEYWORDS: Dict[str, List[str]] = {
        "指数函数": ["指数", "幂函数", "底数", "e^x", "2^x", "a^x", "指数增长", "指数衰减"],
        "对数函数": ["对数", "log", "ln", "底数", "对数运算", "自然对数"],
        "二次函数": ["二次", "抛物线", "顶点", "对称轴", "ax²+bx+c", "判别式"],
        "三角函数": ["三角", "正弦", "余弦", "正切", "sin", "cos", "tan", "角度", "弧度"],
        "函数": ["函数", "图像", "定义域", "值域", "单调性", "奇偶性"],
        "导数": ["导数", "微分", "切线", "斜率", "变化率", "极值", "最值"],
        "积分": ["积分", "定积分", "不定积分", "原函数", "面积", "体积"],
        "方程": ["方程", "解方程", "根", "解", "等式"],
        "不等式": ["不等式", "解不等式", "解集", "不等号"],
        "数列": ["数列", "等差", "等比", "通项", "求和", "递推"],
        "几何": ["几何", "图形", "形状", "位置", "距离", "角度"],
        "统计": ["统计", "数据", "图表", "平均数", "中位数", "众数"],
        "概率": ["概率", "可能性", "随机", "事件", "频率"],
    }
    
    @classmethod
    def extract_topics(cls, query: str) -> List[Tuple[str, float]]:
        """
        从查询中提取数学主题及其权重
        
        Args:
            query: 用户查询
            
        Returns:
            主题列表，每个元素为(主题名称, 权重)的元组
        """
        topics = []
        
        for topic in cls.TOPIC_HIERARCHY.keys():
            if topic in query:
                weight = 1.0
                parents = cls.get_parent_topics(topic)
                for parent in parents:
                    if parent in query:
                        weight *= 0.9
                topics.append((topic, weight))
        
        topics.sort(key=lambda x: x[1], reverse=True)
        return topics
    
    @classmethod
    def get_parent_topics(cls, topic: str) -> List[str]:
        """
        获取父主题列表
        
        Args:
            topic: 主题名称
            
        Returns:
            父主题列表（从直接父到根）
        """
        return cls.TOPIC_HIERARCHY.get(topic, [])
    
    @classmethod
    def get_child_topics(cls, parent_topic: str) -> List[str]:
        """
        获取子主题列表
        
        Args:
            parent_topic: 父主题名称
            
        Returns:
            子主题列表
        """
        children = []
        for topic, parents in cls.TOPIC_HIERARCHY.items():
            if parent_topic in parents:
                children.append(topic)
        return children
    
    @classmethod
    def get_sibling_topics(cls, topic: str) -> List[str]:
        """
        获取兄弟主题列表
        
        Args:
            topic: 主题名称
            
        Returns:
            兄弟主题列表
        """
        return cls.SIBLING_TOPICS.get(topic, [])
    
    @classmethod
    def get_topic_attributes(cls, topic: str) -> List[str]:
        """
        获取主题的属性列表
        
        Args:
            topic: 主题名称
            
        Returns:
            属性列表
        """
        return cls.TOPIC_ATTRIBUTES.get(topic, [])
    
    @classmethod
    def get_concept_domain(cls, topic: str) -> str:
        """
        获取主题所属的概念域
        
        Args:
            topic: 主题名称
            
        Returns:
            概念域名称，如果找不到则返回None
        """
        for domain, topics in cls.CONCEPT_DOMAINS.items():
            if topic in topics:
                return domain
        return None
    
    @classmethod
    def get_domain_topics(cls, domain: str) -> Set[str]:
        """
        获取概念域内的所有主题
        
        Args:
            domain: 概念域名称
            
        Returns:
            主题集合
        """
        return cls.CONCEPT_DOMAINS.get(domain, set())
    
    @classmethod
    def calculate_concept_match_score(cls, resource_topic: str, query_topic: str) -> float:
        """
        计算概念匹配度分数
        
        完全匹配：1.0
        父子匹配：0.9
        兄弟匹配：0.4
        无关匹配：0.0
        
        Args:
            resource_topic: 资源主题
            query_topic: 查询主题
            
        Returns:
            匹配分数 (0.0-1.0)
        """
        if resource_topic == query_topic:
            return 1.0
        
        if query_topic in cls.get_parent_topics(resource_topic):
            return 0.9
        
        if resource_topic in cls.get_parent_topics(query_topic):
            return 0.9
        
        if resource_topic in cls.get_sibling_topics(query_topic):
            return 0.4
        
        return 0.0
    
    @classmethod
    def get_related_keywords(cls, topic: str) -> List[str]:
        """
        获取主题的相关关键词
        
        Args:
            topic: 主题名称
            
        Returns:
            相关关键词列表
        """
        return cls.TOPIC_KEYWORDS.get(topic, [])


# 全局实例
MATH_TOPIC_HIERARCHY = MathTopicHierarchy()
