from .._shared import *


class _GenerateMixin:
    def generate(
        self, 
        user_input: str, 
        theory_resources: List[Dict[str, Any]],
        lesson_plan_patterns: List[Dict[str, Any]]
    ) -> str:
        """
        生成教案
        
        Args:
            user_input: 用户需求
            theory_resources: 理论资源列表
            lesson_plan_patterns: 优秀教案示例列表
        
        Returns:
            生成的教案文本
        """
        print(f"\n====================================")
        print(f"📝 教案生成开始")
        print(f"📝 用户需求: {user_input}")
        print(f"📚 向量数据库理论资源: {len(theory_resources)}条")
        print(f"📄 向量数据库教案示例: {len(lesson_plan_patterns)}条")
        print(f"📚 本地优秀教案共性文件: {'已加载' if self.lesson_plan_common_characteristics else '未找到'}")
        print(f"📚 本地理论卡片文件: {'已加载' if self.theory_cards else '未找到'}")
        
        try:
            # 分析用户输入中的教学方法
            teaching_method = self._analyze_teaching_method(user_input)
            print(f"🔍 分析教学方法: {teaching_method}")
            
            # 分析用户输入中的教学内容类型
            content_type = self._analyze_content_type(user_input)
            print(f"📝 分析教学内容类型: {content_type}")
            
            # 准备输入数据 - 优先使用本地文件，向量数据库资源作为补充
            theory_text = self._format_theory_resources(theory_resources)
            patterns_text = self._format_lesson_plan_patterns(lesson_plan_patterns)
            
            # 获取模型
            model = self.model_config.get_model("lesson_plan")
            
            # 构建链
            chain = self.prompt_template | model | StrOutputParser()
            
            # 调用模型生成教案
            lesson_plan = chain.invoke({
                "user_input": user_input,
                "theory_resources": theory_text,
                "lesson_plan_patterns": patterns_text,
                "lesson_plan_common_characteristics": self.lesson_plan_common_characteristics,
                "theory_cards": self.theory_cards
            })
            
            print(f"✅ 教案生成成功，长度: {len(lesson_plan)}字符")
            
            # 验证理论引用（考虑教学方法和内容类型）
            validated_lesson_plan = self._validate_theory_references(lesson_plan, teaching_method, content_type)
            
            # 理论引用质量三维评估
            quality_evaluated_plan = self._evaluate_theory_quality(validated_lesson_plan, teaching_method, content_type)
            
            # 检查理论多样性
            diverse_plan = self._check_theory_diversity(quality_evaluated_plan)
            
            # 检查理论引用的一致性
            consistent_plan = self._check_theory_consistency(diverse_plan, teaching_method, content_type)
            
            # 转换所有理论依据为新的边框格式
            formatted_plan = self._format_all_theory_references(consistent_plan)
            
            # 检查教案环节完整性
            complete_plan = self._check_lesson_plan_completeness(formatted_plan)
            
            return complete_plan
            
        except Exception as e:
            print(f"❌ 教案生成失败: {str(e)}")
            return self._get_error_response(str(e))
