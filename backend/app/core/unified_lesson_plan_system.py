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

import os
import json
import time
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
from .config_manager import config_manager


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
        self.latest_lesson_plan = None  # 存储最新生成的教案
        self.latest_topic = None  # 存储最新生成的教案的课题
        self.lesson_plan_file = os.path.join(os.path.dirname(__file__), "..", "..", "latest_lesson_plan.json")
        self.session_timeout = config_manager.get_session_timeout()  # 从配置获取会话超时时间
        
        # 加载最新教案
        self._load_latest_lesson_plan()
        # 清理过期会话
        self._clean_expired_sessions()
    
    def _load_latest_lesson_plan(self):
        """
        从文件中加载最新的教案
        """
        if os.path.exists(self.lesson_plan_file):
            try:
                with open(self.lesson_plan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.latest_lesson_plan = data.get('lesson_plan')
                    self.latest_topic = data.get('topic')
                print(f"✅ 从文件加载最新教案: {self.latest_topic}")
            except Exception as e:
                print(f"⚠️ 加载最新教案失败: {e}")
        else:
            print("ℹ️ 最新教案文件不存在")
    
    def _save_latest_lesson_plan(self):
        """
        将最新的教案保存到文件中
        """
        if self.latest_lesson_plan:
            try:
                data = {
                    'lesson_plan': self.latest_lesson_plan,
                    'topic': self.latest_topic,
                    'timestamp': str(uuid.uuid4())  # 用于标识版本
                }
                # 确保目录存在
                os.makedirs(os.path.dirname(self.lesson_plan_file), exist_ok=True)
                with open(self.lesson_plan_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 最新教案已保存到文件: {self.latest_topic}")
            except Exception as e:
                print(f"⚠️ 保存最新教案失败: {e}")
    
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
        # 检查用户是否要求"查看完整教案"
        normalized_input = user_input.replace(' ', '')  # 移除所有空格
        if "查看完整教案" in normalized_input or "完整教案" in normalized_input:
            print("👁️ 用户要求查看完整教案")
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if session.get("lesson_plan"):
                    lesson_plan = session["lesson_plan"]
                    topic = session.get("collected_info", {}).get("topic", "指数函数")
                    
                    # 生成导出数据（默认为 Markdown 格式）
                    export_result = self.export_lesson_plan(session_id, "markdown")
                    
                    response = f"""📖 完整教案如下：

# {lesson_plan}

---

**您可以：**
1. ✏️ 提出修改意见，我可以帮您调整
2. 🔄 基于这个教案继续优化

请告诉我您的想法！"""
                    
                    session["conversation_history"].append({"role": "assistant", "content": response})
                    
                    result = {
                        "success": True,
                        "session_id": session_id,
                        "status": "completed",
                        "response": response,
                        "lesson_plan": lesson_plan,
                        "collected_info": session.get("collected_info", {}),
                        "conversation_history": session["conversation_history"]
                    }
                    
                    # 如果导出成功，添加导出数据
                    if export_result.get("success"):
                        result["export_data"] = {
                            "content": export_result.get("content", ""),
                            "filename": export_result.get("filename", "lesson_plan.md"),
                            "format": export_result.get("format", "markdown")
                        }
                    
                    return result
                else:
                    response = "抱歉，还没有生成教案，请先生成教案后再查看完整内容。"
                    session["conversation_history"].append({"role": "assistant", "content": response})
                    return {
                        "success": False,
                        "session_id": session_id,
                        "status": "error",
                        "response": response
                    }
            else:
                # 没有会话ID或会话不存在，提示用户提供会话ID
                response = """⚠️ 无法查看完整教案

您需要提供会话ID才能查看完整教案。

**如何获取会话ID：**
- 查看您生成教案时的响应，其中包含了会话ID
- 会话ID格式类似：`lp_xxxxxxxx`（以lp_开头，后面跟着8位字符）

**请提供会话ID，然后再次说"查看完整教案"。"""
                
                if session_id and session_id in self.sessions:
                    self.sessions[session_id]["conversation_history"].append({"role": "assistant", "content": response})
                return {
                    "success": False,
                    "session_id": session_id,
                    "status": "error",
                    "response": response
                }
        
        # 检查用户是否要求"导出教案"
        if "导出教案" in user_input:
            print("💾 用户要求导出教案")
            
            # 智能格式推断
            export_format = "markdown"  # 默认格式
            if "word" in user_input.lower() or "docx" in user_input.lower():
                export_format = "docx"
            elif "html" in user_input.lower():
                export_format = "html"
            elif "全部" in user_input or "所有" in user_input:
                export_format = "all"
            
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if session.get("lesson_plan"):
                    # 检查是否需要格式选择引导
                    if "格式" in user_input or "导出为" in user_input:
                        # 提供格式选择引导
                        response = f"""📥 请选择您需要的导出格式：

1. 📄 Markdown格式 - 适合在编辑器中查看和编辑
2. 🌐 HTML格式 - 适合在浏览器中查看
3. 📝 Word格式 - 适合正式文档和打印
4. 📦 全部格式 - 同时导出所有格式

请回复对应的数字或格式名称，例如："1" 或 "Word"。"""
                        session["conversation_history"].append({"role": "assistant", "content": response})
                        return {
                            "success": True,
                            "session_id": session_id,
                            "status": "format_selection",
                            "response": response
                        }
                    else:
                        # 直接导出
                        export_result = self.export_lesson_plan(session_id, export_format)
                        if export_result.get("success"):
                            content = export_result.get("content", "")
                            filename = export_result.get("filename", "lesson_plan.md")
                            format_type = export_result.get("format", "markdown")
                            
                            response = f"""📥 教案导出成功！

**导出格式：** {format_type.upper()}
**文件名：** {filename}

文件已准备好，您可以点击下载按钮保存到本地。

**您还可以：**
1. 继续修改教案
2. 导出为其他格式
3. 确认教案完成

请告诉我您的想法！"""
                            
                            session["conversation_history"].append({"role": "assistant", "content": response})
                            return {
                                "success": True,
                                "session_id": session_id,
                                "status": "completed",
                                "response": response,
                                "export_data": {
                                    "content": content,
                                    "filename": filename,
                                    "format": format_type
                                }
                            }
                        else:
                            response = f"导出失败：{export_result.get('error', '未知错误')}"
                            session["conversation_history"].append({"role": "assistant", "content": response})
                            return {
                                "success": False,
                                "session_id": session_id,
                                "status": "error",
                                "response": response
                            }
                else:
                    response = "抱歉，还没有生成教案，请先生成教案后再导出。"
                    session["conversation_history"].append({"role": "assistant", "content": response})
                    return {
                        "success": False,
                        "session_id": session_id,
                        "status": "error",
                        "response": response
                    }
            else:
                # 尝试从最新教案恢复
                if self.latest_lesson_plan:
                    session_id = f"lp_{uuid.uuid4().hex[:8]}"
                    self.sessions[session_id] = {
                        "collected_info": {"topic": self.latest_topic or "教案"},
                        "lesson_plan": self.latest_lesson_plan,
                        "conversation_history": [],
                        "last_activity": str(time.time())
                    }
                    print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
                    
                    # 检查是否需要格式选择引导
                    if "格式" in user_input or "导出为" in user_input:
                        # 提供格式选择引导
                        response = f"""📥 请选择您需要的导出格式：

1. 📄 Markdown格式 - 适合在编辑器中查看和编辑
2. 🌐 HTML格式 - 适合在浏览器中查看
3. 📝 Word格式 - 适合正式文档和打印
4. 📦 全部格式 - 同时导出所有格式

请回复对应的数字或格式名称，例如："1" 或 "Word"。"""
                        self.sessions[session_id]["conversation_history"].append({"role": "assistant", "content": response})
                        return {
                            "success": True,
                            "session_id": session_id,
                            "status": "format_selection",
                            "response": response
                        }
                    else:
                        # 直接导出
                        export_result = self.export_lesson_plan(session_id, export_format)
                        if export_result.get("success"):
                            files = export_result.get("files", {})
                            file_list = []
                            for fmt, path in files.items():
                                file_list.append(f"{fmt.upper()}: {path}")
                            file_list_str = "\n".join(file_list)
                            
                            response = f"""📥 教案导出成功！

**导出文件：**
{file_list_str}

您可以查看或下载这些文件。

**您还可以：**
1. 继续修改教案
2. 导出为其他格式
3. 确认教案完成

请告诉我您的想法！"""
                            
                            self.sessions[session_id]["conversation_history"].append({"role": "assistant", "content": response})
                            return {
                                "success": True,
                                "session_id": session_id,
                                "status": "completed",
                                "response": response,
                                "files": files
                            }
                        else:
                            response = f"导出失败：{export_result.get('error', '未知错误')}"
                            self.sessions[session_id]["conversation_history"].append({"role": "assistant", "content": response})
                            return {
                                "success": False,
                                "session_id": session_id,
                                "status": "error",
                                "response": response
                            }
                else:
                    response = "抱歉，未找到相关教案，请先生成教案。"
                    return {
                        "success": False,
                        "status": "error",
                        "response": response
                    }
        
        # 检查是否是格式选择回复
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            # 检查上一轮对话是否是格式选择请求
            if session.get("conversation_history"):
                last_message = session["conversation_history"][-1]
                if last_message.get("role") == "assistant" and "请选择您需要的导出格式" in last_message.get("content", ""):
                    # 解析用户选择的格式
                    user_choice = user_input.strip().lower()
                    export_format = "markdown"  # 默认格式
                    
                    if user_choice in ["1", "markdown", "md"]:
                        export_format = "markdown"
                    elif user_choice in ["2", "html"]:
                        export_format = "html"
                    elif user_choice in ["3", "word", "docx"]:
                        export_format = "docx"
                    elif user_choice in ["4", "全部", "所有", "all"]:
                        export_format = "all"
                    
                    # 执行导出
                    export_result = self.export_lesson_plan(session_id, export_format)
                    if export_result.get("success"):
                        files = export_result.get("files", {})
                        file_list = []
                        for fmt, path in files.items():
                            file_list.append(f"{fmt.upper()}: {path}")
                        file_list_str = "\n".join(file_list)
                        
                        response = f"""📥 教案导出成功！

**导出文件：**
{file_list_str}

您可以查看或下载这些文件。

**您还可以：**
1. 继续修改教案
2. 导出为其他格式
3. 确认教案完成

请告诉我您的想法！"""
                        
                        session["conversation_history"].append({"role": "assistant", "content": response})
                        return {
                            "success": True,
                            "session_id": session_id,
                            "status": "completed",
                            "response": response,
                            "files": files
                        }
                    else:
                        response = f"导出失败：{export_result.get('error', '未知错误')}"
                        session["conversation_history"].append({"role": "assistant", "content": response})
                        return {
                            "success": False,
                            "session_id": session_id,
                            "status": "error",
                            "response": response
                        }
        
        # 1. 首先检查是否是修改意见（在会话创建之前）
        # 修改意见特征：包含各种修改相关的词汇
        revision_keywords = [
            # 表达不满意或需要修改
            "觉得", "感觉", "认为", "希望", "想要", "需要", "应该", "建议", "提议",
            # 具体修改动作
            "修改", "调整", "改进", "完善", "优化", "补充", "增加", "添加", "减少", "删除", "删除掉",
            # 疑问式修改请求
            "能不能", "能否", "可不可以", "是否可以", "能不能够",
            # 具体修改内容
            "太短", "太长", "太简单", "太复杂", "不够", "不足", "缺少", "缺乏",
            # 其他修改相关词汇
            "改一下", "改改", "调整一下", "完善一下", "优化一下", "补充一下"
        ]
        has_revision_request = any(keyword in user_input for keyword in revision_keywords)
        
        # 如果检测到修改意见，需要确保有有效的会话
        if has_revision_request:
            print(f"✏️ 检测到修改意见")
            
            # 如果没有session_id或session_id不存在，尝试从最新教案恢复
            if not session_id or session_id not in self.sessions:
                if self.latest_lesson_plan:
                    session_id = f"lp_{uuid.uuid4().hex[:8]}"
                    self.sessions[session_id] = {
                        "collected_info": {"topic": self.latest_topic or "教案"},
                        "lesson_plan": self.latest_lesson_plan,
                        "conversation_history": [],
                        "last_activity": str(time.time()),
                        "progress": 100  # 已完成
                    }
                    print(f"🔄 检测到修改意见，从最新教案恢复会话: {session_id}")
                else:
                    print(f"❌ 检测到修改意见，但没有最新教案")
                    return {
                        "success": False,
                        "error": "对话已过期，请重新开始",
                        "session_id": session_id
                    }
            
            # 获取会话并检查是否有教案
            session = self.sessions[session_id]
            if session.get("lesson_plan"):
                print(f"✏️ 调用修改教案功能")
                # 调用修改教案方法
                return self.revise_lesson_plan(session_id, user_input)
            else:
                print(f"⚠️ 检测到修改意见，但会话中没有教案")
                # 继续正常流程，让用户生成新教案
        
        # 2. 获取或创建会话
        if not session_id:
            session_id = f"lp_{uuid.uuid4().hex[:8]}"
            self.sessions[session_id] = {
                "collected_info": {},
                "lesson_plan": None,
                "conversation_history": [],
                "last_activity": str(time.time()),  # 使用真实的时间戳
                "progress": 0  # 进度跟踪
            }
            print(f"🆕 创建新会话: {session_id}")
        elif session_id not in self.sessions:
            # 尝试从最新教案恢复
            if self.latest_lesson_plan:
                self.sessions[session_id] = {
                    "collected_info": {"topic": self.latest_topic or "教案"},
                    "lesson_plan": self.latest_lesson_plan,
                    "conversation_history": [],
                    "last_activity": str(time.time()),
                    "progress": 100  # 已完成
                }
                print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
            else:
                self.sessions[session_id] = {
                    "collected_info": {},
                    "lesson_plan": None,
                    "conversation_history": [],
                    "last_activity": str(time.time()),
                    "progress": 0  # 进度跟踪
                }
                print(f"🆕 会话不存在，创建新会话: {session_id}")
        
        session = self.sessions[session_id]
        
        # 3. 检查是否包含内容生成指令词，如果有，优先处理教案生成
        content_generation_keywords = ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
        has_content_generation = any(keyword in user_input for keyword in content_generation_keywords)
        
        # 4. 检查是否包含资源获取指令词
        resource_retrieval_keywords = ["推送", "找", "推荐", "有没有", "我要找", "想要", "需要"]
        # 注意：这里不再包含"帮我找"，因为"帮我"可能只是礼貌用语
        has_resource_retrieval = any(keyword in user_input for keyword in resource_retrieval_keywords)
        
        # 5. 智能判断：如果包含"帮我"但同时包含内容生成关键词，视为内容生成请求
        if "帮我" in user_input and has_content_generation:
            has_resource_retrieval = False
            print("🤖 智能识别：'帮我'为礼貌用语，视为内容生成请求")
        
        # 6. 上下文增强判断：分析对话历史，如果最近几轮在讨论教案，则降低资源请求的判定阈值
        conversation_history = session.get("conversation_history", [])
        # 分析最近3轮对话
        recent_history = conversation_history[-3:]
        has_lesson_plan_discussion = any(
            "教案" in msg.get("content", "") or "lesson_plan" in msg.get("content", "")
            for msg in recent_history
        )
        
        if has_lesson_plan_discussion and has_resource_retrieval:
            # 如果最近在讨论教案，且用户使用了资源请求词，可能是在询问与教案相关的资源建议
            has_resource_retrieval = False
            print("🤖 上下文增强：最近在讨论教案，视为教案相关的资源建议")
        
        # 7. 意图分类优化：区分"我要找资源"和"我需要建议"
        suggestion_keywords = ["觉得", "应该", "建议", "如何", "怎样", "是否"]
        has_suggestion = any(keyword in user_input for keyword in suggestion_keywords)
        
        if has_suggestion and has_resource_retrieval:
            # 如果用户在寻求建议，而不是明确要求资源，视为建议请求
            has_resource_retrieval = False
            print("🤖 意图分类：用户在寻求建议，而非明确的资源请求")
        
        # 8. 混合模式：允许用户在生成教案的同时请求资源建议
        if has_content_generation and has_resource_retrieval:
            # 视为混合请求，先生成教案，然后提供资源建议
            has_resource_retrieval = False
            print("🤖 混合模式：用户同时请求生成教案和资源建议")
        
        # 9. 优先级：内容生成 > 资源获取
        if has_resource_retrieval and not has_content_generation:
            print(f"⚠️ 检测到资源获取指令词，拒绝生成教案")
            return {
                "status": "error",
                "message": "您使用了资源获取指令词（如'推送'、'找'、'推荐'等），系统将为您检索相关资源，而不是生成新的教案。",
                "session_id": session_id
            }
        
        # 检查是否是首次交互
        is_first_interaction = len(session.get("conversation_history", [])) == 0
        
        # 主动引导机制：如果是首次交互，检查用户输入是否包含足够的信息
        if is_first_interaction:
            # 提取用户输入中的信息
            extracted_info = self._extract_lesson_plan_info(user_input, session)
            
            # 检查是否包含足够的信息（至少要有课题）
            if extracted_info.get("topic"):
                # 如果用户已经提供了足够的信息，直接处理，不显示欢迎消息
                print(f"📝 首次交互但用户已提供足够信息，直接处理")
                # 记录用户输入
                session["conversation_history"].append({"role": "user", "content": user_input})
                # 更新会话最后活动时间
                session["last_activity"] = str(time.time())
                # 继续正常流程
            else:
                # 如果用户没有提供足够的信息，显示欢迎消息
                response = f"""👋 欢迎使用智能教案生成系统！

我可以帮您生成高质量的教案，支持数学、物理、化学等多个学科。

**您可以：**
1. ✏️ 直接告诉我您需要的教案主题，例如："生成一份关于指数函数的教案"
2. 📋 提供详细信息，例如："为高中二年级学生生成一份2课时的指数函数教案"
3. 🔍 查看示例，例如："查看教案示例"
4. 📚 了解系统功能，例如："你能做什么"

请告诉我您的需求，我将为您生成最适合的教案！"""
                
                session["conversation_history"].append({"role": "assistant", "content": response})
                # 更新会话最后活动时间
                session["last_activity"] = str(time.time())
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "welcome",
                    "response": response,
                    "progress": 0
                }
        else:
            # 记录用户输入
            session["conversation_history"].append({"role": "user", "content": user_input})
        # 更新会话最后活动时间
        session["last_activity"] = str(time.time())
        
        # 检查用户是否要求"直接生成"
        direct_generate_keywords = ["直接生成", "跳过引导", "生成教案"]
        if any(keyword in user_input for keyword in direct_generate_keywords):
            print(f"🚀 用户要求直接生成教案，跳过引导")
            # 确保至少有课题
            if "topic" not in session["collected_info"] or not session["collected_info"]["topic"]:
                session["collected_info"]["topic"] = user_input
            return self._generate_complete_lesson_plan(session_id, session)
        
        # 2. 分析用户输入，提取信息
        extracted_info = self._extract_lesson_plan_info(user_input, session)
        session["collected_info"].update(extracted_info)
        
        # 3. 判断信息完整度
        completion_level = self._assess_info_completion(session["collected_info"])
        
        # 更新进度
        if completion_level == LessonPlanInfoCompletion.COMPLETE:
            session["progress"] = 100
        elif completion_level == LessonPlanInfoCompletion.PARTIAL:
            session["progress"] = 60
        else:  # MINIMAL
            session["progress"] = 30
        
        print(f"📊 信息完整度: {completion_level.value}")
        print(f"📋 已收集信息: {list(session['collected_info'].keys())}")
        print(f"📈 进度: {session['progress']}%")
        
        # 4. 根据完整度决定处理方式
        if completion_level == LessonPlanInfoCompletion.COMPLETE:
            return self._generate_complete_lesson_plan(session_id, session)
        else:
            return self._guide_for_more_info(session_id, session, completion_level)
    
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
    
    def _backup_extract_info(self, user_input: str, existing_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        备用信息提取方法 - 基于关键词的简单提取
        
        当大模型提取失败时使用
        
        Args:
            user_input: 用户输入
            existing_info: 已有信息
        
        Returns:
            提取的信息
        """
        extracted = {}
        
        # 简单关键词匹配
        import re
        
        # 年级/学生水平
        if "student_level" not in existing_info:
            grade_patterns = [
                (r'高[一二三四]', '高一'),
                (r'初[一二三]', '初一'),
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
        if "class_hours" not in existing_info:
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
        if "teaching_methods" not in existing_info:
            method_keywords = ['探究式', '讲授式', '合作学习', '问题解决', '启发式', '讨论式', '演示法', '练习法']
            found_methods = [kw for kw in method_keywords if kw in user_input]
            if found_methods:
                extracted["teaching_methods"] = '、'.join(found_methods)
        
        # 教学目标
        if "teaching_goals" not in existing_info:
            if any(keyword in user_input for keyword in ["目标", "学会", "掌握", "理解"]):
                extracted["teaching_goals"] = user_input
        
        # 教学重点
        if "key_points" not in existing_info:
            if any(keyword in user_input for keyword in ["重点", "关键", "核心"]):
                extracted["key_points"] = user_input
        
        # 教学难点
        if "difficulties" not in existing_info:
            if any(keyword in user_input for keyword in ["难点", "困难", "难以理解"]):
                extracted["difficulties"] = user_input
        
        # 课题
        if "topic" not in existing_info:
            extracted["topic"] = user_input
        
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
        智能引导用户补充信息 - 上下文感知引导
        
        Args:
            session_id: 会话ID
            session: 会话状态
            completion_level: 信息完整度
        
        Returns:
            引导响应
        """
        collected_info = session["collected_info"]
        topic = collected_info.get("topic", "这个课题")
        progress = session.get("progress", 0)
        
        # 生成进度条
        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        
        # 分析已有信息，生成个性化的引导问题
        missing_items = []
        if "teaching_goals" not in collected_info:
            missing_items.append("教学目标")
        if "teaching_methods" not in collected_info:
            missing_items.append("教学方法")
        if "student_level" not in collected_info:
            missing_items.append("学生水平/年级")
        if "class_hours" not in collected_info:
            missing_items.append("课时安排")
        if "key_points" not in collected_info:
            missing_items.append("教学重点")
        if "difficulties" not in collected_info:
            missing_items.append("教学难点")
        
        # 根据已有信息生成上下文感知的引导
        if completion_level == LessonPlanInfoCompletion.MINIMAL:
            response = f"""好的！让我们一起为「{topic}」设计一份优秀的教案。📝

为了给您生成最贴合需求的教案，我需要了解一些关键信息：

1. **教学目标**：这节课您希望学生达到什么目标？（知识、能力、情感等）
2. **教学方法**：您倾向于用什么教学方法？（探究式、讲授式、问题解决等）
3. **学生情况**：授课对象是哪个年级？学生基础如何？
4. **课时安排**：这节课计划用多少课时？

您可以一次性告诉我这些信息，也可以先回答其中一部分，我们逐步完善！

如果您觉得现有信息已经足够，也可以直接回复"直接生成"，我会基于当前信息为您生成教案。"""
        
        else:  # PARTIAL
            # 生成个性化的引导问题
            personalized_questions = []
            
            if "teaching_goals" not in collected_info:
                if "student_level" in collected_info:
                    personalized_questions.append(f"**教学目标**：针对{collected_info['student_level']}的学生，您希望他们通过这节课达到什么目标？")
                else:
                    personalized_questions.append("**教学目标**：您希望学生通过这节课达到什么目标？（知识、能力、情感等）")
            
            if "teaching_methods" not in collected_info:
                if "student_level" in collected_info:
                    personalized_questions.append(f"**教学方法**：针对{collected_info['student_level']}的学生，您倾向于使用什么教学方法？")
                else:
                    personalized_questions.append("**教学方法**：您倾向于使用什么教学方法？（探究式、讲授式、问题解决等）")
            
            if "student_level" not in collected_info:
                personalized_questions.append("**学生情况**：授课对象是哪个年级？学生基础如何？")
            
            if "class_hours" not in collected_info:
                personalized_questions.append("**课时安排**：这节课计划用多少课时？")
            
            if "key_points" not in collected_info:
                personalized_questions.append(f"**教学重点**：「{topic}」的教学重点是什么？")
            
            if "difficulties" not in collected_info:
                personalized_questions.append(f"**教学难点**：学生学习「{topic}」时可能遇到的困难是什么？")
            
            response = f"""很好！我已经了解到一些关于「{topic}」的信息了。👍

为了生成更完善的教案，我还需要了解：
{chr(10).join([f"- {item}" for item in personalized_questions])}

请告诉我这些信息，或者如果您觉得信息已经足够了，也可以直接回复"直接生成"，我会基于现有信息为您生成教案！"""
        
        session["conversation_history"].append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "guiding",
            "response": response,
            "progress": progress,
            "collected_info": collected_info,
            "conversation_history": session["conversation_history"],
            "missing_items": missing_items
        }
    
    def _generate_summary(self, lesson_plan_content: str) -> str:
        """
        生成结构化的教案摘要（现在返回完整内容，不再截断）
        
        Args:
            lesson_plan_content: 完整的教案内容
        
        Returns:
            完整的教案内容（不再截断）
        """
        # 直接返回完整教案内容，不再进行截断
        # 确保用户能够看到完整的教案
        return lesson_plan_content
    
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
        
        # 更新进度为80%（正在生成）
        session["progress"] = 80
        
        # 1. 构建增强的用户输入
        enhanced_input = self._build_enhanced_input(collected_info)
        
        # 2. 检索相关资源
        retrieved_resources = self.resource_retriever.retrieve(
            enhanced_input,
            intent="generate_lesson_plan"
        )
        
        theory_resources = retrieved_resources.get("theory_resources", [])
        lesson_plan_patterns = retrieved_resources.get("lesson_plan_patterns", [])
        
        # 限制资源数量，确保生成的教案更加聚焦
        max_resources = 5  # 最多使用5个理论资源
        max_patterns = 3   # 最多使用3个教案示例
        theory_resources = theory_resources[:max_resources]
        lesson_plan_patterns = lesson_plan_patterns[:max_patterns]
        
        print(f"📚 理论资源: {len(theory_resources)}条 (限制为{max_resources}条)")
        print(f"📄 教案示例: {len(lesson_plan_patterns)}条 (限制为{max_patterns}条)")
        
        # 3. 生成教案
        lesson_plan_content = self.lesson_plan_generator.generate(
            enhanced_input,
            theory_resources,
            lesson_plan_patterns
        )
        
        session["lesson_plan"] = lesson_plan_content
        # 存储最新生成的教案
        self.latest_lesson_plan = lesson_plan_content
        self.latest_topic = topic
        # 保存最新教案到文件
        self._save_latest_lesson_plan()
        # 更新会话最后活动时间
        session["last_activity"] = str(time.time())  # 使用真实的时间戳
        # 更新进度为100%（完成）
        session["progress"] = 100
        
        # 4. 构建响应
        summary = self._generate_summary(lesson_plan_content)
        response = f"""🎉 太棒了！教案已经生成完成！

**课题：** {topic}

**教案摘要：**
{summary}

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
            "progress": 100,
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
            # 尝试从最新教案恢复
            if self.latest_lesson_plan:
                session_id = f"lp_{uuid.uuid4().hex[:8]}"
                self.sessions[session_id] = {
                    "collected_info": {"topic": self.latest_topic or "教案"},
                    "lesson_plan": self.latest_lesson_plan,
                    "conversation_history": [],
                    "last_activity": str(time.time())
                }
                print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
                session = self.sessions[session_id]
            else:
                print(f"❌ 会话不存在且无最新教案: {session_id}")
                return {
                    "success": False,
                    "error": "对话已过期，请重新开始",
                    "session_id": session_id
                }
        else:
            session = self.sessions[session_id]
        
        if not session.get("lesson_plan"):
            return {
                "success": False,
                "error": "还没有生成教案，请先生成教案",
                "session_id": session_id
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
        
        try:
            revised_lesson_plan = chain.invoke({
                "original_lesson_plan": session["lesson_plan"],
                "revision_request": revision_request
            })
            
            session["lesson_plan"] = revised_lesson_plan
            
            response = f"""✅ 教案修改成功！

**您的修改意见：**
{revision_request}

**修订后的教案摘要：**
{self._generate_summary(revised_lesson_plan)}

---

**您可以：**
1. ✏️ 继续提出修改意见，我会帮您进一步调整
2. 📥 导出教案（支持 Markdown、HTML、Word 格式）
3. 👁️ 查看完整教案内容
4. 🔄 确认教案完成

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
        except Exception as e:
            print(f"❌ 修改教案失败: {e}")
            response = "抱歉，修改教案时遇到了问题，请稍后再试。"
            session["conversation_history"].append({"role": "assistant", "content": response})
            return {
                "success": False,
                "error": "修改教案时遇到了问题，请稍后再试",
                "session_id": session_id
            }
    
    def export_lesson_plan(
        self,
        session_id: str,
        export_format: str = "markdown",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导出教案 - 返回文件内容供前端下载
        
        Args:
            session_id: 会话ID
            export_format: 导出格式
            filename: 文件名
        
        Returns:
            导出结果，包含文件内容和文件名
        """
        if session_id not in self.sessions:
            # 尝试从最新教案恢复
            if self.latest_lesson_plan:
                session_id = f"lp_{uuid.uuid4().hex[:8]}"
                self.sessions[session_id] = {
                    "collected_info": {"topic": self.latest_topic or "教案"},
                    "lesson_plan": self.latest_lesson_plan,
                    "conversation_history": [],
                    "last_activity": str(time.time())
                }
                print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
                session = self.sessions[session_id]
            else:
                print(f"❌ 会话不存在且无最新教案: {session_id}")
                return {
                    "success": False,
                    "error": "对话已过期，请重新开始"
                }
        else:
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
        
        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic = metadata.get("topic", "教案").replace(" ", "_")[:20]
            filename = f"{topic}_{timestamp}"
        
        # 移除文件扩展名（如果有的话）
        filename = filename.replace(".md", "").replace(".html", "").replace(".docx", "").replace(".pdf", "")
        
        try:
            if export_format == "markdown":
                content = self._get_markdown_content(lesson_plan_content, metadata)
                return {
                    "success": True,
                    "content": content,
                    "filename": f"{filename}.md",
                    "format": "markdown"
                }
            elif export_format == "html":
                content = self._get_html_content(lesson_plan_content, metadata)
                return {
                    "success": True,
                    "content": content,
                    "filename": f"{filename}.html",
                    "format": "html"
                }
            elif export_format == "docx":
                return {
                    "success": False,
                    "error": "DOCX格式暂不支持，请使用Markdown或HTML格式"
                }
            elif export_format == "all":
                content = self._get_markdown_content(lesson_plan_content, metadata)
                return {
                    "success": True,
                    "content": content,
                    "filename": f"{filename}.md",
                    "format": "markdown"
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的导出格式: {export_format}"
                }
            
        except Exception as e:
            print(f"❌ 导出教案失败: {e}")
            return {
                "success": False,
                "error": "导出教案时遇到了问题，请稍后再试"
            }
    
    def _get_markdown_content(self, lesson_plan_content: str, metadata: Dict[str, Any]) -> str:
        """
        获取Markdown格式的内容
        
        Args:
            lesson_plan_content: 教案内容
            metadata: 元数据
        
        Returns:
            Markdown格式的内容
        """
        # 添加元数据头部
        header_lines = ["---"]
        for key, value in metadata.items():
            if value:
                header_lines.append(f"{key}: {value}")
        header_lines.append(f"export_time: {datetime.now().isoformat()}")
        header_lines.append("---")
        header_lines.append("")
        
        return "\n".join(header_lines) + lesson_plan_content
    
    def _get_html_content(self, lesson_plan_content: str, metadata: Dict[str, Any]) -> str:
        """
        获取HTML格式的内容
        
        Args:
            lesson_plan_content: 教案内容
            metadata: 元数据
        
        Returns:
            HTML格式的内容
        """
        import markdown
        
        title = metadata.get("topic", "教案")
        html_content = markdown.markdown(
            lesson_plan_content,
            extensions=['extra', 'tables', 'toc']
        )
        
        meta_tags = ""
        for key, value in metadata.items():
            if value:
                meta_tags += f'<meta name="{key}" content="{value}">\n'
        
        css = self._get_html_css()
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {meta_tags}
    <title>{title}</title>
    {css}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
        return html
    
    def _get_html_css(self) -> str:
        """获取HTML样式"""
        return """<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: "Microsoft YaHei", "SimSun", sans-serif;
        line-height: 1.8;
        color: #333;
        background-color: #f5f5f5;
        padding: 20px;
    }
    .container {
        max-width: 900px;
        margin: 0 auto;
        background-color: white;
        padding: 40px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-radius: 8px;
    }
    h1 {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 30px;
        padding-bottom: 15px;
        border-bottom: 2px solid #3498db;
    }
    h2 {
        color: #34495e;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-left: 10px;
        border-left: 4px solid #3498db;
    }
    h3 {
        color: #555;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    p {
        margin-bottom: 15px;
        text-align: justify;
    }
    ul, ol {
        margin-left: 30px;
        margin-bottom: 15px;
    }
    li {
        margin-bottom: 8px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    tr:hover {
        background-color: #f5f5f5;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: "Courier New", monospace;
    }
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        margin: 15px 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 20px;
        margin: 20px 0;
        color: #666;
        font-style: italic;
    }
    @media print {
        body {
            background-color: white;
            padding: 0;
        }
        .container {
            box-shadow: none;
            padding: 20px;
        }
    }
</style>"""
    
    def _clean_expired_sessions(self):
        """
        清理过期会话
        """
        import time
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity = session.get("last_activity")
            if last_activity:
                # 尝试将UUID转换为时间戳（简化处理）
                # 实际项目中应该使用真实的时间戳
                if len(last_activity) == 36:  # UUID格式
                    # 这里简化处理，实际应该存储真实的时间戳
                    continue
                try:
                    last_activity_time = float(last_activity)
                    if current_time - last_activity_time > self.session_timeout:
                        expired_sessions.append(session_id)
                except:
                    pass
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🗑️ 清理过期会话: {session_id}")
    
    def _update_session_activity(self, session_id: str):
        """
        更新会话活动时间
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = str(time.time())
            print(f"⏰ 更新会话活动时间: {session_id}")
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return None
        # 更新会话活动时间
        self._update_session_activity(session_id)
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
