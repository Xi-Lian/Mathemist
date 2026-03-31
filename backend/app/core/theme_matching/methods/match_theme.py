from .._shared import *


class _MatchThemeMixin:
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
