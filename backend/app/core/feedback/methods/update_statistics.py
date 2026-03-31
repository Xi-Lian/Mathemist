from .._shared import *


class _UpdateStatisticsMixin:
    def _update_statistics(self):
        """更新统计信息"""
        # 重置统计信息
        self.feedback_data["statistics"]["total_likes"] = 0
        self.feedback_data["statistics"]["total_dislikes"] = 0
        self.feedback_data["statistics"]["total_feedback"] = 0
        self.feedback_data["statistics"]["total_suggestions"] = len(self.feedback_data["improvement_suggestions"])
        self.feedback_data["statistics"]["feedback_by_theme"] = {}
        self.feedback_data["statistics"]["feedback_by_type"] = {}
        self.feedback_data["statistics"]["feedback_by_date"] = {}
        
        # 计算资源反馈统计
        total_feedback = 0
        total_likes = 0
        
        for resource_id, feedbacks in self.feedback_data["resource_feedback"].items():
            for feedback in feedbacks:
                total_feedback += 1
                if feedback["is_like"]:
                    total_likes += 1
                
                # 按资源类型统计
                resource_type = feedback.get("resource_type", "unknown")
                if resource_type not in self.feedback_data["statistics"]["feedback_by_type"]:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type] = {"likes": 0, "dislikes": 0}
                if feedback["is_like"]:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type]["likes"] += 1
                else:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type]["dislikes"] += 1
                
                # 按日期统计
                date = feedback["timestamp"].split('T')[0]
                if date not in self.feedback_data["statistics"]["feedback_by_date"]:
                    self.feedback_data["statistics"]["feedback_by_date"][date] = {"likes": 0, "dislikes": 0, "suggestions": 0}
                if feedback["is_like"]:
                    self.feedback_data["statistics"]["feedback_by_date"][date]["likes"] += 1
                else:
                    self.feedback_data["statistics"]["feedback_by_date"][date]["dislikes"] += 1
        
        # 计算建议按日期统计
        for suggestion in self.feedback_data["improvement_suggestions"]:
            date = suggestion["timestamp"].split('T')[0]
            if date not in self.feedback_data["statistics"]["feedback_by_date"]:
                self.feedback_data["statistics"]["feedback_by_date"][date] = {"likes": 0, "dislikes": 0, "suggestions": 0}
            self.feedback_data["statistics"]["feedback_by_date"][date]["suggestions"] += 1
        
        # 更新统计信息
        self.feedback_data["statistics"]["total_likes"] = total_likes
        self.feedback_data["statistics"]["total_dislikes"] = total_feedback - total_likes
        self.feedback_data["statistics"]["total_feedback"] = total_feedback
        
        # 计算满意度分数
        if total_feedback > 0:
            self.feedback_data["statistics"]["satisfaction_score"] = round(total_likes / total_feedback, 2)
        else:
            self.feedback_data["statistics"]["satisfaction_score"] = 0.0
