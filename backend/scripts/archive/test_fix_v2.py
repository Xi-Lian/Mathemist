#!/usr/bin/env python
import os
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_fix():
    print("测试修复: 查询术语提取")
    print("="*60)

    from app.core.retrieval.retrieve_helpers.postprocess import _extract_query_terms

    query = "立体几何的练习课课件"

    print("[步骤] 测试查询术语提取")
    print("  原始查询: " + query)

    terms = _extract_query_terms(query, "立体几何")
    print("  提取的术语: " + str(terms))

    if "练习课" in str(terms) or "练习课课件" in str(terms):
        print("  结果: 练习课关键词被正确保留")
        return True
    else:
        print("  结果: 练习课关键词被丢失")
        return False

if __name__ == "__main__":
    try:
        result = test_fix()
        if result:
            print("\n修复验证成功!")
        else:
            print("\n修复验证失败!")
    except Exception as e:
        print("出错: " + str(e))
        import traceback
        traceback.print_exc()