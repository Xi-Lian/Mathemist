from .._shared import *


class _ExportLessonPlanMixin:
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
        export_format = export_format.strip().lower()
        
        try:
            if export_format == "markdown":
                content = self._get_markdown_content(lesson_plan_content, metadata)
                return {
                    "success": True,
                    "content": content,
                    "filename": f"{filename}.md",
                    "format": "markdown",
                    "mime_type": "text/markdown"
                }
            elif export_format == "html":
                content = self._get_html_content(lesson_plan_content, metadata)
                return {
                    "success": True,
                    "content": content,
                    "filename": f"{filename}.html",
                    "format": "html",
                    "mime_type": "text/html"
                }
            elif export_format == "docx":
                filepath = export_lesson_plan_docx(lesson_plan_content, filename, metadata)
                with open(filepath, "rb") as f:
                    content_b64 = base64.b64encode(f.read()).decode("ascii")
                return {
                    "success": True,
                    "content": content_b64,
                    "filename": f"{filename}.docx",
                    "format": "docx",
                    "encoding": "base64",
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            elif export_format == "pdf":
                filepath = export_lesson_plan_pdf(lesson_plan_content, filename, metadata)
                with open(filepath, "rb") as f:
                    content_b64 = base64.b64encode(f.read()).decode("ascii")
                return {
                    "success": True,
                    "content": content_b64,
                    "filename": f"{filename}.pdf",
                    "format": "pdf",
                    "encoding": "base64",
                    "mime_type": "application/pdf"
                }
            elif export_format == "all":
                markdown_content = self._get_markdown_content(lesson_plan_content, metadata)
                html_content = self._get_html_content(lesson_plan_content, metadata)
                docx_path = export_lesson_plan_docx(lesson_plan_content, filename, metadata)
                pdf_path = export_lesson_plan_pdf(lesson_plan_content, filename, metadata)
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"{filename}.md", markdown_content.encode("utf-8"))
                    zip_file.writestr(f"{filename}.html", html_content.encode("utf-8"))
                    with open(docx_path, "rb") as f:
                        zip_file.writestr(f"{filename}.docx", f.read())
                    with open(pdf_path, "rb") as f:
                        zip_file.writestr(f"{filename}.pdf", f.read())
                content_b64 = base64.b64encode(zip_buffer.getvalue()).decode("ascii")
                return {
                    "success": True,
                    "content": content_b64,
                    "filename": f"{filename}.zip",
                    "format": "zip",
                    "encoding": "base64",
                    "mime_type": "application/zip"
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
