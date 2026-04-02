from .._shared import *


def prepare_generation_turn(system, user_input, session_id, session):
    is_first_interaction = len(session.get("conversation_history", [])) == 0
    if is_first_interaction:
        extracted_info = system._extract_lesson_plan_info(user_input, session)
        if extracted_info.get("topic"):
            print("📝 首次交互但用户已提供足够信息，直接处理")
            session["conversation_history"].append({"role": "user", "content": user_input})
            session["last_activity"] = str(time.time())
            return None

        try:
            welcome_response = system._generate_lesson_plan_dialogue(
                mode="welcome",
                topic=user_input or "教案需求",
                progress=0,
                collected_info=session.get("collected_info", {}),
                missing_items=["课题", "教学目标", "授课对象", "课时安排"],
                extra_context="用户刚进入教案协作流程，但还没有给出足够信息。",
            )
        except Exception as exc:
            print(f"⚠️ 欢迎回复生成失败，使用降级文案: {exc}")
            welcome_response = "你直接告诉我教案主题、年级、课时或教学目标中的任意几项就行，我会边补全边往下做。"

        session["conversation_history"].append({"role": "assistant", "content": welcome_response})
        session["last_activity"] = str(time.time())
        return {
            "success": True,
            "session_id": session_id,
            "status": "welcome",
            "response": welcome_response,
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
