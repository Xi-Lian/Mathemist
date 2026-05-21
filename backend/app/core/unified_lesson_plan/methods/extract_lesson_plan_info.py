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

## 重要判断：是全新需求还是修改需求？

**首先判断用户意图：**
- **全新需求**：用户提出了一个全新的课题（如“概率统计”、“三角函数”等），与之前的课题完全不同
  - 特征：出现了新的课题名称、新的教学主题
  - 处理：**清空已有信息**，只提取最新输入中的信息
  
- **修改需求**：用户在之前生成的教案基础上提出修改意见（如“把第一课时改一下”、“增加一个例题”）
  - 特征：没有新的课题名称，只是对现有教案的调整
  - 处理：**保留已有信息**，增量提取修改内容

**判断示例：**
- “帮我生成一个概率统计的教案” → 全新需求（清空已有信息）
- “下周有个示范课，主题是概率统计” → 全新需求（清空已有信息）
- “把刚才的教案改一下” → 修改需求（保留已有信息）
- “增加一个例题” → 修改需求（保留已有信息）

## 已有信息（仅在修改需求时使用）
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

8. **usage_scenario（使用场景/教案用途）** ⭐新增
   - 这个教案是用来做什么的？
   - 可能的值：
     - "daily_teaching"（日常教学）：实用、简洁、可操作
     - "public_class"（公开课/示范课）：规范、完整、有亮点
     - "speech_competition"（说课比赛）：理论深度强、逻辑严密
     - "evaluation_class"（评优课/优质课）：高标准、全面、创新性
     - "teacher_training"（新教师培训）：详细、具体、可操作性强
   - 如果用户没有明确说明，可以根据上下文推断，或默认为"daily_teaching"
   - 识别关键词：
     - "比赛"、"说课"、"评比" → speech_competition 或 evaluation_class
     - "公开课"、"示范课"、"展示" → public_class
     - "培训"、"新手"、"新教师" → teacher_training
     - "上课"、"教学"、"备课" → daily_teaching

## 重要提醒：
1. **全新需求 vs 修改需求**：
   - 如果是**全新需求**（用户提出了新课题）：**必须忽略对话历史中的旧课题**，只从最新用户输入中提取信息
   - 如果是**修改需求**（用户在现有教案上修改）：**保留已有信息**，只输出需要修改的字段
2. **全新需求的判断标准**：
   - 用户输入中出现了明确的课题名称（如“概率统计”、“三角函数”等）
   - 这个课题与对话历史中的课题不同
   - 例如：历史中是“函数单调性”，用户说“概率统计” → 全新需求
3. **自然语言理解**：理解自然的口语表达，不要求严格的格式
4. **智能推断**：根据整体上下文推断用户的意图和提供的信息
5. **容错处理**：即使输入不规范，也要尽量提取有价值的信息
6. **至少提取topic**：如果还没有topic，即使只有topic也可以
7. **JSON格式**：只输出JSON，不要其他解释

请以JSON格式输出，只包含从最新用户输入中提取到的新信息，没有的字段可以省略。

**示例1 - 全新需求：**
用户输入：“帮我生成一个概率统计的教案，高二学生”
输出：
{{
    "topic": "概率统计",
    "student_level": "高二",
    "usage_scenario": "daily_teaching"
}}

**示例2 - 修改需求：**
用户输入：“把第一课时的例题改一下”
输出：
{{
    "modification_request": "修改第一课时的例题"
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
            
            # V48.3修复：判断是否为全新需求
            # 如果提取到了新的topic，且与已有信息的topic不同，说明是全新需求
            if "topic" in extracted and extracted["topic"]:
                existing_topic = existing_info.get("topic", "")
                new_topic = extracted["topic"]
                
                if existing_topic and existing_topic != new_topic:
                    print(f"🔄 V48.3检测到全新需求：'{existing_topic}' → '{new_topic}'，清空已有信息")
                    # 清空已有信息，只保留新提取的信息
                    session["collected_info"] = {}
                    existing_info = {}
                    # V48.5增强：确保extracted中只有新提取的字段，移除可能的旧字段
                    # 只保留从最新用户输入中提取的字段
                    cleaned_extracted = {}
                    for key, value in extracted.items():
                        # 如果是topic或其他核心字段，保留
                        if key in ["topic", "student_level", "class_hours", "teaching_methods", 
                                   "teaching_goals", "key_points", "difficulties", "usage_scenario"]:
                            cleaned_extracted[key] = value
                    extracted = cleaned_extracted
                    print(f"✅ 清理后的提取结果: {list(extracted.keys())}")
            
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
