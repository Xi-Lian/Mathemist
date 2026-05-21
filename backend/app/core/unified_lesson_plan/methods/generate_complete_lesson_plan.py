from .._shared import *


class _GenerateCompleteLessonPlanMixin:
    def _generate_complete_lesson_plan(
        self,
        session_id: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成完整教案
        
        Args:
            session_id: 会话ID
            session: 会话状态
        
        Returns:
            生成结果
        """
        collected_info = session["collected_info"]
        topic = collected_info.get("topic", "")
        
        print(f"🚀 开始生成完整教案: {topic}")
        
        # 更新进度为80%（正在生成）
        session["progress"] = 80
        
        # 1. 构建增强的用户输入
        enhanced_input = self._build_enhanced_input(collected_info)
        
        # 2. 检索相关资源
        retrieved_resources = self.resource_retriever.retrieve(
            enhanced_input,
            intent="generate_lesson_plan"
        )
        
        theory_resources = retrieved_resources.get("theory_resources", [])
        lesson_plan_patterns = retrieved_resources.get("lesson_plan_patterns", [])
        excellent_case_resources = retrieved_resources.get("excellent_case_resources", [])
        
        # 限制资源数量，确保生成的教案更加聚焦
        max_resources = 5  # 最多使用5个理论资源
        max_patterns = 3   # 最多使用3个教案示例
        max_excellent_cases = 3  # 最多使用3个优秀案例分析
        theory_resources = theory_resources[:max_resources]
        lesson_plan_patterns = lesson_plan_patterns[:max_patterns]
        excellent_case_resources = excellent_case_resources[:max_excellent_cases]
        
        print(f"📚 理论资源: {len(theory_resources)}条 (限制为{max_resources}条)")
        print(f"📄 教案示例: {len(lesson_plan_patterns)}条 (限制为{max_patterns}条)")
        print(f"🏆 优秀案例分析: {len(excellent_case_resources)}条 (限制为{max_excellent_cases}条)")
        
        # 3. 生成教案
        # V48.0新增：从会话中获取使用场景，默认为日常教学
        usage_scenario = session.get("collected_info", {}).get("usage_scenario", "daily_teaching")
        print(f"🎯 V48.0使用场景: {usage_scenario}")
        
        lesson_plan_content = self.lesson_plan_generator.generate(
            enhanced_input,
            theory_resources,
            lesson_plan_patterns,
            excellent_case_resources,
            usage_scenario  # V48.0新增：传递使用场景
        )
        
        session["lesson_plan"] = lesson_plan_content
        # 存储最新生成的教案
        self.latest_lesson_plan = lesson_plan_content
        self.latest_topic = topic
        # 保存最新教案到文件
        self._save_latest_lesson_plan()
        # 更新会话最后活动时间
        session["last_activity"] = str(time.time())  # 使用真实的时间戳
        # 更新进度为100%（完成）
        session["progress"] = 100
        
        # 4. 构建响应
        summary = self._generate_summary(lesson_plan_content)
        try:
            response = self._generate_lesson_plan_dialogue(
                mode="completed",
                topic=topic,
                progress=100,
                collected_info=collected_info,
                missing_items=[],
                extra_context=f"教案摘要：{summary}",
            )
        except Exception as exc:
            print(f"⚠️ 教案完成回复生成失败，使用降级文案: {exc}")
            response = f"“{topic}”的教案已经生成好了。先给你一个摘要：{summary}\n\n如果你要，我可以继续帮你查看完整教案、按意见修改，或者直接导出。"
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "completed",
            "response": response,
            "progress": 100,
            "lesson_plan": lesson_plan_content,
            "collected_info": collected_info,
            "conversation_history": session["conversation_history"],
            "export_available": True
        }
