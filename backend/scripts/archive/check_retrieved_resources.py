#!/usr/bin/env python
import os
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def check_retrieved_resources():
    print("检查检索结果中资源的教学用途")
    print("="*60)

    from app.core.retrieval.optimized_retriever import OptimizedResourceRetriever

    retriever = OptimizedResourceRetriever()

    query = "立体几何的练习课课件"
    print(f"\n查询: '{query}'")

    try:
        results = retriever.retrieve(query=query)

        courseware_resources = results.get('courseware_resources', {}).get('resources', [])

        print(f"\n检索结果：")
        print(f"找到 {len(courseware_resources)} 个课件资源")

        # 统计教学用途分布
        teaching_use_counts = {}
        resource_details = []

        for i, resource in enumerate(courseware_resources[:15], 1):
            title = resource.get('title', '')[:40]
            teaching_use = resource.get('教学用途', '未知')
            teaching_use_counts[teaching_use] = teaching_use_counts.get(teaching_use, 0) + 1

            resource_details.append({
                'rank': i,
                'title': title,
                'teaching_use': teaching_use
            })

            print(f"[{i}] 教学用途: {teaching_use} | {title}")

        print(f"\n教学用途分布:")
        for use, count in teaching_use_counts.items():
            print(f"  {use}: {count}")

        practice_count = teaching_use_counts.get('练习课课件', 0)
        total_count = len(courseware_resources)

        print(f"\n练习课课件占比: {practice_count}/{total_count} = {practice_count/total_count*100:.1f}%")

        if practice_count > total_count * 0.5:
            print("\n✅ 检索结果中练习课课件占比超过50%")
            return True
        else:
            print(f"\n❌ 检索结果中练习课课件占比仅{practice_count/total_count*100:.1f}%，需要进一步优化")
            return False

    except Exception as e:
        print(f"检索出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_retrieved_resources()
