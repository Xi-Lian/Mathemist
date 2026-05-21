#!/usr/bin/env python3
import chromadb
import jieba

client = chromadb.PersistentClient(path='backend/chroma_db')

collections = client.list_collections()
print("数据库中的集合:")
for col in collections:
    print(f"  - {col.name}")

for col in collections:
    if 'probability' in col.name.lower() or '统计' in col.name:
        print(f"\n使用集合: {col.name}")
        collection = client.get_collection(col.name)

        results = collection.get(
            where={'resource_type': 'courseware'},
            include=['documents', 'metadatas']
        )

        print(f"数据库中courseware总数: {len(results['documents'])}")

        core_theme = '分类加法计数原理'
        themes = core_theme.split(',')
        themes = [theme.strip() for theme in themes if theme.strip()]

        core_theme_keywords = []
        for theme in themes:
            theme_keywords = list(jieba.cut(theme))
            theme_keywords = [kw for kw in theme_keywords if len(kw) > 1]
            core_theme_keywords.extend(theme_keywords)
        core_theme_keywords = list(set(core_theme_keywords))

        matched_courseware = []
        for i, meta in enumerate(results['metadatas']):
            title = meta.get('title', '')
            teaching_use = meta.get('教学用途', '') or ''
            haystack = f'{title} {teaching_use}'

            match_found = False
            for theme in themes:
                if theme in haystack:
                    match_found = True
                    break

            if not match_found:
                for keyword in core_theme_keywords:
                    if keyword in haystack:
                        match_found = True
                        break

            if match_found and '练习课' in teaching_use:
                matched_courseware.append(meta)
                print(f"匹配: {title}")
                print(f"  教学用途: {teaching_use}")
                print(f"  资源类型: {meta.get('resource_type', 'N/A')}")

        print(f"\n总匹配数: {len(matched_courseware)}")

        print("\n检查这些资源的resource_type字段:")
        for meta in matched_courseware:
            print(f"  {meta.get('title', '')[:30]}... -> resource_type: {meta.get('resource_type', 'N/A')}")