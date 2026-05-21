import logging
from .._shared import *
from urllib.parse import quote, unquote, urlsplit, urlunsplit

logger = logging.getLogger(__name__)


class _AppendResourceInfoMixin:
    def _encode_http_url(self, source: str) -> str:
        normalized_source = (source or "").replace("\\", "/")
        parsed = urlsplit(normalized_source)
        normalized_path = unquote(parsed.path).replace("\\", "/").replace("%5C", "/").replace("%5c", "/")
        encoded_path = quote(normalized_path, safe="/:%-._~!$&'()*+,;=@")
        encoded_query = quote(parsed.query, safe="=&%-._~!$'()*+,;:@/?")
        encoded_fragment = quote(parsed.fragment, safe="%-._~!$&'()*+,;=:@/?")
        return urlunsplit((parsed.scheme, parsed.netloc, encoded_path, encoded_query, encoded_fragment))

    def _build_source_markdown(self, source: str) -> str:
        source = (source or "").strip()
        if not source:
            return "未提供文件路径"

        if source.startswith(("http://", "https://")):
            return f"[打开文件]({self._encode_http_url(source)})"

        normalized_source = source.replace("\\", "/")
        return f"[{source}](resource://{normalized_source})"

    @staticmethod
    def _pick_display_source(resource: Dict[str, Any]) -> str:
        original_file_url = (resource.get("original_file_url") or "").strip()
        cloud_url = (resource.get("cloud_url") or "").strip()
        source = (resource.get("source") or "").strip()
        return cloud_url or original_file_url or source

    def _append_resource_info(
        self,
        response_parts: List[str],
        resource: Dict[str, Any],
        icon: str,
        category_name: str,
        scenario: str,
        is_comprehensive: bool = False,
        state: Any = None
    ):
        """
        追加资源信息到响应部分（V8.2改进版）

        Args:
            response_parts: 响应部分列表
            resource: 资源字典
            icon: 图标
            category_name: 分类名称
            scenario: 场景类型
            is_comprehensive: 是否为综合性资源
            state: 状态对象，用于获取用户原始查询
        """
        title = resource.get("title", "未知")
        content = resource.get("content", "")
        relevance = resource.get("relevance", 0)
        source = resource.get("source", "")
        display_source = self._pick_display_source(resource)
        matched_themes = resource.get("matched_themes", [])
        matched_theme_count = resource.get("matched_theme_count", 0)
        
        logger.warning(f"📝 [资源格式化] 开始处理资源: title='{title[:30]}', has_content={bool(content)}, has_source={bool(source)}, matched_themes={matched_themes}")
        
        # V9.0：获取精准匹配信息
        core_theme = resource.get("core_theme")
        related_themes = resource.get("related_themes", [])
        mentioned_themes = resource.get("mentioned_themes", [])
        is_core_match = resource.get("is_core_match", False)
        match_level = resource.get("match_level", "none")
        match_explanation = resource.get("match_explanation", "")
        
        # V11.3：获取多维度评估信息（不使用默认值，直接显示实际值）
        overall_score = resource.get("overall_score", resource.get("relevance", 0))
        # V11.3：不使用默认值，如果值为None则显示0
        resource_quality = resource.get("resource_quality")
        if resource_quality is None:
            resource_quality = 0.0
        content_completeness = resource.get("content_completeness")
        if content_completeness is None:
            content_completeness = 0.0
        teaching_value = resource.get("teaching_value")
        if teaching_value is None:
            teaching_value = 0.0
        comprehensiveness = resource.get("comprehensiveness")
        if comprehensiveness is None:
            comprehensiveness = 0.0

        # 处理内容
        processed_content = self._process_resource_content(
            category_name,
            title,
            content,
            scenario,
            resource
        ).strip()

        # 根据资源类型调整标题显示
        display_title = title
        print(f"   🔍 调试 - category_name: '{category_name}', display_title: '{display_title}'")
        if category_name == "教案资源":
            # 教案资源中移除标题中的习题相关字样
            if "涔犻" in display_title:
                display_title = display_title.replace("涔犻:", "").replace("涔犻", "").strip()
                print(f"   🔍 调试 - 移除'涔犻'后: '{display_title}'")
            elif "习题" in display_title:
                display_title = display_title.replace("习题:", "").replace("习题", "").strip()
                print(f"   🔍 调试 - 移除'习题'后: '{display_title}'")
            if not display_title:
                display_title = "教案"
                print(f"   🔍 调试 - 设置为'教案': '{display_title}'")
        print(f"   🔍 调试 - 最终display_title: '{display_title}'")

        # 获取用户原始查询，用于提取所有查询主题
        user_input = ""
        if state:
            user_input = self._get_state_value(state, "user_input", "")
        
        # 提取查询中的所有主题
        query_themes = []
        if user_input:
            # 改进：更全面的主题提取逻辑
            theme_keywords = [
                "二次函数", "指数函数", "对数函数", "幂函数", "三角函数",
                "三角恒等变换", "诱导公式", "函数的单调性", "函数的奇偶性",
                "函数的周期性", "函数的概念", "函数的性质", "函数的应用"
            ]
            for keyword in theme_keywords:
                if keyword in user_input:
                    query_themes.append(keyword)
            
            # 特殊处理：如果用户查询包含"三角恒等变换"，也添加"三角函数"到查询主题
            if "三角恒等变换" in user_input:
                if "三角函数" not in query_themes:
                    query_themes.append("三角函数")
            # 特殊处理：如果用户查询包含具体的三角函数主题，也添加"三角函数"到查询主题
            elif any(trig_theme in user_input for trig_theme in ["诱导公式", "三角恒等"]):
                if "三角函数" not in query_themes:
                    query_themes.append("三角函数")
        
        theme_tags = ""
        short_theme_hint = ""
        if core_theme:
            # 核心主题匹配
            if matched_theme_count > 1:
                # 多主题匹配，只显示与查询相关的主题
                relevant_themes = [theme for theme in matched_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
                if relevant_themes:
                    short_theme_hint = ", ".join(relevant_themes)
                    theme_tags = f" [匹配主题: {short_theme_hint}]"
            else:
                # 单主题匹配，只显示与查询相关的主题
                if not query_themes or core_theme in query_themes or any(qt in core_theme for qt in query_themes):
                    short_theme_hint = core_theme
                    theme_tags = f" [核心主题: {core_theme}]"
        elif related_themes:
            # 相关主题匹配，只显示与查询相关的主题
            relevant_related = [theme for theme in related_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
            if relevant_related:
                short_theme_hint = relevant_related[0]
                theme_tags = f" [相关主题: {relevant_related[0]}]"
        elif mentioned_themes:
            # 提及主题匹配，只显示与查询相关的主题
            relevant_mentioned = [theme for theme in mentioned_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
            if relevant_mentioned:
                short_theme_hint = relevant_mentioned[0]
                theme_tags = f" [提及主题: {relevant_mentioned[0]}]"
        elif matched_theme_count > 1:
            short_theme_hint = ", ".join(matched_themes)
            theme_tags = f" [匹配主题: {short_theme_hint}]"
        elif matched_themes:
            short_theme_hint = matched_themes[0]
            theme_tags = f" [主题: {matched_themes[0]}]"

        # V9.0：核心主题匹配添加特殊标记
        title_prefix = f"{icon} "
        if is_core_match:
            title_prefix += "⭐ "
        elif is_comprehensive:
            title_prefix += "🔥 "
        response_parts.append(f"**{title_prefix}{display_title}**")

        match_label_map = {
            "exact": "高度匹配",
            "direct": "直接相关",
            "related": "较为相关",
            "mentioned": "可作补充",
            "none": "弱相关",
        }
        priority_name = resource.get("priority_name", "")
        match_label = "核心匹配" if is_core_match else match_label_map.get(match_level, priority_name or "相关资源")
        reason_parts = [match_label]
        if short_theme_hint:
            reason_parts.append(f"主题：{short_theme_hint}")
        if match_explanation:
            reason_parts.append(match_explanation)

        response_parts.append(f"- 适配说明：{'；'.join(reason_parts)}")
        
        # V43.1：添加教学用途降级提示
        teaching_use = resource.get('teaching_use', '')
        if state and teaching_use:
            user_input = self._get_state_value(state, "user_input", "")
            if user_input:
                # 检测用户是否明确要求某种教学用途
                user_intent = None
                if '复习' in user_input or '总结' in user_input or '回顾' in user_input:
                    user_intent = '复习课'
                elif '练习' in user_input or '习题' in user_input or '训练' in user_input:
                    user_intent = '练习课'
                elif '新授' in user_input or '新课' in user_input:
                    user_intent = '新授课'
                
                # 如果用户有明确意图，且课件用途不匹配，添加提示
                if user_intent and user_intent not in teaching_use:
                    fallback_message = self._get_fallback_message(user_intent, teaching_use)
                    if fallback_message:
                        response_parts.append(f"- ⚠️ {fallback_message}")
        
        # 教学大纲资源特殊处理：显示完整内容，不做预览
        # 同时检查resource_type和category_name，确保教学大纲资源能被正确识别
        resource_type = resource.get('resource_type', '')
        is_syllabus = (category_name == "教学大纲" or category_name == "syllabus" or 
                      resource_type == 'syllabus' or 'syllabus' in str(resource_type).lower())
        
        if is_syllabus:
            response_parts.append("")  # 添加空行分隔
            response_parts.append("**📚 教学大纲内容：**")
            response_parts.append("")
            
            # 解析并格式化教学大纲内容
            lines = processed_content.splitlines()
            in_code_block = False
            
            for line in lines:
                # 处理标题
                if line.startswith('### '):
                    response_parts.append(f"#### {line[4:]}")
                elif line.startswith('## '):
                    response_parts.append(f"**◆ {line[3:]}**")
                elif line.startswith('# '):
                    response_parts.append(f"**📌 {line[2:]}**")
                # 处理列表
                elif line.startswith('- **') and '** (当前章节)' in line:
                    # 提取章节名称（去掉 "- **" 前缀和 "** (当前章节)" 后缀）
                    chapter_name = line.replace('- **', '').replace('** (当前章节)', '').strip()
                    response_parts.append(f"  ✅ {chapter_name}")
                elif line.startswith('- '):
                    response_parts.append(f"  ○ {line[2:]}")
                # 处理特殊标记
                elif line.startswith('【') and line.endswith('】'):
                    response_parts.append("")
                    response_parts.append(f"**{line}**")
                    response_parts.append("")
                # 处理分隔线
                elif line.strip() == '---':
                    response_parts.append("---")
                # 处理普通文本
                elif line.strip():
                    response_parts.append(f"  {line}")
                # 空行
                else:
                    response_parts.append("")
        else:
            # 其他资源显示内容预览
            if "\n" in processed_content:
                response_parts.append("- 内容预览：")
                for line in processed_content.splitlines():
                    response_parts.append(line if line else "")
            else:
                response_parts.append(f"- 内容预览：{processed_content}")

        if self.show_debug_scores:
            debug_parts = []
            if is_core_match:
                debug_parts.append(f"相关性 {relevance*100:.1f}% (核心匹配)")
            else:
                debug_parts.append(f"相关性 {relevance*100:.1f}%")
            debug_parts.append(f"综合得分 {overall_score*100:.1f}%")
            debug_parts.append(f"资源质量 {resource_quality*100:.1f}%")
            debug_parts.append(f"内容完整性 {content_completeness*100:.1f}%")
            debug_parts.append(f"教学价值 {teaching_value*100:.1f}%")
            debug_parts.append(f"综合性 {comprehensiveness*100:.1f}%")
            response_parts.append(f"- 调试分数：{' | '.join(debug_parts)}")

        # V45.0：课例视频特殊处理：显示视频链接、教材、课程名称、分析
        is_lesson_case = (category_name == "课例资源" or category_name == "lesson_case" or 
                         resource_type == 'lesson_case' or 'lesson_case' in str(resource_type).lower())
        
        # V45.3修复：课例视频不显示Excel文件路径，直接显示视频链接
        if not is_syllabus and not is_lesson_case:
            response_parts.append(f"- 文件路径：{self._build_source_markdown(display_source)}")
        
        if is_lesson_case:
            # 获取课例视频的关键字段
            video_url = resource.get('视频文件名/网址', '') or resource.get('video_url', '') or resource.get('url', '')
            textbook = resource.get('教材', '') or resource.get('textbook', '')
            course_name = resource.get('课程名称', '') or resource.get('course_name', '') or resource.get('title', '')
            analysis = resource.get('分析', '') or resource.get('analysis', '') or resource.get('content', '')
            chapter = resource.get('章节', '') or resource.get('chapter', '')
            
            # 显示视频链接（如果有）
            if video_url:
                # 判断是URL还是文件名
                if video_url.startswith('http'):
                    response_parts.append(f"- 🎬 **视频链接**：[{video_url}]({video_url})")
                else:
                    # 文件名，尝试构建链接
                    response_parts.append(f"- 🎬 **视频文件**：`{video_url}`")
            
            # 显示教材信息
            if textbook:
                response_parts.append(f"- 📚 **教材**：{textbook}")
            
            # 显示课程名称
            if course_name and course_name != title:
                response_parts.append(f"- 📖 **课程名称**：{course_name}")
            
            # 显示章节信息
            if chapter:
                response_parts.append(f"- 📑 **章节**：{chapter}")
            
            # 显示分析内容
            if analysis:
                # 如果分析内容太长，截取前200字符
                analysis_preview = analysis[:200] + "..." if len(analysis) > 200 else analysis
                response_parts.append(f"- 💡 **分析**：{analysis_preview}")

        if category_name == "教案资源":
            cloud_url = (resource.get("cloud_url") or "").strip()
            original_file_url = (resource.get("original_file_url") or "").strip()
            original_filename = (resource.get("original_filename") or "").strip()
            related_file = (resource.get("related_file") or "").strip()

            if cloud_url and cloud_url != display_source:
                response_parts.append(f"- Markdown链接：{self._build_source_markdown(cloud_url)}")

            if original_file_url and original_file_url != display_source:
                original_label = original_filename or "原文件"
                response_parts.append(f"- 原文件链接：[{original_label}]({self._encode_http_url(original_file_url)})")

            if related_file:
                response_parts.append(f"- 关联文件：`{related_file}`")
        response_parts.append("")
    
    def _get_fallback_message(self, user_intent: str, teaching_use: str) -> str:
        """
        V43.1：生成教学用途降级提示信息
        
        Args:
            user_intent: 用户意图（复习课/练习课/新授课）
            teaching_use: 课件实际教学用途
        
        Returns:
            降级提示信息，如果不需要提示则返回空字符串
        """
        # 定义降级关系
        fallback_map = {
            '复习课': {
                '练习课': '这是练习课课件，可用于复习参考',
                '习题课': '这是习题课课件，可用于复习参考',
                '新授课': '这是新授课课件，可作为复习参考资料（数据库中暂无复习课课件）',
            },
            '练习课': {
                '习题课': '这是习题课课件，可用于练习参考',
                '新授课': '这是新授课课件，可作为练习参考资料（数据库中暂无练习课课件）',
            },
            '习题课': {
                '练习课': '这是练习课课件，可用于习题参考',
                '新授课': '这是新授课课件，可作为习题参考资料（数据库中暂无习题课课件）',
            }
        }
        
        # 检查是否有降级关系
        if user_intent in fallback_map:
            for fallback_type, message in fallback_map[user_intent].items():
                if fallback_type in teaching_use:
                    return message
        
        return ""
