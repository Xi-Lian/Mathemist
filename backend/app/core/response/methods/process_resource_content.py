from .._shared import *


class _ProcessResourceContentMixin:
    def _process_resource_content(
        self, 
        category: str, 
        title: str, 
        content: str,
        scenario: str = "search",
        resource: Dict[str, Any] = None
    ) -> str:
        """
        处理资源内容
        
        Args:
            category: 资源分类
            title: 资源标题
            content: 原始内容
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景
        
        Returns:
            处理后的内容
        """
        # 习题资源特殊处理
        if category == "习题资源":
            return self._build_exercise_preview(resource or {}, content)
        
        # 课件、课例、GGB只显示文件名
        if category in ["课件资源", "课例资源", "GGB资源"]:
            return "（请查看文件）"
        
        # 教案和教学大纲，根据场景决定是否显示内容
        if category in ["教案资源", "教学大纲"]:
            # 资源检索场景：只显示文件名，不显示内容
            if scenario == "search":
                return "（请查看文件）"
            # 教案生成场景：返回完整内容
            else:
                return content
        
        # 其他资源，生成摘要
        return self.content_processor.generate_summary(content, max_length=150)

    def _build_exercise_preview(self, resource: Dict[str, Any], fallback_content: str) -> str:
        lines: List[str] = []

        question_type = (resource.get("question_type") or "").strip()
        question = (resource.get("question") or "").strip()
        answer = (resource.get("answer") or "").strip()
        knowledge_tags = (resource.get("knowledge_tags") or "").strip()
        difficulty = (resource.get("difficulty") or "").strip()
        usage_scene = (resource.get("usage_scene") or "").strip()
        filename = (resource.get("filename") or "").strip()
        question_image_url = (resource.get("question_image_url") or "").strip()
        answer_image_url = (resource.get("answer_image_url") or "").strip()
        answer_format = (resource.get("answer_format") or "").strip()

        if question_type:
            lines.append(f"题目类型：{question_type}")
        if question:
            lines.append(f"题目：{question}")
        if question_image_url:
            lines.append("")
            lines.append("题目图片：")
            lines.append(f"![题目图片]({question_image_url})")
            lines.append(f"[打开题目图片]({question_image_url})")
        elif filename:
            lines.append(f"题目文件名：{filename}")

        if answer_image_url:
            lines.append("")
            lines.append("答案图片：")
            lines.append(f"![答案图片]({answer_image_url})")
            lines.append(f"[打开答案图片]({answer_image_url})")
        elif answer:
            answer_label = "解析（LaTeX）" if answer_format == "latex" else "解析"
            lines.append("")
            lines.append(f"{answer_label}：{answer}")

        meta_parts = []
        if knowledge_tags:
            meta_parts.append(f"知识点：{knowledge_tags}")
        if difficulty:
            meta_parts.append(f"难度：{difficulty}")
        if usage_scene:
            meta_parts.append(f"适用场景：{usage_scene}")
        if meta_parts:
            lines.append("")
            lines.extend(meta_parts)

        if not lines:
            return fallback_content
        return "\n".join(lines).strip()
