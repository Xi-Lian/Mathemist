from .._shared import *
from .session import recover_session_from_latest


REVISION_KEYWORDS = [
    "觉得", "感觉", "认为", "希望", "想要", "需要", "应该", "建议", "提议",
    "修改", "调整", "改进", "完善", "优化", "补充", "增加", "添加", "减少", "删除", "删除掉",
    "能不能", "能否", "可不可以", "是否可以", "能不能够",
    "太短", "太长", "太简单", "太复杂", "不够", "不足", "缺少", "缺乏",
    "改一下", "改改", "调整一下", "完善一下", "优化一下", "补充一下",
    "替换", "换成", "改为", "改成", "变更", "更改", "更新", "重写", "重新写",
    "去掉", "去除", "删去", "移除", "取消", "不要", "不用",
]
GENERATION_KEYWORDS = ["生成", "创建", "新建", "制作", "写一份", "来一份"]
CONTENT_GENERATION_KEYWORDS = ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
RESOURCE_RETRIEVAL_KEYWORDS = ["推送", "找", "推荐", "有没有", "我要找", "想要", "需要"]
SUGGESTION_KEYWORDS = ["觉得", "应该", "建议", "如何", "怎样", "是否"]
DIRECT_GENERATE_KEYWORDS = ["直接生成", "跳过引导", "生成教案"]


def handle_revision_request(system, user_input, session_id):
    # V48.4修复：先检查是否包含生成关键词，如果是则不是修改请求
    has_generation_keyword = any(keyword in user_input for keyword in GENERATION_KEYWORDS)
    if has_generation_keyword:
        print(f"✅ 检测到生成关键词，跳过修改请求判断")
        return None, session_id
    
    has_revision_request = any(keyword in user_input for keyword in REVISION_KEYWORDS)
    if not has_revision_request:
        return None, session_id

    print("✏️ 检测到修改意见")
    if not session_id or session_id not in system.sessions:
        session_id, session = recover_session_from_latest(system)
        if not session:
            print("❌ 检测到修改意见，但没有最新教案")
            return {"success": False, "error": "对话已过期，请重新开始", "session_id": session_id}, session_id
        print(f"🔄 检测到修改意见，从最新教案恢复会话: {session_id}")

    session = system.sessions[session_id]
    if session.get("lesson_plan"):
        print("✏️ 调用修改教案功能")
        return system.revise_lesson_plan(session_id, user_input), session_id

    print("⚠️ 检测到修改意见，但会话中没有教案")
    return None, session_id


def should_reject_resource_request(session, user_input):
    has_content_generation = any(keyword in user_input for keyword in CONTENT_GENERATION_KEYWORDS)
    has_resource_retrieval = any(keyword in user_input for keyword in RESOURCE_RETRIEVAL_KEYWORDS)

    if "帮我" in user_input and has_content_generation:
        has_resource_retrieval = False
        print("🤖 智能识别：'帮我'为礼貌用语，视为内容生成请求")

    recent_history = session.get("conversation_history", [])[-3:]
    has_lesson_plan_discussion = any("教案" in msg.get("content", "") or "lesson_plan" in msg.get("content", "") for msg in recent_history)
    if has_lesson_plan_discussion and has_resource_retrieval:
        has_resource_retrieval = False
        print("🤖 上下文增强：最近在讨论教案，视为教案相关的资源建议")

    if any(keyword in user_input for keyword in SUGGESTION_KEYWORDS) and has_resource_retrieval:
        has_resource_retrieval = False
        print("🤖 意图分类：用户在寻求建议，而非明确的资源请求")

    if has_content_generation and has_resource_retrieval:
        has_resource_retrieval = False
        print("🤖 混合模式：用户同时请求生成教案和资源建议")

    return has_resource_retrieval and not has_content_generation


def is_direct_generate_request(user_input):
    return any(keyword in user_input for keyword in DIRECT_GENERATE_KEYWORDS)
