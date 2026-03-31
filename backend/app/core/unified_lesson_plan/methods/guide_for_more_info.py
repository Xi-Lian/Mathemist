from .._shared import *


class _GuideForMoreInfoMixin:
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
        
        # 根据已有信息生成上下文感知的引导
        if completion_level == LessonPlanInfoCompletion.MINIMAL:
            response = f"""好的！让我们一起为「{topic}」设计一份优秀的教案。📝

为了给您生成最贴合需求的教案，我需要了解一些关键信息：

1. **教学目标**：这节课您希望学生达到什么目标？（知识、能力、情感等）
2. **教学方法**：您倾向于用什么教学方法？（探究式、讲授式、问题解决等）
3. **学生情况**：授课对象是哪个年级？学生基础如何？
4. **课时安排**：这节课计划用多少课时？

您可以一次性告诉我这些信息，也可以先回答其中一部分，我们逐步完善！

如果您觉得现有信息已经足够，也可以直接回复"直接生成"，我会基于当前信息为您生成教案。"""
        
        else:  # PARTIAL
            # 生成个性化的引导问题
            personalized_questions = []
            
            if "teaching_goals" not in collected_info:
                if "student_level" in collected_info:
                    personalized_questions.append(f"**教学目标**：针对{collected_info['student_level']}的学生，您希望他们通过这节课达到什么目标？")
                else:
                    personalized_questions.append("**教学目标**：您希望学生通过这节课达到什么目标？（知识、能力、情感等）")
            
            if "teaching_methods" not in collected_info:
                if "student_level" in collected_info:
                    personalized_questions.append(f"**教学方法**：针对{collected_info['student_level']}的学生，您倾向于使用什么教学方法？")
                else:
                    personalized_questions.append("**教学方法**：您倾向于使用什么教学方法？（探究式、讲授式、问题解决等）")
            
            if "student_level" not in collected_info:
                personalized_questions.append("**学生情况**：授课对象是哪个年级？学生基础如何？")
            
            if "class_hours" not in collected_info:
                personalized_questions.append("**课时安排**：这节课计划用多少课时？")
            
            if "key_points" not in collected_info:
                personalized_questions.append(f"**教学重点**：「{topic}」的教学重点是什么？")
            
            if "difficulties" not in collected_info:
                personalized_questions.append(f"**教学难点**：学生学习「{topic}」时可能遇到的困难是什么？")
            
            response = f"""很好！我已经了解到一些关于「{topic}」的信息了。👍

为了生成更完善的教案，我还需要了解：
{chr(10).join([f"- {item}" for item in personalized_questions])}

请告诉我这些信息，或者如果您觉得信息已经足够了，也可以直接回复"直接生成"，我会基于现有信息为您生成教案！"""
        
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
