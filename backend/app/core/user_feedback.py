"""
用户反馈系统

功能：
- 记录用户对资源的点赞/点踩反馈
- 记录详细的反馈原因
- 记录改进建议
- 提供反馈数据分析功能
"""

import json
import os
from datetime import datetime
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
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载反馈数据失败: {e}")
                return self._get_default_structure()
        return self._get_default_structure()
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """获取默认数据结构"""
        return {
            "resource_feedback": {},  # 资源反馈: {resource_id: [{...}]}
            "improvement_suggestions": [],  # 改进建议列表
            "statistics": {
                "total_likes": 0,
                "total_dislikes": 0,
                "feedback_by_theme": {},
                "feedback_by_type": {}
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
    
    def record_resource_feedback(
        self,
        resource_id: str,
        is_like: bool,
        query: str = "",
        resource_type: str = "",
        metadata: Dict[str, Any] = None,
        dislike_reason: str = ""
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
        
        Returns:
            是否成功
        """
        try:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "resource_type": resource_type,
                "is_like": is_like,
                "dislike_reason": dislike_reason if not is_like else "",
                "metadata": metadata or {}
            }
            
            # 记录资源反馈
            if resource_id not in self.feedback_data["resource_feedback"]:
                self.feedback_data["resource_feedback"][resource_id] = []
            self.feedback_data["resource_feedback"][resource_id].append(feedback_entry)
            
            # 更新统计
            if is_like:
                self.feedback_data["statistics"]["total_likes"] += 1
            else:
                self.feedback_data["statistics"]["total_dislikes"] += 1
            
            # 按资源类型统计
            if resource_type:
                if resource_type not in self.feedback_data["statistics"]["feedback_by_type"]:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type] = {"likes": 0, "dislikes": 0}
                if is_like:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type]["likes"] += 1
                else:
                    self.feedback_data["statistics"]["feedback_by_type"][resource_type]["dislikes"] += 1
            
            self._save_feedback()
            print(f"✅ 记录反馈成功: resource_id={resource_id}, is_like={is_like}")
            return True
        except Exception as e:
            print(f"❌ 记录反馈失败: {e}")
            return False
    
    def record_improvement_suggestion(
        self,
        query: str,
        suggestion: str,
        contact: str = ""
    ) -> bool:
        """
        记录改进建议
        
        Args:
            query: 用户原始查询
            suggestion: 改进建议内容
            contact: 联系方式（可选）
        
        Returns:
            是否成功
        """
        try:
            suggestion_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "suggestion": suggestion,
                "contact": contact
            }
            self.feedback_data["improvement_suggestions"].append(suggestion_entry)
            self._save_feedback()
            print(f"✅ 记录改进建议成功")
            return True
        except Exception as e:
            print(f"❌ 记录改进建议失败: {e}")
            return False
    
    def get_resource_feedback(self, resource_id: str) -> List[Dict[str, Any]]:
        """获取资源的所有反馈"""
        return self.feedback_data["resource_feedback"].get(resource_id, [])
    
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
