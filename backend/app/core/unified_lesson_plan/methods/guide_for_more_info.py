from .._shared import *


class _GuideForMoreInfoMixin:
    def _generate_lesson_plan_dialogue(
        self,
        *,
        mode: str,
        topic: str,
        progress: int,
        collected_info: Dict[str, Any],
        missing_items: List[str],
        extra_context: str = "",
    ) -> str:
        prompt = ChatPromptTemplate.from_template(
            """
你是一个高中数学教案协作助手。你的任务不是直接生成完整教案正文，而是基于当前状态给用户回复一段自然、简洁、有上下文的对话。

模式：{mode}
课题：{topic}
当前进度：{progress}
已收集信息：{collected_info}
仍缺少的信息：{missing_items}
补充上下文：{extra_context}

要求：
1. 回复必须像真实对话，不要套模板腔。
2. 如果模式是 welcome，要简短说明你能继续做什么，并引导用户直接给主题或关键条件。
3. 如果模式是 guiding，要结合已收集信息，只追问最关键的 2-4 项，不要把所有字段机械罗列。
4. 如果模式是 completed，要告诉用户教案已经生成好，简要概括当前结果，并提示下一步可以查看、修改或导出。
5. 如果模式是 revised，要告诉用户修改已经完成，概括本轮修改重点，并提示可以继续微调或查看完整教案。
6. 直接输出回复正文，不要输出 JSON，不要输出解释。
"""
        )

        model = self.model_config.get_model("lesson_plan")
        chain = prompt | model | StrOutputParser()
        return chain.invoke(
            {
                "mode": mode,
                "topic": topic or "当前课题",
                "progress": f"{progress}%",
                "collected_info": json.dumps(collected_info, ensure_ascii=False),
                "missing_items": "、".join(missing_items) if missing_items else "无",
                "extra_context": extra_context,
            }
        ).strip()

    def _guide_for_more_info(
        self,
        session_id: str,
        session: Dict[str, Any],
        completion_level: LessonPlanInfoCompletion
    ) -> Dict[str, Any]:
        """
        智能引导用户补充信息 - 上下文感知引导
        
        Args:
            session_id: 会话ID
            session: 会话状态
            completion_level: 信息完整度
        
        Returns:
            引导响应
        """
        collected_info = session["collected_info"]
        topic = collected_info.get("topic", "这个课题")
        progress = session.get("progress", 0)
        
        # 生成进度条
        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        
        # 分析已有信息，生成个性化的引导问题
        missing_items = []
        if "teaching_goals" not in collected_info:
            missing_items.append("教学目标")
        if "teaching_methods" not in collected_info:
            missing_items.append("教学方法")
        if "student_level" not in collected_info:
            missing_items.append("学生水平/年级")
        if "class_hours" not in collected_info:
            missing_items.append("课时安排")
        if "key_points" not in collected_info:
            missing_items.append("教学重点")
        if "difficulties" not in collected_info:
            missing_items.append("教学难点")
        
        try:
            response = self._generate_lesson_plan_dialogue(
                mode="guiding",
                topic=topic,
                progress=progress,
                collected_info=collected_info,
                missing_items=missing_items,
                extra_context=f"信息完整度={completion_level.value}",
            )
        except Exception as exc:
            print(f"⚠️ 教案引导回复生成失败，使用降级文案: {exc}")
            missing_text = "、".join(missing_items[:4]) if missing_items else "教学目标、课时安排等关键信息"
            response = f"关于“{topic}”，我还需要你再补充几个关键信息：{missing_text}。你也可以直接回复“直接生成”，我按现有信息先出一版。"
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "guiding",
            "response": response,
            "progress": progress,
            "collected_info": collected_info,
            "conversation_history": session["conversation_history"],
            "missing_items": missing_items
        }
