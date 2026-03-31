from .._shared import *


class _ProcessFeedbackMixin:
    def process_feedback(self, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户反馈
        
        Args:
            user_feedback: 用户反馈，包含feedback_type和相关数据
        
        Returns:
            处理结果
        """
        feedback_type = user_feedback.get('feedback_type')
        
        if feedback_type == 'theme_correction':
            # 主题修正反馈
            correct_theme = user_feedback.get('correct_theme')
            wrong_theme = user_feedback.get('wrong_theme')
            content = user_feedback.get('content', '')
            
            if correct_theme and wrong_theme:
                # 调整主题权重
                self.update_theme_weights({correct_theme: 0.1, wrong_theme: -0.1})
                print(f"   🔄 主题反馈处理: 修正 {wrong_theme} -> {correct_theme}")
                
                # 重新检测主题
                new_themes = self.dynamic_theme_detection(content)
                return {
                    'status': 'success',
                    'message': '主题权重已更新',
                    'new_themes': new_themes
                }
        
        elif feedback_type == 'relevance_feedback':
            # 相关性反馈
            resource_id = user_feedback.get('resource_id')
            relevance_score = user_feedback.get('relevance_score')
            
            if resource_id and relevance_score is not None:
                # 这里可以实现更复杂的相关性反馈处理
                print(f"   🔄 相关性反馈: {resource_id} -> {relevance_score}")
                return {
                    'status': 'success',
                    'message': '相关性反馈已记录'
                }
        
        return {
            'status': 'error',
            'message': '无效的反馈类型'
        }


# 全局主题匹配器实例
_theme_matcher = None
