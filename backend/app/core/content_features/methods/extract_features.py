from .._shared import *


class _ExtractFeaturesMixin:
    def extract_features(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        从教案内容中提取特征标签
        
        Args:
            content: 教案内容
            title: 教案标题
            
        Returns:
            特征标签字典
        """
        features = {
            'teaching_methods': [],  # 教学方法
            'teaching_stages': [],   # 教学环节
            'teaching_tools': [],    # 教学手段
            'has_group_work': False, # 是否有小组合作
            'has_experiment': False, # 是否有实验
            'has_multimedia': False, # 是否使用多媒体
            'has_practice': False,   # 是否有练习环节
            'content_summary': ''    # 内容摘要
        }
        
        if not content:
            return features
        
        # 提取教学方法
        for method, keywords in self.TEACHING_METHODS.items():
            if self._check_keywords(content, keywords):
                features['teaching_methods'].append(method)
        
        # 提取教学环节
        for stage, keywords in self.TEACHING_STAGES.items():
            if self._check_keywords(content, keywords):
                features['teaching_stages'].append(stage)
        
        # 提取教学手段
        for tool, keywords in self.TEACHING_TOOLS.items():
            if self._check_keywords(content, keywords):
                features['teaching_tools'].append(tool)
        
        # 设置布尔特征
        features['has_group_work'] = '小组讨论' in features['teaching_methods']
        features['has_experiment'] = '实验探究' in features['teaching_methods']
        features['has_multimedia'] = '多媒体教学' in features['teaching_methods'] or '多媒体' in features['teaching_tools']
        features['has_practice'] = '练习巩固' in features['teaching_methods'] or '课堂练习' in features['teaching_stages']
        
        # 生成内容摘要
        features['content_summary'] = self._generate_summary(content)
        
        return features
