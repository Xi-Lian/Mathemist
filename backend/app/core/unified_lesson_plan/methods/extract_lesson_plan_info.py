from .._shared import *


class _ExtractLessonPlanInfoMixin:
    def _extract_lesson_plan_info(self, user_input: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        从用户输入中提取教案关键信息 - 基于对话历史的增量提取
        
        支持各种输入方式：
        - 明确的关键词输入
        - 自然语言描述（无需特定关键词）
        - 口语化表达
        - 混合方式
        
        Args:
            user_input: 用户输入文本
            session: 会话状态
        
        Returns:
            提取的信息字典
        """
        # 获取已有信息
        existing_info = session.get("collected_info", {})
        
        # 构建对话历史上下文
        conversation_history = session.get("conversation_history", [])
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        
        prompt = ChatPromptTemplate.from_template("""
你是一位专业的教案信息提取专家，擅长从各种形式的用户输入中提取教案生成所需的关键信息。

## 已有信息
{existing_info}

## 对话历史
{history_text}

## 最新用户输入
{user_input}

## 任务说明：
用户可能以任何形式表达需求，包括但不限于：
- 明确关键词、自然语言描述、口语化表达、混合方式等。
请灵活理解用户意图，不要局限于特定关键词。

## 提取目标
请从用户最新输入中智能提取以下信息（如果有相关信息存在）：

1. **topic（课题/主题/授课内容**
   - 可以是明确的课题名称，也可以是用户想要教的内容/想设计的内容

2. **teaching_goals（教学目标/教学目的/学习目标）
   - 用户希望学生达到什么目标
   - 希望学生学会什么/掌握什么/理解什么

3. **teaching_methods（教学方法/教学策略/教学方式）
   - 用什么方法教
   - 倾向于什么教学方式

4. **student_level（学生水平/年级/授课对象/学生情况）
   - 哪个年级的学生
   - 学生基础如何

5. **class_hours（课时/时间安排）
   - 用多少课时/多长时间

6. **key_points（教学重点/关键内容/核心知识点）
   - 重点讲什么
   - 关键内容是什么

7. **difficulties（教学难点/学生可能遇到的困难）
   - 学生可能难以理解的地方
   - 难点是什么

## 重要提醒：
1. **增量提取**：只提取用户最新输入中提供的新信息，不要重复提取已有信息
2. **自然语言理解**：理解自然的口语表达，不要求严格的格式
3. **智能推断**：根据整体上下文推断用户的意图和提供的信息
4. **容错处理**：即使输入不规范，也要尽量提取有价值的信息
5. **至少提取topic**：如果还没有topic，即使只有topic也可以
6. **JSON格式**：只输出JSON，不要其他解释

请以JSON格式输出，只包含从最新用户输入中提取到的新信息，没有的字段可以省略。
示例：
{{
    "teaching_goals": "理解函数单调性的概念，掌握判断方法",
    "teaching_methods": "探究式教学"
}}
""")
        
        model = self.model_config.get_model("info_extraction")
        chain = prompt | model | StrOutputParser()
        
        try:
            result = chain.invoke({
                "user_input": user_input,
                "existing_info": str(existing_info),
                "history_text": history_text
            })
            print(f"📤 模型提取结果（原始）: {result[:200]}...")
            import json
            extracted = json.loads(result)
            
            # 容错：确保至少有topic（如果还没有）
            if "topic" not in existing_info and ("topic" not in extracted or not extracted["topic"]):
                extracted["topic"] = user_input
            
            print(f"✅ 信息提取成功: {list(extracted.keys())}")
            return extracted
            
        except Exception as e:
            print(f"⚠️ 信息提取失败: {e}")
            # 多重容错机制
            print(f"🔄 使用备用提取方案")
            
            # 备用方案1: 简单关键词匹配
            backup_info = self._backup_extract_info(user_input, existing_info)
            print(f"🔄 备用提取结果: {list(backup_info.keys())}")
            return backup_info
