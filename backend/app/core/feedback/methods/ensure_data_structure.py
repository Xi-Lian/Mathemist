from .._shared import *


class _EnsureDataStructureMixin:
    def _ensure_data_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """确保数据结构完整"""
        # 确保基本结构存在
        if "resource_feedback" not in data:
            data["resource_feedback"] = {}
        if "improvement_suggestions" not in data:
            data["improvement_suggestions"] = []
        if "user_feedback_history" not in data:
            data["user_feedback_history"] = {}
        if "feedback_processing" not in data:
            data["feedback_processing"] = {}
        if "statistics" not in data:
            data["statistics"] = {}
        if "config" not in data:
            data["config"] = {}
        
        # 确保统计信息完整
        stats = data["statistics"]
        if "total_likes" not in stats:
            stats["total_likes"] = 0
        if "total_dislikes" not in stats:
            stats["total_dislikes"] = 0
        if "total_feedback" not in stats:
            stats["total_feedback"] = 0
        if "total_suggestions" not in stats:
            stats["total_suggestions"] = len(data.get("improvement_suggestions", []))
        if "feedback_by_theme" not in stats:
            stats["feedback_by_theme"] = {}
        if "feedback_by_type" not in stats:
            stats["feedback_by_type"] = {}
        if "feedback_by_date" not in stats:
            stats["feedback_by_date"] = {}
        if "satisfaction_score" not in stats:
            stats["satisfaction_score"] = 0.0
        
        # 确保配置信息完整
        config = data["config"]
        if "feedback_rate_limit" not in config:
            config["feedback_rate_limit"] = 10
        if "feedback_expiry_days" not in config:
            config["feedback_expiry_days"] = 365
        
        # 为旧数据生成反馈ID
        feedback_id_counter = 1
        for resource_id, feedbacks in data["resource_feedback"].items():
            for feedback in feedbacks:
                if "feedback_id" not in feedback:
                    feedback["feedback_id"] = f"feedback_old_{feedback_id_counter}"
                    feedback_id_counter += 1
                if "user_id" not in feedback:
                    feedback["user_id"] = "anonymous"
                if "status" not in feedback:
                    feedback["status"] = "processed"
        
        for suggestion in data["improvement_suggestions"]:
            if "feedback_id" not in suggestion:
                suggestion["feedback_id"] = f"feedback_old_{feedback_id_counter}"
                feedback_id_counter += 1
            if "user_id" not in suggestion:
                suggestion["user_id"] = "anonymous"
            if "status" not in suggestion:
                suggestion["status"] = "processed"
        
        # 重新计算统计信息
        self.feedback_data = data
        self._update_statistics()
        
        return data
