from .._shared import *


class _GetFeedbackTrendsMixin:
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
