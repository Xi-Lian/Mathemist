from .._shared import *


def has_knowledge_match(retriever, specific_knowledge_points, knowledge_tags, source_file, title, question_content, question_file):
    knowledge_hierarchy = retriever.knowledge_hierarchy
    for kp in specific_knowledge_points:
        if kp not in knowledge_hierarchy:
            continue
        keywords = knowledge_hierarchy[kp].get("keywords", [])
        if knowledge_tags:
            if kp in knowledge_tags:
                print(f"   ✅ 知识点标签完全匹配：'{kp}'")
                return True
            for keyword in keywords:
                if keyword in knowledge_tags:
                    print(f"   ✅ 知识点关键词匹配：'{keyword}'")
                    return True
        if kp in source_file:
            print(f"   ✅ 来源文件匹配：'{kp}'")
            return True
        for keyword in keywords:
            if keyword in source_file:
                print(f"   ✅ 来源文件关键词匹配：'{keyword}'")
                return True
        if kp in title:
            print(f"   ✅ 标题匹配：'{kp}'")
            return True
        for keyword in keywords:
            if keyword in title:
                print(f"   ✅ 标题关键词匹配：'{keyword}'")
                return True
        if question_content:
            if kp in question_content:
                print(f"   ✅ 题目内容匹配：'{kp}'")
                return True
            for keyword in keywords:
                if keyword in question_content:
                    print(f"   ✅ 题目内容关键词匹配：'{keyword}'")
                    return True
        if question_file:
            if kp in question_file:
                print(f"   ✅ 题目文件名匹配：'{kp}'")
                return True
            for keyword in keywords:
                if keyword in question_file:
                    print(f"   ✅ 题目文件名关键词匹配：'{keyword}'")
                    return True
    return False


def contains_conflicting_theme(retriever, specific_knowledge_points, all_info, relevance):
    if relevance > 0.6:
        print(f"   ✅ 中相关性资源：相关性分数{relevance}，放宽匹配条件")
        return False

    knowledge_hierarchy = retriever.knowledge_hierarchy
    for theme_name, theme_info in knowledge_hierarchy.items():
        if theme_name in specific_knowledge_points:
            continue
        same_parent = False
        for kp in specific_knowledge_points:
            if kp in knowledge_hierarchy and theme_name in knowledge_hierarchy:
                kp_parent = knowledge_hierarchy[kp].get("parent_topic")
                theme_parent = knowledge_hierarchy[theme_name].get("parent_topic")
                if kp_parent and theme_parent and kp_parent == theme_parent:
                    same_parent = True
                    break
        if same_parent:
            continue

        for keyword in [k for k in theme_info.get("keywords", []) if len(k) >= 2]:
            if keyword in all_info:
                print(f"   ⚠️ 核心关键词过滤：包含非查询主题 '{theme_name}' 的关键词 '{keyword}'")
                return True
    return False
