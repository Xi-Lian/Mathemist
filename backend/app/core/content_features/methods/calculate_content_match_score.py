from .._shared import *


class _CalculateContentMatchScoreMixin:
    def calculate_content_match_score(self, resource_features: Dict[str, Any], query_features: Dict[str, Any], resource_metadata: Dict[str, Any] = None, resource_content: str = None) -> float:
        """
        计算内容匹配得分
        
        Args:
            resource_features: 资源特征（教案）
            query_features: 查询特征
            resource_metadata: 资源元数据（习题）
            resource_content: 资源内容（习题）
            
        Returns:
            匹配得分 (0-1)
        """
        if not query_features['has_content_requirement']:
            return 1.0  # 没有内容要求，默认满分
        
        scores = []
        
        # V12.0改进：使用主观意图解释器的难度匹配逻辑
        if query_features.get('subjective_intent') and resource_metadata:
            # 使用新的主观意图匹配逻辑
            subjective_intent = query_features['subjective_intent']
            difficulty_str = resource_metadata.get('难度（1-5）', '')
            
            if difficulty_str and subjective_intent['interpreted_dimensions']:
                # 获取第一个主观词汇的维度
                first_word = subjective_intent['original_words'][0]
                query_difficulty = subjective_intent['interpreted_dimensions'][first_word]
                
                difficulty_score = self.subjective_interpreter.calculate_difficulty_match_score(
                    query_difficulty, difficulty_str
                )
                scores.append(difficulty_score)
        
        # 原有的难度匹配逻辑（作为后备）
        elif query_features['required_difficulty'] and resource_metadata:
            difficulty_str = resource_metadata.get('难度（1-5）', '')
            if difficulty_str:
                try:
                    difficulty = int(difficulty_str)
                    # 简单: 1-2, 中等: 3, 困难: 4-5
                    if query_features['required_difficulty'] == '简单':
                        difficulty_score = 1.0 if difficulty <= 2 else 0.0
                    elif query_features['required_difficulty'] == '中等':
                        difficulty_score = 1.0 if difficulty == 3 else 0.0
                    elif query_features['required_difficulty'] == '困难':
                        difficulty_score = 1.0 if difficulty >= 4 else 0.0
                    else:
                        difficulty_score = 1.0
                    scores.append(difficulty_score)
                except:
                    pass
        
        # 习题类型匹配
        # V9.5改进：对于"计算题"，放宽限制，只要不是"选择题"都算匹配
        # V10.0改进：增强题型识别，支持"应用题"、"综合题"、"方程组"等题型
        # V11.0改进：增强应用题识别，基于场景关键词库
        if query_features['required_exercise_type'] and resource_metadata:
            exercise_type = resource_metadata.get('题目类型', '')
            required_type = query_features['required_exercise_type']
            
            # 特殊处理应用题
            if required_type == '应用题':
                # 检查资源内容和元数据，判断是否是应用题
                resource_content = resource_content or resource_metadata.get('题干', '') + resource_metadata.get('题目描述', '')
                is_app = self.is_application_problem(resource_content, resource_metadata)
                scores.append(1.0 if is_app else 0.0)
            # V9.5改进：对于"计算题"，只要不是"选择题"都算匹配
            elif required_type == '计算题':
                # 如果是选择题，得0分；否则得1分
                if exercise_type and '选择题' in exercise_type:
                    scores.append(0.0)
                else:
                    scores.append(1.0)
            # 其他题型匹配
            else:
                # 精确匹配题目类型
                if required_type in exercise_type:
                    scores.append(1.0)
                else:
                    scores.append(0.0)
        
        # 教学方法匹配（教案）
        if query_features['required_methods'] and resource_features.get('teaching_methods'):
            method_matches = set(resource_features['teaching_methods']) & set(query_features['required_methods'])
            method_score = len(method_matches) / len(query_features['required_methods'])
            scores.append(method_score)
        
        # 教学环节匹配（教案）
        if query_features['required_stages'] and resource_features.get('teaching_stages'):
            stage_matches = set(resource_features['teaching_stages']) & set(query_features['required_stages'])
            stage_score = len(stage_matches) / len(query_features['required_stages'])
            scores.append(stage_score)
        
        # 教学手段匹配（教案）
        if query_features['required_tools'] and resource_features.get('teaching_tools'):
            tool_matches = set(resource_features['teaching_tools']) & set(query_features['required_tools'])
            tool_score = len(tool_matches) / len(query_features['required_tools'])
            scores.append(tool_score)
        
        # V12.0改进2：年级匹配
        if query_features.get('required_grade') and resource_metadata:
            grade_enricher = get_grade_enricher()
            resource_grade_level = resource_metadata.get('grade_level', 0)
            query_grade = query_features['required_grade']
            
            grade_score = grade_enricher.calculate_grade_match_score(
                resource_grade_level, query_grade
            )
            
            # 只有当年级匹配得分较低时才影响总分
            if grade_score < 0.5:
                scores.append(grade_score)
            elif grade_score < 0.8:
                # 部分匹配，轻微影响
                scores.append(grade_score)
        
        if not scores:
            return 1.0
        
        # 返回平均得分
        return sum(scores) / len(scores)
