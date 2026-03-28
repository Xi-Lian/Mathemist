"""
用户反馈系统

功能：
- 记录用户对资源的点赞/点踩反馈
- 记录详细的反馈原因
- 记录改进建议
- 提供反馈数据分析功能
- 提供反馈处理状态跟踪
- 提供反馈趋势分析
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 反馈数据存储路径
FEEDBACK_DATA_DIR = Path(__file__).parent.parent.parent / "data"
FEEDBACK_FILE = FEEDBACK_DATA_DIR / "user_feedback.json"


class UserFeedbackSystem:
    """用户反馈系统"""
    
    def __init__(self):
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict[str, Any]:
        """加载反馈数据"""
        if FEEDBACK_FILE.exists():
            try:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保数据结构完整
                    return self._ensure_data_structure(data)
            except Exception as e:
                print(f"⚠️  加载反馈数据失败: {e}")
                return self._get_default_structure()
        return self._get_default_structure()
    
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
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """获取默认数据结构"""
        return {
            "resource_feedback": {},  # 资源反馈: {resource_id: [{...}]}
            "improvement_suggestions": [],  # 改进建议列表
            "user_feedback_history": {},  # 用户反馈历史: {user_id: [{...}]}
            "feedback_processing": {},  # 反馈处理状态: {feedback_id: {...}}
            "statistics": {
                "total_likes": 0,
                "total_dislikes": 0,
                "total_feedback": 0,
                "total_suggestions": 0,
                "feedback_by_theme": {},
                "feedback_by_type": {},
                "feedback_by_date": {},
                "satisfaction_score": 0.0
            },
            "config": {
                "feedback_rate_limit": 10,  # 每小时最大反馈次数
                "feedback_expiry_days": 365  # 反馈数据保留天数
            }
        }
    
    def _save_feedback(self):
        """保存反馈数据"""
        FEEDBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存反馈数据失败: {e}")
    
    def _generate_feedback_id(self) -> str:
        """生成反馈ID"""
        return f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _clean_expired_feedback(self):
        """清理过期的反馈数据"""
        expiry_days = self.feedback_data.get("config", {}).get("feedback_expiry_days", 365)
        cutoff_date = datetime.now() - timedelta(days=expiry_days)
        
        # 清理资源反馈
        for resource_id, feedbacks in list(self.feedback_data["resource_feedback"].items()):
            filtered_feedbacks = []
            for feedback in feedbacks:
                feedback_date = datetime.fromisoformat(feedback["timestamp"])
                if feedback_date > cutoff_date:
                    filtered_feedbacks.append(feedback)
            if filtered_feedbacks:
                self.feedback_data["resource_feedback"][resource_id] = filtered_feedbacks
            else:
                del self.feedback_data["resource_feedback"][resource_id]
        
        # 清理改进建议
        filtered_suggestions = []
        for suggestion in self.feedback_data["improvement_suggestions"]:
            suggestion_date = datetime.fromisoformat(suggestion["timestamp"])
            if suggestion_date > cutoff_date:
                filtered_suggestions.append(suggestion)
        self.feedback_data["improvement_suggestions"] = filtered_suggestions
        
        # 清理用户反馈历史
        for user_id, feedbacks in list(self.feedback_data["user_feedback_history"].items()):
            filtered_feedbacks = []
            for feedback in feedbacks:
                feedback_date = datetime.fromisoformat(feedback["timestamp"])
                if feedback_date > cutoff_date:
                    filtered_feedbacks.append(feedback)
            if filtered_feedbacks:
                self.feedback_data["user_feedback_history"][user_id] = filtered_feedbacks
            else:
                del self.feedback_data["user_feedback_history"][user_id]
    
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
    
    def check_feedback_rate_limit(self, user_id: str) -> bool:
        """
        检查用户反馈频率限制
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否允许反馈
        """
        rate_limit = self.feedback_data.get("config", {}).get("feedback_rate_limit", 10)
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        user_feedbacks = self.feedback_data["user_feedback_history"].get(user_id, [])
        recent_feedbacks = [f for f in user_feedbacks if datetime.fromisoformat(f["timestamp"]) > one_hour_ago]
        
        return len(recent_feedbacks) < rate_limit
    
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
    
    def get_resource_feedback(self, resource_id: str) -> List[Dict[str, Any]]:
        """获取资源的所有反馈"""
        return self.feedback_data["resource_feedback"].get(resource_id, [])
    
    def get_user_feedback_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的反馈历史"""
        return self.feedback_data["user_feedback_history"].get(user_id, [])
    
    def get_feedback_processing_status(self, feedback_id: str) -> Dict[str, Any]:
        """获取反馈处理状态"""
        return self.feedback_data["feedback_processing"].get(feedback_id, {})
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.feedback_data["statistics"]
    
    def get_improvement_suggestions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取改进建议"""
        suggestions = self.feedback_data["improvement_suggestions"]
        return suggestions[-limit:] if limit > 0 else suggestions
    
    def get_disliked_resources(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取被点踩最多的资源"""
        disliked = []
        for resource_id, feedbacks in self.feedback_data["resource_feedback"].items():
            dislike_count = sum(1 for f in feedbacks if not f["is_like"])
            if dislike_count > 0:
                disliked.append({
                    "resource_id": resource_id,
                    "dislike_count": dislike_count,
                    "feedbacks": feedbacks
                })
        disliked.sort(key=lambda x: x["dislike_count"], reverse=True)
        return disliked[:limit]
    
    def get_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取反馈趋势"""
        trends = {
            "daily": [],
            "total": {
                "likes": 0,
                "dislikes": 0,
                "suggestions": 0
            }
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 按日期统计
        for date_str, data in self.feedback_data["statistics"]["feedback_by_date"].items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= cutoff_date:
                trends["daily"].append({
                    "date": date_str,
                    "likes": data.get("likes", 0),
                    "dislikes": data.get("dislikes", 0),
                    "suggestions": data.get("suggestions", 0)
                })
                trends["total"]["likes"] += data.get("likes", 0)
                trends["total"]["dislikes"] += data.get("dislikes", 0)
                trends["total"]["suggestions"] += data.get("suggestions", 0)
        
        # 按日期排序
        trends["daily"].sort(key=lambda x: x["date"])
        
        return trends
    
    def get_resource_satisfaction(self, resource_id: str) -> Dict[str, Any]:
        """获取资源满意度"""
        feedbacks = self.feedback_data["resource_feedback"].get(resource_id, [])
        if not feedbacks:
            return {
                "resource_id": resource_id,
                "total_feedback": 0,
                "likes": 0,
                "dislikes": 0,
                "satisfaction_score": 0.0,
                "recent_feedback": []
            }
        
        total_feedback = len(feedbacks)
        likes = sum(1 for f in feedbacks if f["is_like"])
        dislikes = total_feedback - likes
        satisfaction_score = round(likes / total_feedback, 2) if total_feedback > 0 else 0.0
        
        # 获取最近的5条反馈
        recent_feedback = sorted(feedbacks, key=lambda x: x["timestamp"], reverse=True)[:5]
        
        return {
            "resource_id": resource_id,
            "total_feedback": total_feedback,
            "likes": likes,
            "dislikes": dislikes,
            "satisfaction_score": satisfaction_score,
            "recent_feedback": recent_feedback
        }
    
    def export_feedback_data(self, export_path: str = None) -> str:
        """导出反馈数据"""
        if export_path is None:
            export_path = FEEDBACK_DATA_DIR / f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 反馈数据已导出到: {export_path}")
            return str(export_path)
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""


# 全局反馈系统实例
_feedback_system = None


def get_feedback_system() -> UserFeedbackSystem:
    """获取反馈系统实例"""
    global _feedback_system
    if _feedback_system is None:
        _feedback_system = UserFeedbackSystem()
    return _feedback_system
