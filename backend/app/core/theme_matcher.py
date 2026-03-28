"""
主题匹配系统

职责：
- 建立主题-关键词映射库
- 多维度主题匹配
- 分级加分机制
- 冲突主题降权
- 匹配结果可视化
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re


class ThemeMatcher:
    """主题匹配器"""
    
    # 主题-关键词映射库（通用版）
    # 结构: {
    #     "主题名": {
    #         "core_keywords": ["核心关键词（一级证据）"],
    #         "related_keywords": ["相关关键词（三级证据）"],
    #         "chapter_indicators": ["章节标识（二级证据）"],
    #         "conflict_themes": ["冲突主题"],
    #         "path_keywords": ["路径关键词（二级证据）"]
    #     }
    # }
    THEME_KEYWORD_MAP = {
        "函数的单调性": {
            "core_keywords": ["函数的单调性", "单调性", "单调递增", "单调递减", "增函数", "减函数"],
            "related_keywords": ["单调区间", "最值", "最大值", "最小值", "极值", "单调性与最值"],
            "chapter_indicators": ["3.2.1", "3-2-1"],
            "conflict_themes": ["函数的奇偶性", "函数的周期性", "函数的概念", "函数的表示法", "函数的应用"],
            "path_keywords": ["单调性", "单调"]
        },
        "函数的奇偶性": {
            "core_keywords": ["函数的奇偶性", "奇偶性", "奇函数", "偶函数"],
            "related_keywords": ["对称性", "关于原点对称", "关于y轴对称", "f(-x)"],
            "chapter_indicators": ["3.2.2", "3-2-2"],
            "conflict_themes": ["函数的单调性", "函数的周期性", "函数的概念", "函数的表示法"],
            "path_keywords": ["奇偶性", "奇偶"]
        },
        "函数的周期性": {
            "core_keywords": ["函数的周期性", "周期性", "周期函数", "最小正周期"],
            "related_keywords": ["周期", "T", "f(x+T)", "正弦周期", "余弦周期"],
            "chapter_indicators": ["5.4"],
            "conflict_themes": ["函数的单调性", "函数的奇偶性", "函数的概念"],
            "path_keywords": ["周期性", "周期"]
        },
        "函数的概念": {
            "core_keywords": ["函数的概念", "函数概念", "函数定义"],
            "related_keywords": ["什么是函数", "函数意义", "函数本质"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["函数的应用", "函数的性质", "函数的表示法", "函数的单调性", "函数的奇偶性"],
            "path_keywords": ["概念", "定义"]
        },
        "指数函数的概念": {
            "core_keywords": ["指数函数的概念", "指数函数概念"],
            "related_keywords": ["指数函数", "指数"],
            "chapter_indicators": ["4.2.1"],
            "conflict_themes": ["对数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["指数函数"]
        },
        "对数函数的概念": {
            "core_keywords": ["对数函数的概念", "对数函数概念"],
            "related_keywords": ["对数函数", "对数"],
            "chapter_indicators": ["4.4.1"],
            "conflict_themes": ["指数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["对数函数"]
        },
        "函数的应用": {
            "core_keywords": ["函数应用", "函数的应用"],
            "related_keywords": ["应用", "建模", "实际问题", "数学建模"],
            "chapter_indicators": ["4.5"],
            "conflict_themes": ["函数的概念", "函数的性质", "函数的表示法", "函数的单调性", "函数的奇偶性"],
            "path_keywords": ["应用"]
        },
        "函数的性质": {
            "core_keywords": ["函数的性质", "函数性质"],
            "related_keywords": ["单调性", "奇偶性", "周期性", "对称性"],
            "chapter_indicators": ["3.2", "3.3"],
            "conflict_themes": ["函数的概念", "函数的应用", "函数的表示法"],
            "path_keywords": ["性质"]
        },
        "函数的表示法": {
            "core_keywords": ["函数的表示法", "函数表示法"],
            "related_keywords": ["解析法", "图像法", "列表法", "映射"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["函数的概念", "函数的应用", "函数的性质"],
            "path_keywords": ["表示法"]
        },
        "指数函数": {
            "core_keywords": ["指数函数", "指数与指数函数"],
            "related_keywords": ["2^x", "a^x", "e^", "指数增长", "指数衰减"],
            "chapter_indicators": ["4.2", "4.1"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["指数函数"]
        },
        "指数运算": {
            "core_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂"],
            "related_keywords": ["8^", "2^(", "a^(2/3)", "分数指数", "有理指数幂", "n次根式"],
            "chapter_indicators": ["4.1", "4-1"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数"],
            "path_keywords": ["指数", "4-1"],
            "description": "指数运算是计算 a^b 形式的值，底数是常数，指数可以是分数"
        },
        "对数函数": {
            "core_keywords": ["对数函数", "对数与对数函数"],
            "related_keywords": ["log", "ln", "对数增长", "对数衰减", "对数运算", "对数方程", "换底公式", "对数性质"],
            "chapter_indicators": ["4.3", "4.4"],
            "conflict_themes": ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["对数"]
        },
        "对数函数运算": {
            "core_keywords": ["对数函数运算", "对数运算", "换底公式"],
            "related_keywords": ["log", "ln", "对数性质", "对数方程"],
            "chapter_indicators": ["4.3.2", "4-3-2"],
            "conflict_themes": ["指数函数", "幂函数", "三角函数", "二次函数"],
            "path_keywords": ["对数运算", "换底公式"]
        },
        "指数与对数函数综合": {
            "core_keywords": ["指数与对数函数综合", "指数对数综合", "综合应用"],
            "related_keywords": ["指数函数", "对数函数", "综合题", "实际应用", "函数模型"],
            "chapter_indicators": ["4.4", "4.5"],
            "conflict_themes": ["三角函数", "二次函数", "幂函数"],
            "path_keywords": ["综合", "应用"]
        },
        "幂函数": {
            "core_keywords": ["幂函数", "y=x^a", "y = x^a", "幂函数的图像", "幂函数的性质"],
            "related_keywords": ["x^a", "x的幂", "幂运算", "幂函数图像"],
            "chapter_indicators": ["3.3", "3-3"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "二次函数", "一次函数", "分段函数", "指数运算"],
            "path_keywords": ["幂函数", "3-3幂函数", "3.3幂函数"],
            "exclude_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂", "8^", "2^(", "a^x", "a^(2/3)", "分数指数"]
        },
        "二次函数": {
            "core_keywords": ["二次函数"],
            "related_keywords": ["二次", "x²", "x^2", "一元二次", "抛物线", "顶点式", "一般式"],
            "chapter_indicators": ["3.1", "3.2", "3.3"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "一次函数", "分段函数"],
            "path_keywords": ["二次"]
        },
        "一次函数": {
            "core_keywords": ["一次函数", "线性函数"],
            "related_keywords": ["一次", "y=kx+b", "斜率", "截距", "直线"],
            "chapter_indicators": ["3.1"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "分段函数"],
            "path_keywords": ["一次"]
        },
        "三角函数": {
            "core_keywords": ["三角函数", "正弦", "余弦", "正切"],
            "related_keywords": ["三角", "sin", "cos", "tan", "cot", "sec", "csc", "任意角", "诱导公式"],
            "chapter_indicators": ["5.1", "5.2", "5.3", "5.4", "5.6"],
            "conflict_themes": ["指数函数", "对数函数", "二次函数", "幂函数", "一次函数", "分段函数"],
            "path_keywords": ["三角"]
        },
        "三角恒等变换": {
            "core_keywords": ["三角恒等变换", "三角恒等式", "恒等变换", "和差化积", "积化和差", "二倍角", "半角公式"],
            "related_keywords": ["sin", "cos", "tan", "诱导公式", "两角和与差", "三角公式"],
            "chapter_indicators": ["5.5", "5-5"],
            "conflict_themes": ["指数函数", "对数函数", "二次函数", "幂函数", "一次函数"],
            "path_keywords": ["三角恒等变换", "5-5", "恒等变换"]
        },
        "分段函数": {
            "core_keywords": ["分段函数"],
            "related_keywords": ["分段", "绝对值函数", "取整函数", "符号函数"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["分段"]
        },
        "导数": {
            "core_keywords": ["导数", "导函数", "微分", "求导"],
            "related_keywords": ["f'", "y'", "dy/dx", "导数的几何意义", "切线方程", "瞬时变化率"],
            "chapter_indicators": ["6.1", "6.2", "6-1", "6-2"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["导数", "微分", "求导"]
        },
        "导数的应用": {
            "core_keywords": ["导数的应用", "导数应用"],
            "related_keywords": ["单调性", "极值", "最值", "优化问题", "切线", "曲率"],
            "chapter_indicators": ["6.3", "6.4", "6-3", "6-4"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["导数应用", "应用"]
        }
    }
    
    # 加分配置（提高主题匹配的权重）
    BOOST_CONFIG = {
        "filename_core_keyword_match": 0.80,  # 文件名包含核心关键词（最高优先级）
        "title_core_keyword_match": 0.75,  # 标题包含核心关键词
        "core_keyword_match": 0.70,  # 其他地方核心关键词匹配
        "chapter_indicator_match": 0.65,  # 章节标识匹配
        "path_keyword_match": 0.60,  # 路径关键词匹配
        "related_keyword_match": 0.55,  # 相关关键词匹配
        "weak_match": 0.50  # 弱匹配
    }
    
    # 减分配置
    PENALTY_CONFIG = {
        "conflict_theme": 0.35  # 冲突主题
    }
    
    def __init__(self):
        """初始化主题匹配器"""
        pass
    
    def match_theme(
        self,
        core_theme: str,
        metadata: Dict[str, Any],
        document: str,
        verbose: bool = True,
        all_themes: List[str] = None
    ) -> Dict[str, Any]:
        """
        多维度主题匹配（带详细日志）
        
        Args:
            core_theme: 核心主题
            metadata: 资源元数据
            document: 文档内容
            verbose: 是否输出详细日志
            all_themes: 查询中包含的所有主题列表（用于排除多主题查询中的主题冲突）
        
        Returns:
            匹配结果字典
        """
        result = {
            "is_theme_match": False,
            "is_conflict_theme": False,
            "relevance_boost": 0.0,
            "relevance_penalty": 0.0,
            "match_evidence": [],
            "conflict_evidence": [],
            "match_log": []
        }
        
        if not core_theme or core_theme not in self.THEME_KEYWORD_MAP:
            if verbose:
                print(f"   ℹ️  无核心主题或主题不在词库中，跳过匹配")
            return result
        
        theme_config = self.THEME_KEYWORD_MAP[core_theme]
        if verbose:
            print(f"\n   📋 开始主题匹配 - 核心主题: {core_theme}")
        
        # 获取资源的关键信息
        title = metadata.get('title', '')
        source_file = metadata.get('source_file', '')
        tags = metadata.get('知识点标签', '')
        stem = metadata.get('题干', '')
        chapter = metadata.get('章节', '')
        file_topic = metadata.get('文件名主题', '')  # 教案文件名中提取的主题
        
        if verbose:
            print(f"   📄 资源信息: 标题={title}, 源文件={Path(source_file).name if source_file else 'N/A'}, 章节={chapter}, 文件名主题={file_topic}")
        
        # 检查多维度匹配（优先级从高到低）
        match_evidence = []
        match_log = []
        
        # 1. 检查文件名（从路径提取）是否包含核心关键词（最高优先级）
        filename = Path(source_file).name if source_file else ""
        if filename and self._check_keywords_in_text(filename, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
            match_evidence.append(("文件名", filename))
            match_log.append(f"✓ 文件名匹配: {filename} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        elif verbose and filename:
            match_log.append(f"✗ 文件名不匹配: {filename}")
        
        # 2. 检查文件名主题（从教案文件名中提取的主题关键词，高优先级）
        if not result["is_theme_match"] and file_topic and self._check_keywords_in_text(file_topic, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
            match_evidence.append(("文件名主题", file_topic))
            match_log.append(f"✓ 文件名主题匹配: {file_topic} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        elif verbose and file_topic and not result["is_theme_match"]:
            match_log.append(f"✗ 文件名主题不匹配: {file_topic}")
        
        # 3. 检查标题是否包含核心关键词
        if not result["is_theme_match"] and title and self._check_keywords_in_text(title, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["title_core_keyword_match"]
            match_evidence.append(("文件标题", title))
            match_log.append(f"✓ 标题匹配: {title} (+{self.BOOST_CONFIG['title_core_keyword_match']:.0%})")
        elif verbose and title and not result["is_theme_match"]:
            match_log.append(f"✗ 标题不匹配: {title}")
        
        # 4. 检查知识点标签（强匹配）
        if not result["is_theme_match"] and tags and self._check_keywords_in_text(tags, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["core_keyword_match"]
            match_evidence.append(("知识点标签", tags))
            match_log.append(f"✓ 知识点标签匹配: {tags} (+{self.BOOST_CONFIG['core_keyword_match']:.0%})")
        elif verbose and tags and not result["is_theme_match"]:
            match_log.append(f"✗ 知识点标签不匹配: {tags}")
        
        # 5. 检查题干（中匹配）
        if not result["is_theme_match"] and stem and self._check_keywords_in_text(stem, theme_config["core_keywords"] + theme_config["related_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["related_keyword_match"]
            match_evidence.append(("题干", stem))
            match_log.append(f"✓ 题干匹配 (+{self.BOOST_CONFIG['related_keyword_match']:.0%})")
        
        # 6. 检查文件名是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and filename:
            power_function_keywords = ["幂函数", "3-3", "3.3"]
            if any(keyword in filename for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("文件名", filename))
                match_log.append(f"✓ 幂函数文件名匹配: {filename} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 7. 检查源文件路径是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and source_file:
            power_function_keywords = ["幂函数", "3-3", "3.3"]
            if any(keyword in source_file for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("源文件路径", source_file))
                match_log.append(f"✓ 幂函数源文件路径匹配: {source_file} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 8. 检查知识点标签是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and tags:
            power_function_keywords = ["幂函数"]
            if any(keyword in tags for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("知识点标签", tags))
                match_log.append(f"✓ 幂函数知识点标签匹配: {tags} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 9. 检查章节标识（强匹配）
        if not result["is_theme_match"] and self._check_keywords_in_text(chapter, theme_config["chapter_indicators"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["chapter_indicator_match"]
            match_evidence.append(("章节字段", chapter))
            match_log.append(f"✓ 章节标识匹配: {chapter} (+{self.BOOST_CONFIG['chapter_indicator_match']:.0%})")
        elif verbose and chapter and not result["is_theme_match"]:
            match_log.append(f"✗ 章节标识不匹配: {chapter}")
        
        # 10. 检查路径关键词 + 章节标识（中匹配）
        if not result["is_theme_match"]:
            path_has_keyword = self._check_keywords_in_text(source_file, theme_config["path_keywords"])
            path_has_chapter = self._check_keywords_in_text(source_file, theme_config["chapter_indicators"])
            metadata_has_chapter = self._check_keywords_in_text(chapter, theme_config["chapter_indicators"])
            
            if path_has_keyword and (path_has_chapter or metadata_has_chapter):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["path_keyword_match"]
                match_evidence.append(("文件路径+章节", source_file))
                match_log.append(f"✓ 路径+章节匹配: {Path(source_file).name} (+{self.BOOST_CONFIG['path_keyword_match']:.0%})")
            elif verbose:
                match_log.append(f"✗ 路径+章节不匹配 (路径关键词={path_has_keyword}, 章节标识={path_has_chapter or metadata_has_chapter})")
        
        # 7. 检查标题相关关键词（中匹配）
        if not result["is_theme_match"] and self._check_keywords_in_text(title, theme_config["related_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["related_keyword_match"]
            match_evidence.append(("文件标题（相关词）", title))
            match_log.append(f"✓ 标题相关词匹配: {title} (+{self.BOOST_CONFIG['related_keyword_match']:.0%})")
        
        # 8. 检查内容（弱匹配）
        if not result["is_theme_match"] and self._check_keywords_in_text(document, theme_config["core_keywords"] + theme_config["related_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["weak_match"]
            match_evidence.append(("文档内容", "内容中包含相关关键词"))
            match_log.append(f"✓ 内容弱匹配 (+{self.BOOST_CONFIG['weak_match']:.0%})")
        
        result["match_evidence"] = match_evidence
        result["match_log"] = match_log
        
        # 检查冲突主题（始终执行）
        conflict_evidence = []
        
        # 获取实际需要检测的冲突主题（排除查询中包含的其他主题）
        actual_conflict_themes = theme_config["conflict_themes"]
        if all_themes:
            actual_conflict_themes = [ct for ct in theme_config["conflict_themes"] if ct not in all_themes]
        
        # 特别检查：如果文件名或标题明确包含冲突主题词，应该优先判定为冲突
        strong_conflict = False
        filename = Path(source_file).name if source_file else ""
        check_strong_conflict_texts = [filename, title, chapter]
        
        for text in check_strong_conflict_texts:
            if text:
                for ct in actual_conflict_themes:
                    # 避免将章节名称中的"函数的概念"误判为冲突
                    # 例如："第三章函数的概念与性质"中的"函数的概念"只是章节名称的一部分
                    if ct in text:
                        # 检查是否是"函数的概念"冲突，且文本是章节名称或路径
                        if ct == "函数的概念":
                            # 检查是否是在章节路径中，而不是实际主题
                            if "章" in text or "第" in text or "函数的概念与性质" in text:
                                continue  # 跳过章节名称中的"函数的概念"
                        
                        strong_conflict = True
                        result["is_conflict_theme"] = True
                        result["relevance_penalty"] = self.PENALTY_CONFIG["conflict_theme"]
                        conflict_evidence.append((ct, text))
                        match_log.append(f"⚠️ 强冲突检测: {ct} 在 '{text}' 中 (-{self.PENALTY_CONFIG['conflict_theme']:.0%})")
                        break
            if strong_conflict:
                break
        
        # 增强冲突检测：检查文件路径中的章节信息
        if not strong_conflict and source_file:
            # 检查是否在三角函数章节
            trigonometry_paths = ["第五章三角函数", "5.4", "5.5", "5.6"]
            for trig_path in trigonometry_paths:
                if trig_path in source_file:
                    # 检查当前主题是否与三角函数相关
                    current_theme_is_trig = any(trig_keyword in core_theme for trig_keyword in ["三角函数", "正弦", "余弦", "正切", "三角恒等变换", "诱导公式"])
                    if not current_theme_is_trig:
                        # 只有当当前主题与三角函数完全无关时才标记为冲突
                        # 避免将函数性质主题错误标记为冲突
                        function_property_themes = ["函数的单调性", "函数的奇偶性", "函数的周期性", "函数的概念", "函数的性质"]
                        if core_theme not in function_property_themes:
                            strong_conflict = True
                            result["is_conflict_theme"] = True
                            result["relevance_penalty"] = self.PENALTY_CONFIG["conflict_theme"]
                            conflict_evidence.append(("三角函数", source_file))
                            match_log.append(f"⚠️ 路径冲突检测: 三角函数章节 (-{self.PENALTY_CONFIG['conflict_theme']:.0%})")
                            break
        
        # 如果有强冲突，取消主题匹配（即使内容匹配了）
        if strong_conflict:
            result["is_theme_match"] = False
            result["relevance_boost"] = 0.0
            match_evidence = []
            match_log.append("   ↪️ 强冲突生效，取消主题匹配加分")
        
        # 如果没有强冲突，且没有通过强匹配方式匹配主题，再检查其他文本
        if not strong_conflict:
            is_strong_match = False
            if match_evidence:
                first_evidence_type = match_evidence[0][0]
                if first_evidence_type in ["文件名", "文件标题", "知识点标签"]:
                    is_strong_match = True
            
            if not is_strong_match:
                check_texts = [tags, chapter, stem, document, source_file]
                for text in check_texts:
                    if text:
                        for ct in actual_conflict_themes:
                            if ct in text:
                                result["is_conflict_theme"] = True
                                result["relevance_penalty"] = self.PENALTY_CONFIG["conflict_theme"]
                                conflict_evidence.append((ct, text[:100]))
                                match_log.append(f"⚠️ 弱冲突检测: {ct} (-{self.PENALTY_CONFIG['conflict_theme']:.0%})")
                                break
                    if result["is_conflict_theme"]:
                        break
        
        result["conflict_evidence"] = conflict_evidence
        
        # 输出详细的匹配日志
        if verbose:
            for log in match_log:
                print(f"   {log}")
            print(f"   📊 匹配总结: 主题匹配={result['is_theme_match']}, 冲突主题={result['is_conflict_theme']}, 加分={result['relevance_boost']:.0%}, 减分={result['relevance_penalty']:.0%}")
        
        return result
    
    def _check_keywords_in_text(self, text: str, keywords: List[str]) -> bool:
        """
        检查文本中是否包含任意关键词
        
        Args:
            text: 待检查文本
            keywords: 关键词列表
        
        Returns:
            是否匹配
        """
        if not text:
            return False
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def _print_match_info(self, core_theme: str, title: str, result: Dict[str, Any]) -> None:
        """
        打印匹配信息（可视化）
        
        Args:
            core_theme: 核心主题
            title: 资源标题
            result: 匹配结果
        """
        if result["is_theme_match"]:
            evidence_type, evidence_text = result["match_evidence"][0] if result["match_evidence"] else ("未知", "")
            print(f"   🎯 主题匹配+分: +{result['relevance_boost']:.0%}, "
                  f"依据: {evidence_type}")
        if result["is_conflict_theme"]:
            conflict_theme, conflict_text = result["conflict_evidence"][0] if result["conflict_evidence"] else ("未知", "")
            print(f"   ⚠️  冲突主题-分: -{result['relevance_penalty']:.0%}, "
                  f"冲突: {conflict_theme}")
    
    def get_all_themes(self) -> List[str]:
        """
        获取所有支持的主题列表
        
        Returns:
            主题列表
        """
        return list(self.THEME_KEYWORD_MAP.keys())
    
    def add_theme_keywords(self, theme: str, keywords: List[str], keyword_type: str = "related") -> bool:
        """
        动态添加主题关键词
        
        Args:
            theme: 主题名
            keywords: 关键词列表
            keyword_type: 关键词类型 (core/related/chapter/path)
        
        Returns:
            是否成功
        """
        if theme not in self.THEME_KEYWORD_MAP:
            return False
        
        type_map = {
            "core": "core_keywords",
            "related": "related_keywords",
            "chapter": "chapter_indicators",
            "path": "path_keywords"
        }
        
        key = type_map.get(keyword_type)
        if not key:
            return False
        
        for kw in keywords:
            if kw not in self.THEME_KEYWORD_MAP[theme][key]:
                self.THEME_KEYWORD_MAP[theme][key].append(kw)
        
        return True
    
    def dynamic_theme_detection(self, content: str, title: str = "") -> List[Dict[str, Any]]:
        """
        动态主题检测
        
        Args:
            content: 资源内容
            title: 资源标题
        
        Returns:
            检测到的主题列表
        """
        detected_themes = []
        
        # 1. 基于主题关键词映射的检测
        for theme, config in self.THEME_KEYWORD_MAP.items():
            # 检查核心关键词
            if self._check_keywords_in_text(content, config["core_keywords"]) or \
               self._check_keywords_in_text(title, config["core_keywords"]):
                detected_themes.append({
                    "theme": theme,
                    "confidence": 0.9,
                    "evidence": "core_keyword",
                    "matched_keywords": [kw for kw in config["core_keywords"] 
                                        if kw in content or kw in title]
                })
            # 检查相关关键词
            elif self._check_keywords_in_text(content, config["related_keywords"]) or \
                 self._check_keywords_in_text(title, config["related_keywords"]):
                detected_themes.append({
                    "theme": theme,
                    "confidence": 0.7,
                    "evidence": "related_keyword",
                    "matched_keywords": [kw for kw in config["related_keywords"] 
                                        if kw in content or kw in title]
                })
        
        # 2. 基于数学公式的动态检测
        formula_themes = self._detect_formula_themes(content)
        detected_themes.extend(formula_themes)
        
        # 3. 基于上下文的动态检测
        context_themes = self._detect_context_themes(content, title)
        detected_themes.extend(context_themes)
        
        # 4. 去重并按置信度排序
        unique_themes = {}
        for theme_info in detected_themes:
            theme = theme_info["theme"]
            if theme not in unique_themes or theme_info["confidence"] > unique_themes[theme]["confidence"]:
                unique_themes[theme] = theme_info
        
        return sorted(unique_themes.values(), key=lambda x: -x["confidence"])
    
    def _detect_formula_themes(self, content: str) -> List[Dict[str, Any]]:
        """
        基于公式的主题检测
        """
        formula_themes = []
        
        # 幂函数: y = x^a
        if re.search(r'y\s*=\s*x\s*\^\s*[a-zA-Z]', content):
            formula_themes.append({
                "theme": "幂函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = x^a"]
            })
        
        # 指数函数: y = a^x
        if re.search(r'y\s*=\s*[a-zA-Z]\s*\^\s*x', content):
            formula_themes.append({
                "theme": "指数函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = a^x"]
            })
        
        # 二次函数: y = ax² + bx + c
        if re.search(r'y\s*=\s*[a-zA-Z]\s*[xX]\s*[\^2²]', content):
            formula_themes.append({
                "theme": "二次函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = ax²"]
            })
        
        # 三角函数
        if re.search(r'[sS][iI][nN]|cos|tan|sin|cos|tan', content):
            formula_themes.append({
                "theme": "三角函数",
                "confidence": 0.75,
                "evidence": "formula",
                "matched_keywords": ["sin", "cos", "tan"]
            })
        
        return formula_themes
    
    def _detect_context_themes(self, content: str, title: str) -> List[Dict[str, Any]]:
        """
        基于上下文的主题检测
        """
        context_themes = []
        
        # 基于教学目标
        if any(keyword in content for keyword in ["教学目标", "学习目标", "教学重难点"]):
            # 分析教学目标中的主题
            lines = content.split('\n')
            for line in lines:
                if "目标" in line or "重点" in line:
                    for theme in self.THEME_KEYWORD_MAP:
                        if theme in line:
                            context_themes.append({
                                "theme": theme,
                                "confidence": 0.7,
                                "evidence": "teaching_goal",
                                "matched_keywords": [theme]
                            })
        
        # 基于章节信息
        chapter_patterns = [r'第[一二三四五六七八九十]+章', r'第[0-9]+章', r'模块[0-9]+']
        for pattern in chapter_patterns:
            match = re.search(pattern, content + title)
            if match:
                chapter = match.group()
                # 映射章节到主题
                chapter_theme_map = {
                    "第三章": ["函数的概念", "函数的性质", "二次函数", "幂函数"],
                    "第四章": ["指数函数", "对数函数"],
                    "第五章": ["三角函数"],
                    "第六章": ["三角恒等变换"]
                }
                for chapter_key, themes in chapter_theme_map.items():
                    if chapter_key in chapter:
                        for theme in themes:
                            context_themes.append({
                                "theme": theme,
                                "confidence": 0.6,
                                "evidence": "chapter",
                                "matched_keywords": [chapter]
                            })
        
        return context_themes
    
    def update_theme_weights(self, theme_feedback: Dict[str, float]) -> None:
        """
        根据用户反馈更新主题权重
        
        Args:
            theme_feedback: 主题反馈字典 {theme: score}
        """
        # 这里可以实现权重更新逻辑
        # 例如：调整关键词权重、添加新关键词等
        print(f"📊 更新主题权重: {theme_feedback}")
    
    def process_feedback(self, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户反馈
        
        Args:
            user_feedback: 用户反馈，包含feedback_type和相关数据
        
        Returns:
            处理结果
        """
        feedback_type = user_feedback.get('feedback_type')
        
        if feedback_type == 'theme_correction':
            # 主题修正反馈
            correct_theme = user_feedback.get('correct_theme')
            wrong_theme = user_feedback.get('wrong_theme')
            content = user_feedback.get('content', '')
            
            if correct_theme and wrong_theme:
                # 调整主题权重
                self.update_theme_weights({correct_theme: 0.1, wrong_theme: -0.1})
                print(f"   🔄 主题反馈处理: 修正 {wrong_theme} -> {correct_theme}")
                
                # 重新检测主题
                new_themes = self.dynamic_theme_detection(content)
                return {
                    'status': 'success',
                    'message': '主题权重已更新',
                    'new_themes': new_themes
                }
        
        elif feedback_type == 'relevance_feedback':
            # 相关性反馈
            resource_id = user_feedback.get('resource_id')
            relevance_score = user_feedback.get('relevance_score')
            
            if resource_id and relevance_score is not None:
                # 这里可以实现更复杂的相关性反馈处理
                print(f"   🔄 相关性反馈: {resource_id} -> {relevance_score}")
                return {
                    'status': 'success',
                    'message': '相关性反馈已记录'
                }
        
        return {
            'status': 'error',
            'message': '无效的反馈类型'
        }


# 全局主题匹配器实例
_theme_matcher = None


def get_theme_matcher() -> ThemeMatcher:
    """
    获取主题匹配器实例（单例模式）
    
    Returns:
        主题匹配器
    """
    global _theme_matcher
    if _theme_matcher is None:
        _theme_matcher = ThemeMatcher()
    return _theme_matcher
