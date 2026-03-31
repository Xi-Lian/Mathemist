from .._shared import *


class _ApplyTopicExclusionMixin:
    def _apply_topic_exclusion(self, classified: Dict[str, Any], clarified_topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        V33.0: 应用主题排除过滤
        
        Args:
            classified: 分类后的资源
            clarified_topic: 澄清后的主题信息
        
        Returns:
            过滤后的资源
        """
        exclude_keywords = clarified_topic.get('exclude_keywords_matched', [])
        if not exclude_keywords:
            return classified
        
        for category in classified:
            if isinstance(classified[category], list):
                filtered = []
                for resource in classified[category]:
                    content = resource.get('content', '')
                    title = resource.get('title', '')
                    knowledge_tags = resource.get('metadata', {}).get('知识点标签', '')
                    
                    should_exclude = False
                    for keyword in exclude_keywords:
                        if keyword in content or keyword in title or keyword in knowledge_tags:
                            should_exclude = True
                            print(f"   🔍 V33.0主题排除移除: '{title}' (排除关键词: {keyword})")
                            break
                    
                    if not should_exclude:
                        filtered.append(resource)
                
                classified[category] = filtered
        
        return classified
