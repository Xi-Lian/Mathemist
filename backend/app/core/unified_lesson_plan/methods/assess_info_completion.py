from .._shared import *


class _AssessInfoCompletionMixin:
    def _assess_info_completion(self, collected_info: Dict[str, Any]) -> LessonPlanInfoCompletion:
        """
        评估信息完整度 - 智能多维度评估体系
        
        评估指标（更合理的权重分配）：
        - 基础信息完整性（35%）- 课题、教学目标、学生水平
        - 内容质量评分（25%）- 各字段内容的丰富度
        - 教学要素完整性（25%）- 教学方法、课时、重难点
        - 输入整体丰富度（15%）- 整体输入的信息量
        
        Args:
            collected_info: 已收集的信息
        
        Returns:
            信息完整度级别
        """
        # 提取各项信息
        has_topic = "topic" in collected_info and collected_info["topic"]
        has_goals = "teaching_goals" in collected_info and collected_info["teaching_goals"]
        has_methods = "teaching_methods" in collected_info and collected_info["teaching_methods"]
        has_student_level = "student_level" in collected_info and collected_info["student_level"]
        has_class_hours = "class_hours" in collected_info and collected_info["class_hours"]
        has_key_points = "key_points" in collected_info and collected_info["key_points"]
        has_difficulties = "difficulties" in collected_info and collected_info["difficulties"]
        
        # 1. 基础信息完整性评分 (0-35)
        base_completeness = 0
        if has_topic:
            base_completeness += 15
        if has_goals:
            base_completeness += 12
        if has_student_level:
            base_completeness += 8
        
        # 2. 内容质量评分 (0-25) - 评估内容丰富度
        content_quality = 0
        if has_topic:
            topic_len = len(collected_info["topic"])
            if topic_len > 10:
                content_quality += 8
            elif topic_len > 5:
                content_quality += 5
            else:
                content_quality += 3
        
        if has_goals:
            goals_len = len(collected_info["teaching_goals"])
            if goals_len > 50:
                content_quality += 10
            elif goals_len > 20:
                content_quality += 7
            else:
                content_quality += 4
        
        if has_methods:
            methods_len = len(collected_info["teaching_methods"])
            if methods_len > 30:
                content_quality += 7
            elif methods_len > 15:
                content_quality += 5
            else:
                content_quality += 3
        
        # 3. 教学要素完整性评分 (0-25)
        teaching_elements = 0
        if has_methods:
            teaching_elements += 10
        if has_class_hours:
            teaching_elements += 5
        if has_key_points:
            teaching_elements += 5
        if has_difficulties:
            teaching_elements += 5
        
        # 4. 输入整体丰富度评分 (0-15)
        overall_richness = 0
        # 计算有多少个字段有值
        total_fields = 0
        if has_topic: total_fields += 1
        if has_goals: total_fields += 1
        if has_methods: total_fields += 1
        if has_student_level: total_fields += 1
        if has_class_hours: total_fields += 1
        if has_key_points: total_fields += 1
        if has_difficulties: total_fields += 1
        
        if total_fields >= 5:
            overall_richness = 15
        elif total_fields >= 4:
            overall_richness = 12
        elif total_fields >= 3:
            overall_richness = 9
        elif total_fields >= 2:
            overall_richness = 6
        else:
            overall_richness = 3
        
        # 计算总分
        total_score = base_completeness + content_quality + teaching_elements + overall_richness
        
        print(f"📊 智能多维度评估得分:")
        print(f"  1. 基础信息完整性: {base_completeness}/35")
        print(f"  2. 内容质量评分: {content_quality}/25")
        print(f"  3. 教学要素完整性: {teaching_elements}/25")
        print(f"  4. 输入整体丰富度: {overall_richness}/15")
        print(f"  📈 总分: {total_score}/100")
        
        # 更合理的阈值设置
        # - 只要有课题+任意一个其他信息，就可以尝试生成（降低门槛）
        # - 有课题+教学目标，就可以认为基本完整
        # - 信息全面时才认为完全完整
        
        # 快速判断：只要有课题 + 任意两个其他字段，就可以生成
        quick_check = has_topic and total_fields >= 3
        
        if quick_check or total_score >= 55:
            print(f"✅ 评估结果: 信息完整 (COMPLETE) - 可以直接生成教案")
            return LessonPlanInfoCompletion.COMPLETE
        elif has_topic and total_fields >= 2 or total_score >= 30:
            print(f"ℹ️ 评估结果: 信息部分完整 (PARTIAL) - 建议补充但也可生成")
            return LessonPlanInfoCompletion.PARTIAL
        else:
            print(f"❓ 评估结果: 信息较少 (MINIMAL) - 需要引导用户补充")
            return LessonPlanInfoCompletion.MINIMAL
