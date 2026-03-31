from .._shared import *
from .context import GENERAL_CHAPTERS


def has_path_conflict(retriever, metadata, specific_knowledge_points, source_file, relevance):
    if not source_file:
        return False

    knowledge_hierarchy = retriever.knowledge_hierarchy
    is_general_chapter = any(general in source_file for general in GENERAL_CHAPTERS)

    for kp in specific_knowledge_points:
        if kp in knowledge_hierarchy:
            chapters = knowledge_hierarchy[kp].get("chapters", [])
            if any(chapter in source_file for chapter in chapters):
                print(f"   ✅ 章节匹配：资源在知识点'{kp}'的章节中")
                return False

    for theme_name, theme_info in knowledge_hierarchy.items():
        if theme_name in specific_knowledge_points:
            continue
        chapters = theme_info.get("chapters", [])
        if not any(chapter in source_file for chapter in chapters):
            continue

        has_same_parent, is_parent_child, is_sibling = _check_theme_relation(knowledge_hierarchy, specific_knowledge_points, theme_name)
        if is_general_chapter:
            print(f"   ✅ 通用章节：'{source_file}' 可能包含多个知识点，跳过路径冲突检测")
            continue
        if has_same_parent or is_parent_child:
            if is_sibling:
                print(f"   ✅ 兄弟主题：'{theme_name}' 和查询主题{specific_knowledge_points} 属于同一父主题，不过滤")
            else:
                print(f"   ✅ 父子主题：'{theme_name}' 和查询主题{specific_knowledge_points} 存在父子关系，不过滤")
            continue
        if relevance > 0.7:
            print(f"   ✅ 高相关性资源：相关性分数{relevance}，放宽路径冲突检测")
            continue
        if metadata.get("resource_type", "") in ["lesson_plan", "courseware", "syllabus"]:
            print(f"   ✅ 教学资源：{metadata.get('resource_type', '')} 类型资源，放宽路径冲突检测")
            continue

        print(f"   ⚠️ 路径冲突检测: 资源在'{theme_name}'章节，但查询主题是{specific_knowledge_points}")
        return True

    return False


def _check_theme_relation(knowledge_hierarchy, specific_knowledge_points, theme_name):
    has_same_parent = False
    is_parent_child = False
    is_sibling = False
    for kp in specific_knowledge_points:
        if kp not in knowledge_hierarchy or theme_name not in knowledge_hierarchy:
            continue
        kp_parent = knowledge_hierarchy[kp].get("parent_topic")
        theme_parent = knowledge_hierarchy[theme_name].get("parent_topic")
        if kp_parent and theme_parent and kp_parent == theme_parent:
            has_same_parent = True
            is_sibling = True
            break
        if kp_parent and kp_parent == theme_name:
            is_parent_child = True
            break
        if theme_parent and theme_parent == kp:
            is_parent_child = True
            break
    return has_same_parent, is_parent_child, is_sibling
