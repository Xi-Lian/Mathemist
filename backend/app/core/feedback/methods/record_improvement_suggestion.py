from .._shared import *


class _RecordImprovementSuggestionMixin:
    def record_improvement_suggestion(
        self,
        query: str,
        suggestion: str,
        contact: str = "",
        user_id: str = "anonymous"
    ) -> bool:
        """
        记录改进建议
        
        Args:
            query: 用户原始查询
            suggestion: 改进建议内容
            contact: 联系方式（可选）
            user_id: 用户ID（可选）
        
        Returns:
            是否成功
        """
        try:
            # 检查频率限制
            if not self.check_feedback_rate_limit(user_id):
                print(f"⚠️  反馈频率过高: user_id={user_id}")
                return False
            
            feedback_id = self._generate_feedback_id()
            suggestion_entry = {
                "feedback_id": feedback_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "suggestion": suggestion,
                "contact": contact,
                "user_id": user_id,
                "status": "pending"  # pending, processed, implemented
            }
            
            # 记录改进建议
            self.feedback_data["improvement_suggestions"].append(suggestion_entry)
            
            # 记录用户反馈历史
            if user_id not in self.feedback_data["user_feedback_history"]:
                self.feedback_data["user_feedback_history"][user_id] = []
            self.feedback_data["user_feedback_history"][user_id].append({
                "feedback_id": feedback_id,
                "timestamp": suggestion_entry["timestamp"],
                "type": "suggestion",
                "status": "pending"
            })
            
            # 记录反馈处理状态
            self.feedback_data["feedback_processing"][feedback_id] = {
                "timestamp": suggestion_entry["timestamp"],
                "type": "suggestion",
                "status": "pending",
                "processed_at": None,
                "processor_id": None,
                "notes": ""
            }
            
            # 更新统计
            self._update_statistics()
            
            # 清理过期数据
            self._clean_expired_feedback()
            
            self._save_feedback()
            print(f"✅ 记录改进建议成功: feedback_id={feedback_id}")
            return True
        except Exception as e:
            print(f"❌ 记录改进建议失败: {e}")
            return False
