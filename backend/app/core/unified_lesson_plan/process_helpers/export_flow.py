from .._shared import *
from .session import recover_session_from_latest


FORMAT_SELECTION_RESPONSE = """📥 请选择您需要的导出格式：

1. 📄 Markdown格式 - 适合在编辑器中查看和编辑
2. 🌐 HTML格式 - 适合在浏览器中查看
3. 📝 Word格式 - 适合正式文档和打印
4. 📕 PDF格式 - 适合打印与分享
5. 📦 全部格式 - 同时导出所有格式（ZIP）

请回复对应的数字或格式名称，例如："1"、"Word" 或 "PDF"。"""


def handle_view_full_lesson_plan(system, user_input, session_id):
    normalized_input = user_input.replace(" ", "")
    if "查看完整教案" not in normalized_input and "完整教案" not in normalized_input:
        return None

    print("👁️ 用户要求查看完整教案")
    if session_id and session_id in system.sessions:
        session = system.sessions[session_id]
        if session.get("lesson_plan"):
            lesson_plan = session["lesson_plan"]
            export_result = system.export_lesson_plan(session_id, "markdown")
            response = f"""📖 完整教案如下：

{lesson_plan}

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
                "conversation_history": session["conversation_history"],
            }
            if export_result.get("success"):
                result["export_data"] = {
                    "content": export_result.get("content", ""),
                    "filename": export_result.get("filename", "lesson_plan.md"),
                    "format": export_result.get("format", "markdown"),
                    "encoding": export_result.get("encoding"),
                    "mime_type": export_result.get("mime_type"),
                }
            return result

        response = "抱歉，还没有生成教案，请先生成教案后再查看完整内容。"
        session["conversation_history"].append({"role": "assistant", "content": response})
        return {"success": False, "session_id": session_id, "status": "error", "response": response}

    response = """⚠️ 无法查看完整教案

您需要提供会话ID才能查看完整教案。

**如何获取会话ID：**
- 查看您生成教案时的响应，其中包含了会话ID
- 会话ID格式类似：`lp_xxxxxxxx`（以lp_开头，后面跟着8位字符）

**请提供会话ID，然后再次说"查看完整教案"。"""
    if session_id and session_id in system.sessions:
        system.sessions[session_id]["conversation_history"].append({"role": "assistant", "content": response})
    return {"success": False, "session_id": session_id, "status": "error", "response": response}


def handle_export_request(system, user_input, session_id):
    if "导出教案" not in user_input:
        return None

    print("💾 用户要求导出教案")
    export_format = infer_export_format(user_input)
    if session_id and session_id in system.sessions:
        return _export_from_session(system, user_input, session_id, export_format)

    session_id, _ = recover_session_from_latest(system)
    if session_id:
        print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
        return _export_from_session(system, user_input, session_id, export_format)
    return {"success": False, "status": "error", "response": "抱歉，未找到相关教案，请先生成教案。"}


def handle_format_selection_reply(system, user_input, session_id):
    if not (session_id and session_id in system.sessions):
        return None
    session = system.sessions[session_id]
    if not session.get("conversation_history"):
        return None
    last_message = session["conversation_history"][-1]
    if last_message.get("role") != "assistant" or "请选择您需要的导出格式" not in last_message.get("content", ""):
        return None

    export_format = parse_export_choice(user_input)
    export_result = system.export_lesson_plan(session_id, export_format)
    return build_export_response(session, session_id, export_result)


def infer_export_format(user_input):
    if "全部" in user_input or "所有" in user_input:
        return "all"
    lowered = user_input.lower()
    if "word" in lowered or "docx" in lowered:
        return "docx"
    if "pdf" in lowered:
        return "pdf"
    if "html" in lowered:
        return "html"
    return "markdown"


def parse_export_choice(user_input):
    user_choice = user_input.strip().lower()
    if user_choice in ["1", "markdown", "md"]:
        return "markdown"
    if user_choice in ["2", "html"]:
        return "html"
    if user_choice in ["3", "word", "docx"]:
        return "docx"
    if user_choice in ["4", "pdf"]:
        return "pdf"
    if user_choice in ["5", "全部", "所有", "all"]:
        return "all"
    return "markdown"


def _export_from_session(system, user_input, session_id, export_format):
    session = system.sessions[session_id]
    if not session.get("lesson_plan"):
        response = "抱歉，还没有生成教案，请先生成教案后再导出。"
        session["conversation_history"].append({"role": "assistant", "content": response})
        return {"success": False, "session_id": session_id, "status": "error", "response": response}

    if "格式" in user_input or "导出为" in user_input:
        session["conversation_history"].append({"role": "assistant", "content": FORMAT_SELECTION_RESPONSE})
        return {"success": True, "session_id": session_id, "status": "format_selection", "response": FORMAT_SELECTION_RESPONSE}

    export_result = system.export_lesson_plan(session_id, export_format)
    return build_export_response(session, session_id, export_result)


def build_export_response(session, session_id, export_result):
    if not export_result.get("success"):
        response = f"导出失败：{export_result.get('error', '未知错误')}"
        session["conversation_history"].append({"role": "assistant", "content": response})
        return {"success": False, "session_id": session_id, "status": "error", "response": response}

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
            "format": format_type,
            "encoding": export_result.get("encoding"),
            "mime_type": export_result.get("mime_type"),
        },
    }
