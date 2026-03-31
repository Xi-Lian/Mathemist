from .._shared import *


class _ExtractQueryContentFeaturesMixin:
    def extract_query_content_features(self, query: str) -> Dict[str, Any]:
        """
        从用户查询中提取内容特征要求
        
        Args:
            query: 用户查询
            
        Returns:
            查询特征字典
        """
        features = {
            'has_content_requirement': False,  # 是否有内容要求
            'required_methods': [],            # 要求的教学方法
            'required_stages': [],             # 要求的教学环节
            'required_tools': [],              # 要求的教学手段
            'required_difficulty': None,        # 要求的习题难度
            'required_exercise_type': None,     # 要求的习题类型
            'query_type': 'theme',              # 查询类型：theme(主题) 或 content(内容)
            # V12.0新增：主观意图理解
            'subjective_intent': None,          # 主观意图解释结果
            'has_subjective_word': False,       # 是否包含主观词汇
            # V12.0改进2：年级识别
            'required_grade': None,             # 要求的年级
            'has_grade_requirement': False,     # 是否有年级要求
        }
        
        # V12.0新增：首先进行主观意图解释
        subjective_features = self.subjective_interpreter.interpret_intent(query)
        if subjective_features['original_words']:
            features['subjective_intent'] = subjective_features
            features['has_subjective_word'] = True
            features['has_content_requirement'] = True
            features['query_type'] = 'content'
            
            # 从主观意图推断难度要求
            if subjective_features['interpreted_dimensions']:
                # 获取第一个检测到的主观词汇的难度范围
                first_word = subjective_features['original_words'][0]
                dim = subjective_features['interpreted_dimensions'][first_word]
                diff_range = dim['difficulty_range']
                
                # 映射到原有的难度分类
                if diff_range[1] <= 2:
                    features['required_difficulty'] = '简单'
                elif diff_range[0] >= 4:
                    features['required_difficulty'] = '困难'
                else:
                    features['required_difficulty'] = '中等'
        
        # 检查是否包含内容要求关键词
        all_content_keywords = []
        for keywords in self.TEACHING_METHODS.values():
            all_content_keywords.extend(keywords)
        for keywords in self.TEACHING_STAGES.values():
            all_content_keywords.extend(keywords)
        for keywords in self.TEACHING_TOOLS.values():
            all_content_keywords.extend(keywords)
        for keywords in self.EXERCISE_DIFFICULTY.values():
            all_content_keywords.extend(keywords)
        for keywords in self.EXERCISE_TYPES.values():
            all_content_keywords.extend(keywords)
        
        # 检查查询中是否包含内容特征词
        for keyword in all_content_keywords:
            if keyword in query:
                features['has_content_requirement'] = True
                break
        
        # 如果包含内容要求，提取具体的教学方法、环节、手段
        if features['has_content_requirement']:
            features['query_type'] = 'content'
            
            # 提取教学方法要求
            for method, keywords in self.TEACHING_METHODS.items():
                if self._check_keywords(query, keywords):
                    features['required_methods'].append(method)
            
            # 提取教学环节要求
            for stage, keywords in self.TEACHING_STAGES.items():
                if self._check_keywords(query, keywords):
                    features['required_stages'].append(stage)
            
            # 提取教学手段要求
            for tool, keywords in self.TEACHING_TOOLS.items():
                if self._check_keywords(query, keywords):
                    features['required_tools'].append(tool)
            
            # 提取习题难度要求（如果主观意图没有设置）
            if not features['required_difficulty']:
                for difficulty, keywords in self.EXERCISE_DIFFICULTY.items():
                    if self._check_keywords(query, keywords):
                        features['required_difficulty'] = difficulty
                        break
            
            # 提取习题类型要求
            for ex_type, keywords in self.EXERCISE_TYPES.items():
                if self._check_keywords(query, keywords):
                    features['required_exercise_type'] = ex_type
                    break
        
        # V12.0改进2：年级识别
        grade_enricher = get_grade_enricher()
        grade_info = grade_enricher.infer_grade_from_title(query)
        
        if grade_info:
            features['required_grade'] = grade_info['grade']
            features['has_grade_requirement'] = True
            features['has_content_requirement'] = True
            features['query_type'] = 'content'
        
        return features
