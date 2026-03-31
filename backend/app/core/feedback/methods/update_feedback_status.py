from .._shared import *


class _UpdateFeedbackStatusMixin:
    def update_feedback_status(
        self,
        feedback_id: str,
        status: str,
        processor_id: str = "system",
        notes: str = ""
    ) -> bool:
        """
        更新反馈处理状态
        
        Args:
            feedback_id: 反馈ID
            status: 状态（pending, processed, resolved, implemented）
            processor_id: 处理者ID
            notes: 处理备注
        
        Returns:
            是否成功
        """
        try:
            if feedback_id not in self.feedback_data["feedback_processing"]:
                print(f"⚠️  反馈ID不存在: {feedback_id}")
                return False
            
            # 更新反馈处理状态
            self.feedback_data["feedback_processing"][feedback_id].update({
                "status": status,
                "processed_at": datetime.now().isoformat(),
                "processor_id": processor_id,
                "notes": notes
            })
            
            # 更新资源反馈状态
            for resource_id, feedbacks in self.feedback_data["resource_feedback"].items():
                for feedback in feedbacks:
                    if feedback.get("feedback_id") == feedback_id:
                        feedback["status"] = status
                        break
            
            # 更新改进建议状态
            for suggestion in self.feedback_data["improvement_suggestions"]:
                if suggestion.get("feedback_id") == feedback_id:
                    suggestion["status"] = status
                    break
            
            # 更新用户反馈历史状态
            for user_id, feedbacks in self.feedback_data["user_feedback_history"].items():
                for feedback in feedbacks:
                    if feedback.get("feedback_id") == feedback_id:
                        feedback["status"] = status
                        break
            
            self._save_feedback()
            print(f"✅ 更新反馈状态成功: feedback_id={feedback_id}, status={status}")
            return True
        except Exception as e:
            print(f"❌ 更新反馈状态失败: {e}")
            return False
