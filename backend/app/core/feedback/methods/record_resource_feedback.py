from .._shared import *


class _RecordResourceFeedbackMixin:
    def record_resource_feedback(
        self,
        resource_id: str,
        is_like: bool,
        query: str = "",
        resource_type: str = "",
        metadata: Dict[str, Any] = None,
        dislike_reason: str = "",
        user_id: str = "anonymous"
    ) -> bool:
        """
        记录资源反馈
        
        Args:
            resource_id: 资源ID
            is_like: 是否点赞
            query: 用户查询
            resource_type: 资源类型
            metadata: 资源元数据
            dislike_reason: 点踩原因（主题不对/难度不合适/类型不对/其他）
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
            feedback_entry = {
                "feedback_id": feedback_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "resource_type": resource_type,
                "is_like": is_like,
                "dislike_reason": dislike_reason if not is_like else "",
                "metadata": metadata or {},
                "user_id": user_id,
                "status": "pending"  # pending, processed, resolved
            }
            
            # 记录资源反馈
            if resource_id not in self.feedback_data["resource_feedback"]:
                self.feedback_data["resource_feedback"][resource_id] = []
            self.feedback_data["resource_feedback"][resource_id].append(feedback_entry)
            
            # 记录用户反馈历史
            if user_id not in self.feedback_data["user_feedback_history"]:
                self.feedback_data["user_feedback_history"][user_id] = []
            self.feedback_data["user_feedback_history"][user_id].append({
                "feedback_id": feedback_id,
                "timestamp": feedback_entry["timestamp"],
                "resource_id": resource_id,
                "is_like": is_like,
                "resource_type": resource_type,
                "status": "pending"
            })
            
            # 记录反馈处理状态
            self.feedback_data["feedback_processing"][feedback_id] = {
                "resource_id": resource_id,
                "timestamp": feedback_entry["timestamp"],
                "is_like": is_like,
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
            print(f"✅ 记录反馈成功: resource_id={resource_id}, is_like={is_like}, feedback_id={feedback_id}")
            return True
        except Exception as e:
            print(f"❌ 记录反馈失败: {e}")
            return False
