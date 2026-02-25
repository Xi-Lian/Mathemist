"""
主题匹配系统

职责：
- 建立主题-关键词映射库
- 多维度主题匹配
- 分级加分机制
- 冲突主题降权
- 匹配结果可视化
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path


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
        "函数的概念": {
            "core_keywords": ["函数的概念", "函数概念", "函数定义"],
            "related_keywords": ["什么是函数", "函数意义", "函数本质"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["函数的应用", "函数的性质", "函数的表示法"],
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
            "conflict_themes": ["函数的概念", "函数的性质", "函数的表示法"],
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
            "core_keywords": ["指数函数", "指数与指数函数", "指数"],
            "related_keywords": ["2^x", "a^x", "e^", "指数增长", "指数衰减"],
            "chapter_indicators": ["4.2"],
            "conflict_themes": ["对数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["指数"]
        },
        "对数函数": {
            "core_keywords": ["对数函数", "对数与对数函数", "对数"],
            "related_keywords": ["log", "ln", "对数增长", "对数衰减"],
            "chapter_indicators": ["4.3", "4.4"],
            "conflict_themes": ["指数函数", "幂函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["对数"]
        },
        "幂函数": {
            "core_keywords": ["幂函数", "幂"],
            "related_keywords": ["x^a", "x的幂", "幂运算"],
            "chapter_indicators": ["3.3"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "二次函数", "一次函数", "分段函数"],
            "path_keywords": ["幂"]
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
            "related_keywords": ["三角", "sin", "cos", "tan", "cot", "sec", "csc", "任意角", "诱导公式", "三角恒等变换"],
            "chapter_indicators": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"],
            "conflict_themes": ["指数函数", "对数函数", "二次函数", "幂函数", "一次函数", "分段函数"],
            "path_keywords": ["三角"]
        },
        "分段函数": {
            "core_keywords": ["分段函数"],
            "related_keywords": ["分段", "绝对值函数", "取整函数", "符号函数"],
            "chapter_indicators": ["3.1", "3.2"],
            "conflict_themes": ["指数函数", "对数函数", "三角函数", "幂函数", "二次函数", "一次函数"],
            "path_keywords": ["分段"]
        }
    }
    
    # 加分配置
    BOOST_CONFIG = {
        "filename_core_keyword_match": 0.40,  # 文件名包含核心关键词（最高优先级）
        "title_core_keyword_match": 0.38,  # 标题包含核心关键词
        "core_keyword_match": 0.35,  # 其他地方核心关键词匹配
        "chapter_indicator_match": 0.30,  # 章节标识匹配
        "path_keyword_match": 0.25,  # 路径关键词匹配
        "related_keyword_match": 0.20,  # 相关关键词匹配
        "weak_match": 0.15  # 弱匹配
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
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        多维度主题匹配（带详细日志）
        
        Args:
            core_theme: 核心主题
            metadata: 资源元数据
            document: 文档内容
            verbose: 是否输出详细日志
        
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
        
        if verbose:
            print(f"   📄 资源信息: 标题={title}, 源文件={Path(source_file).name if source_file else 'N/A'}, 章节={chapter}")
        
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
        
        # 2. 检查标题是否包含核心关键词
        if not result["is_theme_match"] and title and self._check_keywords_in_text(title, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["title_core_keyword_match"]
            match_evidence.append(("文件标题", title))
            match_log.append(f"✓ 标题匹配: {title} (+{self.BOOST_CONFIG['title_core_keyword_match']:.0%})")
        elif verbose and title and not result["is_theme_match"]:
            match_log.append(f"✗ 标题不匹配: {title}")
        
        # 3. 检查知识点标签（强匹配）
        if not result["is_theme_match"] and tags and self._check_keywords_in_text(tags, theme_config["core_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["core_keyword_match"]
            match_evidence.append(("知识点标签", tags))
            match_log.append(f"✓ 知识点标签匹配: {tags} (+{self.BOOST_CONFIG['core_keyword_match']:.0%})")
        elif verbose and tags and not result["is_theme_match"]:
            match_log.append(f"✗ 知识点标签不匹配: {tags}")
        
        # 4. 检查题干（中匹配）
        if not result["is_theme_match"] and stem and self._check_keywords_in_text(stem, theme_config["core_keywords"] + theme_config["related_keywords"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["related_keyword_match"]
            match_evidence.append(("题干", stem))
            match_log.append(f"✓ 题干匹配 (+{self.BOOST_CONFIG['related_keyword_match']:.0%})")
        
        # 5. 检查文件名是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and filename:
            power_function_keywords = ["幂函数", "3-3", "3.3"]
            if any(keyword in filename for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("文件名", filename))
                match_log.append(f"✓ 幂函数文件名匹配: {filename} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 6. 检查源文件路径是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and source_file:
            power_function_keywords = ["幂函数", "3-3", "3.3"]
            if any(keyword in source_file for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("源文件路径", source_file))
                match_log.append(f"✓ 幂函数源文件路径匹配: {source_file} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 7. 检查知识点标签是否包含幂函数相关关键词（针对幂函数特殊处理）
        if not result["is_theme_match"] and core_theme == "幂函数" and tags:
            power_function_keywords = ["幂函数"]
            if any(keyword in tags for keyword in power_function_keywords):
                result["is_theme_match"] = True
                result["relevance_boost"] = self.BOOST_CONFIG["filename_core_keyword_match"]
                match_evidence.append(("知识点标签", tags))
                match_log.append(f"✓ 幂函数知识点标签匹配: {tags} (+{self.BOOST_CONFIG['filename_core_keyword_match']:.0%})")
        
        # 6. 检查章节标识（强匹配）
        if not result["is_theme_match"] and self._check_keywords_in_text(chapter, theme_config["chapter_indicators"]):
            result["is_theme_match"] = True
            result["relevance_boost"] = self.BOOST_CONFIG["chapter_indicator_match"]
            match_evidence.append(("章节字段", chapter))
            match_log.append(f"✓ 章节标识匹配: {chapter} (+{self.BOOST_CONFIG['chapter_indicator_match']:.0%})")
        elif verbose and chapter and not result["is_theme_match"]:
            match_log.append(f"✗ 章节标识不匹配: {chapter}")
        
        # 6. 检查路径关键词 + 章节标识（中匹配）
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
        
        # 特别检查：如果文件名或标题明确包含冲突主题词，应该优先判定为冲突
        strong_conflict = False
        filename = Path(source_file).name if source_file else ""
        check_strong_conflict_texts = [filename, title]
        
        for text in check_strong_conflict_texts:
            if text:
                for ct in theme_config["conflict_themes"]:
                    if ct in text:
                        strong_conflict = True
                        result["is_conflict_theme"] = True
                        result["relevance_penalty"] = self.PENALTY_CONFIG["conflict_theme"]
                        conflict_evidence.append((ct, text))
                        match_log.append(f"⚠️ 强冲突检测: {ct} 在 '{text}' 中 (-{self.PENALTY_CONFIG['conflict_theme']:.0%})")
                        break
            if strong_conflict:
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
                        for ct in theme_config["conflict_themes"]:
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
