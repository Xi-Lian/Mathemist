import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在merge_retrieved_resources函数中添加调试日志
old_code = '''def merge_retrieved_resources(resource_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = get_empty_retrieved_resources()
    if not resource_groups:
        return merged

    # 为每个资源类别创建全局的去重集合，存储资源标识到资源索引的映射
    seen_per_category = {}
    for group in resource_groups:
        if not isinstance(group, dict):
            continue
        for key, value in group.items():
            if key not in merged or not isinstance(value, list):
                continue
            # 为每个类别初始化去重集合
            if key not in seen_per_category:
                seen_per_category[key] = {}
                # 将已存在的资源添加到去重集合
                for idx, item in enumerate(merged[key]):
                    if isinstance(item, dict):
                        identity = resource_identity(item)
                        if identity:
                            seen_per_category[key][identity] = idx
            
            existing = merged[key]
            seen = seen_per_category[key]
            for item in value:
                if not isinstance(item, dict):
                    continue
                identity = resource_identity(item)
                if identity and identity in seen:
                    # 资源已存在，合并matched_themes字段
                    existing_idx = seen[identity]
                    existing_item = existing[existing_idx]
                    
                    # 合并matched_themes
                    existing_themes = existing_item.get('matched_themes', [])
                    new_themes = item.get('matched_themes', [])
                    for theme in new_themes:
                        if theme not in existing_themes:
                            existing_themes.append(theme)
                    existing_item['matched_themes'] = existing_themes
                    
                    # 合并theme_distances
                    existing_distances = existing_item.get('theme_distances', {})
                    new_distances = item.get('theme_distances', {})
                    existing_distances.update(new_distances)
                    existing_item['theme_distances'] = existing_distances
                    
                    # 更新matched_theme_count
                    existing_item['matched_theme_count'] = len(existing_themes)
                    
                    continue
                
                if identity:
                    seen[identity] = len(existing)
                existing.append(item)
    return merged'''

new_code = '''def merge_retrieved_resources(resource_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = get_empty_retrieved_resources()
    if not resource_groups:
        return merged

    print(f"[DEBUG] merge_retrieved_resources: 合并 {len(resource_groups)} 个资源组")

    # 为每个资源类别创建全局的去重集合，存储资源标识到资源索引的映射
    seen_per_category = {}
    for group_idx, group in enumerate(resource_groups):
        if not isinstance(group, dict):
            continue
        for key, value in group.items():
            if key not in merged or not isinstance(value, list):
                continue
            # 为每个类别初始化去重集合
            if key not in seen_per_category:
                seen_per_category[key] = {}
                # 将已存在的资源添加到去重集合
                for idx, item in enumerate(merged[key]):
                    if isinstance(item, dict):
                        identity = resource_identity(item)
                        if identity:
                            seen_per_category[key][identity] = idx
            
            existing = merged[key]
            seen = seen_per_category[key]
            for item in value:
                if not isinstance(item, dict):
                    continue
                identity = resource_identity(item)
                title = item.get('title', item.get('meta', {}).get('title', '未知'))[:30]
                matched_themes = item.get('matched_themes', [])
                print(f"[DEBUG] 处理资源: {title}, matched_themes={matched_themes}, identity={identity[:50]}")
                
                if identity and identity in seen:
                    # 资源已存在，合并matched_themes字段
                    existing_idx = seen[identity]
                    existing_item = existing[existing_idx]
                    
                    # 合并matched_themes
                    existing_themes = existing_item.get('matched_themes', [])
                    new_themes = item.get('matched_themes', [])
                    print(f"[DEBUG] 合并主题: 现有主题={existing_themes}, 新主题={new_themes}")
                    for theme in new_themes:
                        if theme not in existing_themes:
                            existing_themes.append(theme)
                    existing_item['matched_themes'] = existing_themes
                    
                    # 合并theme_distances
                    existing_distances = existing_item.get('theme_distances', {})
                    new_distances = item.get('theme_distances', {})
                    existing_distances.update(new_distances)
                    existing_item['theme_distances'] = existing_distances
                    
                    # 更新matched_theme_count
                    existing_item['matched_theme_count'] = len(existing_themes)
                    print(f"[DEBUG] 合并后主题={existing_item['matched_themes']}")
                    
                    continue
                
                if identity:
                    seen[identity] = len(existing)
                existing.append(item)
    
    # 统计合并结果
    for key, items in merged.items():
        if isinstance(items, list) and items:
            themes_found = set()
            for item in items:
                for theme in item.get('matched_themes', []):
                    themes_found.add(theme)
            print(f"[DEBUG] 合并结果: {key} 类别有 {len(items)} 个资源，包含主题: {themes_found}")
    
    return merged'''

content = content.replace(old_code, new_code)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件修改完成！")