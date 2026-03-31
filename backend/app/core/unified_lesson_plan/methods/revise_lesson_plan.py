from .._shared import *


class _ReviseLessonPlanMixin:
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
2. 📥 导出教案（支持 Markdown、HTML、Word、PDF 格式）
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
