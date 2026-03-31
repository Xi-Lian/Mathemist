from .._shared import *


WELCOME_RESPONSE = """👋 欢迎使用智能教案生成系统！

我可以帮您生成高质量的教案，支持数学、物理、化学等多个学科。

**您可以：**
1. ✏️ 直接告诉我您需要的教案主题，例如："生成一份关于指数函数的教案"
2. 📋 提供详细信息，例如："为高中二年级学生生成一份2课时的指数函数教案"
3. 🔍 查看示例，例如："查看教案示例"
4. 📚 了解系统功能，例如："你能做什么"

请告诉我您的需求，我将为您生成最适合的教案！"""


def prepare_generation_turn(system, user_input, session_id, session):
    is_first_interaction = len(session.get("conversation_history", [])) == 0
    if is_first_interaction:
        extracted_info = system._extract_lesson_plan_info(user_input, session)
        if extracted_info.get("topic"):
            print("📝 首次交互但用户已提供足够信息，直接处理")
            session["conversation_history"].append({"role": "user", "content": user_input})
            session["last_activity"] = str(time.time())
            return None

        session["conversation_history"].append({"role": "assistant", "content": WELCOME_RESPONSE})
        session["last_activity"] = str(time.time())
        return {
            "success": True,
            "session_id": session_id,
            "status": "welcome",
            "response": WELCOME_RESPONSE,
            "progress": 0,
        }

    session["conversation_history"].append({"role": "user", "content": user_input})
    session["last_activity"] = str(time.time())
    return None


def handle_generation_flow(system, user_input, session_id, session):
    extracted_info = system._extract_lesson_plan_info(user_input, session)
    session["collected_info"].update(extracted_info)
    completion_level = system._assess_info_completion(session["collected_info"])

    if completion_level == LessonPlanInfoCompletion.COMPLETE:
        session["progress"] = 100
    elif completion_level == LessonPlanInfoCompletion.PARTIAL:
        session["progress"] = 60
    else:
        session["progress"] = 30

    print(f"📊 信息完整度: {completion_level.value}")
    print(f"📋 已收集信息: {list(session['collected_info'].keys())}")
    print(f"📈 进度: {session['progress']}%")

    if completion_level == LessonPlanInfoCompletion.COMPLETE:
        return system._generate_complete_lesson_plan(session_id, session)
    return system._guide_for_more_info(session_id, session, completion_level)
