"""
统一教案生成系统

核心理念：
- 不区分"协编"和"生成"模式
- 根据用户输入的完整程度智能决定处理方式
- 信息完整 → 直接生成完整教案
- 信息不完整 → 引导用户补充关键信息
- 支持多轮对话迭代优化
- 最终统一导出

职责：
- 智能分析用户输入的完整性
- 动态引导用户补充关键信息
- 整合理论资源和优秀案例
- 生成高质量教案
- 支持多格式导出

依赖：
- lesson_plan_generator (教案生成核心)
- lesson_plan_exporter (教案导出)
- resource_retriever (资源检索)
- model_config (模型配置)
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from .lesson_plan_generator import LessonPlanGenerator
from .lesson_plan_exporter import (
    export_lesson_plan_markdown,
    export_lesson_plan_html,
    export_lesson_plan_docx,
    export_lesson_plan_all
)
from .resource_retriever import ResourceRetriever
from .model_config import model_config


class LessonPlanInfoCompletion(Enum):
    """教案信息完整度"""
    COMPLETE = "complete"  # 信息完整，可以直接生成
    PARTIAL = "partial"    # 信息部分完整，需要引导补充
    MINIMAL = "minimal"    # 信息很少，需要逐步引导


class RequiredInfo(BaseModel):
    """教案所需关键信息"""
    topic: str = Field(description="课题名称")
    teaching_goals: Optional[str] = Field(description="教学目标", default=None)
    teaching_methods: Optional[str] = Field(description="教学方法", default=None)
    student_level: Optional[str] = Field(description="学生水平", default=None)
    class_hours: Optional[str] = Field(description="课时", default=None)
    key_points: Optional[str] = Field(description="教学重点", default=None)
    difficulties: Optional[str] = Field(description="教学难点", default=None)


class UnifiedLessonPlanSystem:
    """统一教案生成系统"""
    
    def __init__(self):
        """初始化统一教案系统"""
        self.lesson_plan_generator = LessonPlanGenerator()
        self.resource_retriever = ResourceRetriever()
        self.model_config = model_config
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def process_lesson_plan_request(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理教案生成请求 - 统一入口
        
        Args:
            user_input: 用户输入（可以是课题，也可以是完整需求）
            session_id: 会话ID（用于多轮对话）
        
        Returns:
            处理结果
        """
        # 检查是否包含内容生成指令词，如果有，优先处理教案生成
        content_generation_keywords = ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
        has_content_generation = any(keyword in user_input for keyword in content_generation_keywords)
        
        # 检查是否包含资源获取指令词（排除"帮我"等礼貌用语）
        resource_retrieval_keywords = ["推送", "找", "推荐", "有没有", "帮我找", "我要找", "想要", "需要"]
        has_resource_retrieval = any(keyword in user_input for keyword in resource_retrieval_keywords)
        
        # 优先级：内容生成 > 资源获取
        if has_resource_retrieval and not has_content_generation:
            print(f"⚠️ 检测到资源获取指令词，拒绝生成教案")
            return {
                "status": "error",
                "message": "您使用了资源获取指令词（如'推送'、'找'、'推荐'等），系统将为您检索相关资源，而不是生成新的教案。",
                "session_id": session_id
            }
        
        # 1. 获取或创建会话
        if not session_id:
            session_id = f"lp_{uuid.uuid4().hex[:8]}"
            self.sessions[session_id] = {
                "collected_info": {},
                "lesson_plan": None,
                "conversation_history": []
            }
            print(f"🆕 创建新会话: {session_id}")
        
        session = self.sessions[session_id]
        session["conversation_history"].append({"role": "user", "content": user_input})
        
        # 2. 分析用户输入，提取信息
        extracted_info = self._extract_lesson_plan_info(user_input)
        session["collected_info"].update(extracted_info)
        
        # 3. 判断信息完整度
        completion_level = self._assess_info_completion(session["collected_info"])
        
        print(f"📊 信息完整度: {completion_level.value}")
        print(f"📋 已收集信息: {list(session['collected_info'].keys())}")
        
        # 4. 根据完整度决定处理方式
        if completion_level == LessonPlanInfoCompletion.COMPLETE:
            return self._generate_complete_lesson_plan(session_id, session)
        else:
            return self._guide_for_more_info(session_id, session, completion_level)
    
    def _extract_lesson_plan_info(self, user_input: str) -> Dict[str, Any]:
        """
        从用户输入中提取教案关键信息 - 高容错智能提取
        
        支持各种输入方式：
        - 明确的关键词输入
        - 自然语言描述（无需特定关键词
        - 口语化表达
        - 混合方式
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            提取的信息字典
        """
        prompt = ChatPromptTemplate.from_template("""
你是一位专业的教案信息提取专家，擅长从各种形式的用户输入中提取教案生成所需的关键信息。

## 任务说明：
用户可能以任何形式表达需求，包括但不限于：
- 明确关键词、自然语言描述、口语化表达、混合方式等。
请灵活理解用户意图，不要局限于特定关键词。

用户输入：
{user_input}

## 提取目标
请从用户输入中智能提取以下信息（如果有相关信息存在）：

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
1. **灵活理解**：不一定要有明确的关键词，根据语义判断
2. **智能推断**：如果用户没有明确说，根据整体内容推断
3. **容错处理**：即使输入不规范，也要尽量提取
4. **至少提取topic**：topic是必须的，即使只有topic也可以
5. **JSON格式**：只输出JSON，不要其他解释

请以JSON格式输出，只包含提取到的信息，没有的字段可以省略。
示例：
{{
    "topic": "函数的单调性",
    "student_level": "高一",
    "teaching_goals": "理解函数单调性的概念，掌握判断方法"
}}
""")
        
        model = self.model_config.get_model("info_extraction")
        chain = prompt | model | StrOutputParser()
        
        try:
            result = chain.invoke({"user_input": user_input})
            print(f"📤 模型提取结果（原始）: {result[:200]}...")
            import json
            extracted = json.loads(result)
            
            # 容错：确保至少有topic
            if "topic" not in extracted or not extracted["topic"]:
                extracted["topic"] = user_input
            
            print(f"✅ 信息提取成功: {list(extracted.keys())}")
            return extracted
            
        except Exception as e:
            print(f"⚠️ 信息提取失败: {e}")
            # 多重容错机制
            print(f"🔄 使用备用提取方案")
            
            # 备用方案1: 简单关键词匹配
            backup_info = self._backup_extract_info(user_input)
            print(f"🔄 备用提取结果: {list(backup_info.keys())}")
            return backup_info
    
    def _backup_extract_info(self, user_input: str) -> Dict[str, Any]:
        """
        备用信息提取方法 - 基于关键词的简单提取
        
        当大模型提取失败时使用
        
        Args:
            user_input: 用户输入
        
        Returns:
            提取的信息
        """
        extracted = {"topic": user_input}
        
        # 简单关键词匹配
        import re
        
        # 年级/学生水平
        grade_patterns = [
            (r'高[一二三四]', '高一'),
            (r'初[一二三]', '高一'),
            (r'高(\d+)', lambda m: f'高{m.group(1)}'),
            (r'初(\d+)', lambda m: f'初{m.group(1)}'),
        ]
        
        for pattern, replacement in grade_patterns:
            match = re.search(pattern, user_input)
            if match:
                if callable(replacement):
                    extracted["student_level"] = replacement(match)
                else:
                    extracted["student_level"] = replacement
                break
        
        # 课时
        hour_patterns = [
            (r'(\d+)\s*课时?', lambda m: f'{m.group(1)}课时'),
            (r'(\d+)\s*小时?', lambda m: f'{m.group(1)}小时'),
        ]
        
        for pattern, replacement in hour_patterns:
            match = re.search(pattern, user_input)
            if match:
                if callable(replacement):
                    extracted["class_hours"] = replacement(match)
                else:
                    extracted["class_hours"] = replacement
                break
        
        # 教学方法关键词
        method_keywords = ['探究式', '讲授式', '合作学习', '问题解决', '启发式', '讨论式', '演示法', '练习法']
        found_methods = [kw for kw in method_keywords if kw in user_input]
        if found_methods:
            extracted["teaching_methods"] = '、'.join(found_methods)
        
        return extracted
    
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
    
    def _guide_for_more_info(
        self,
        session_id: str,
        session: Dict[str, Any],
        completion_level: LessonPlanInfoCompletion
    ) -> Dict[str, Any]:
        """
        引导用户补充信息
        
        Args:
            session_id: 会话ID
            session: 会话状态
            completion_level: 信息完整度
        
        Returns:
            引导响应
        """
        collected_info = session["collected_info"]
        topic = collected_info.get("topic", "这个课题")
        
        if completion_level == LessonPlanInfoCompletion.MINIMAL:
            response = f"""好的！让我们一起为「{topic}」设计一份优秀的教案。📝

为了给您生成最贴合需求的教案，我需要了解一些关键信息：

1. **教学目标**：这节课您希望学生达到什么目标？（知识、能力、情感等）
2. **教学方法**：您倾向于用什么教学方法？（探究式、讲授式、问题解决等）
3. **学生情况**：授课对象是哪个年级？学生基础如何？
4. **课时安排**：这节课计划用多少课时？

您可以一次性告诉我这些信息，也可以先回答其中一部分，我们逐步完善！"""
        
        else:  # PARTIAL
            missing_items = []
            if "teaching_goals" not in collected_info:
                missing_items.append("教学目标")
            if "teaching_methods" not in collected_info:
                missing_items.append("教学方法")
            if "student_level" not in collected_info:
                missing_items.append("学生水平/年级")
            
            response = f"""很好！我已经了解到一些关于「{topic}」的信息了。👍

为了生成更完善的教案，我还需要了解：
{chr(10).join([f"- {item}" for item in missing_items])}

请告诉我这些信息，或者如果您觉得信息已经足够了，也可以直接说"直接生成"，我会基于现有信息为您生成教案！"""
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "guiding",
            "response": response,
            "collected_info": collected_info,
            "conversation_history": session["conversation_history"]
        }
    
    def _generate_complete_lesson_plan(
        self,
        session_id: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成完整教案
        
        Args:
            session_id: 会话ID
            session: 会话状态
        
        Returns:
            生成结果
        """
        collected_info = session["collected_info"]
        topic = collected_info.get("topic", "")
        
        print(f"🚀 开始生成完整教案: {topic}")
        
        # 1. 构建增强的用户输入
        enhanced_input = self._build_enhanced_input(collected_info)
        
        # 2. 检索相关资源
        retrieved_resources = self.resource_retriever.retrieve(
            enhanced_input,
            intent="generate_lesson_plan"
        )
        
        theory_resources = retrieved_resources.get("theory_resources", [])
        lesson_plan_patterns = retrieved_resources.get("lesson_plan_patterns", [])
        
        print(f"📚 理论资源: {len(theory_resources)}条")
        print(f"📄 教案示例: {len(lesson_plan_patterns)}条")
        
        # 3. 生成教案
        lesson_plan_content = self.lesson_plan_generator.generate(
            enhanced_input,
            theory_resources,
            lesson_plan_patterns
        )
        
        session["lesson_plan"] = lesson_plan_content
        
        # 4. 构建响应
        response = f"""🎉 太棒了！教案已经生成完成！

**课题：** {topic}

**教案摘要：**
{lesson_plan_content[:600]}...

---

**您可以：**
1. 📖 查看完整教案
2. ✏️ 提出修改意见，我可以帮您调整
3. 📥 导出教案（支持 Markdown、HTML、Word 格式）
4. 🔄 基于这个教案继续优化

请告诉我您的想法！"""
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "completed",
            "response": response,
            "lesson_plan": lesson_plan_content,
            "collected_info": collected_info,
            "conversation_history": session["conversation_history"],
            "export_available": True
        }
    
    def _build_enhanced_input(self, collected_info: Dict[str, Any]) -> str:
        """
        构建增强的用户输入
        
        Args:
            collected_info: 收集的信息
        
        Returns:
            增强的输入文本
        """
        parts = []
        if "topic" in collected_info:
            parts.append(f"课题：{collected_info['topic']}")
        if "teaching_goals" in collected_info:
            parts.append(f"教学目标：{collected_info['teaching_goals']}")
        if "teaching_methods" in collected_info:
            parts.append(f"教学方法：{collected_info['teaching_methods']}")
        if "student_level" in collected_info:
            parts.append(f"学生水平：{collected_info['student_level']}")
        if "class_hours" in collected_info:
            parts.append(f"课时：{collected_info['class_hours']}")
        if "key_points" in collected_info:
            parts.append(f"教学重点：{collected_info['key_points']}")
        if "difficulties" in collected_info:
            parts.append(f"教学难点：{collected_info['difficulties']}")
        
        return "\n".join(parts)
    
    def revise_lesson_plan(
        self,
        session_id: str,
        revision_request: str
    ) -> Dict[str, Any]:
        """
        修改教案
        
        Args:
            session_id: 会话ID
            revision_request: 修改意见
        
        Returns:
            修改结果
        """
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "会话不存在"
            }
        
        session = self.sessions[session_id]
        if not session.get("lesson_plan"):
            return {
                "success": False,
                "error": "还没有生成教案，请先生成教案"
            }
        
        session["conversation_history"].append({"role": "user", "content": revision_request})
        
        # 使用修改提示词
        prompt = ChatPromptTemplate.from_template("""
你是一位教案修改专家。请根据用户的修改意见，对教案进行修订。

## 原始教案
{original_lesson_plan}

## 修改意见
{revision_request}

请根据修改意见，对教案进行相应的调整。保持教案的整体结构不变，但要针对性地修改相关部分。

请输出完整的修订后教案。
""")
        
        model = self.model_config.get_model("lesson_plan")
        chain = prompt | model | StrOutputParser()
        
        revised_lesson_plan = chain.invoke({
            "original_lesson_plan": session["lesson_plan"],
            "revision_request": revision_request
        })
        
        session["lesson_plan"] = revised_lesson_plan
        
        response = f"""好的，我已经根据您的意见对教案进行了修订！📝

**修订后的教案摘要：**
{revised_lesson_plan[:600]}...

---

**您可以：**
1. 继续提出修改意见
2. 导出教案
3. 确认教案完成

请告诉我您的想法！"""
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "completed",
            "response": response,
            "lesson_plan": revised_lesson_plan,
            "conversation_history": session["conversation_history"],
            "export_available": True
        }
    
    def export_lesson_plan(
        self,
        session_id: str,
        export_format: str = "markdown",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导出教案
        
        Args:
            session_id: 会话ID
            export_format: 导出格式
            filename: 文件名
        
        Returns:
            导出结果
        """
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "会话不存在"
            }
        
        session = self.sessions[session_id]
        if not session.get("lesson_plan"):
            return {
                "success": False,
                "error": "还没有生成教案，请先生成教案"
            }
        
        lesson_plan_content = session["lesson_plan"]
        collected_info = session.get("collected_info", {})
        
        metadata = {
            "topic": collected_info.get("topic", "教案"),
            "student_level": collected_info.get("student_level", ""),
            "class_hours": collected_info.get("class_hours", "")
        }
        
        try:
            if export_format == "markdown":
                filepath = export_lesson_plan_markdown(
                    lesson_plan_content, filename, metadata
                )
                result = {"markdown": filepath}
            elif export_format == "html":
                filepath = export_lesson_plan_html(
                    lesson_plan_content, filename, metadata
                )
                result = {"html": filepath}
            elif export_format == "docx":
                filepath = export_lesson_plan_docx(
                    lesson_plan_content, filename, metadata
                )
                result = {"docx": filepath}
            elif export_format == "all":
                result = export_lesson_plan_all(
                    lesson_plan_content, filename, metadata
                )
            else:
                return {
                    "success": False,
                    "error": f"不支持的导出格式: {export_format}"
                }
            
            return {
                "success": True,
                "files": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id]


# 全局实例
unified_lesson_plan_system = UnifiedLessonPlanSystem()


# 便捷函数接口
def generate_lesson_plan(
    user_input: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成教案 - 统一入口
    
    智能判断用户输入的完整程度：
    - 信息完整 → 直接生成完整教案
    - 信息不完整 → 引导用户补充关键信息
    """
    return unified_lesson_plan_system.process_lesson_plan_request(user_input, session_id)


def revise_lesson_plan(session_id: str, revision_request: str) -> Dict[str, Any]:
    """修改教案"""
    return unified_lesson_plan_system.revise_lesson_plan(session_id, revision_request)


def export_lesson_plan(
    session_id: str,
    export_format: str = "markdown",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """导出教案"""
    return unified_lesson_plan_system.export_lesson_plan(session_id, export_format, filename)
