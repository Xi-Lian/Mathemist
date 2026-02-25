"""
用户反馈系统 - 管理员测试工具

快速查看和分析用户反馈数据
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def print_separator(title):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_statistics():
    """测试统计概览"""
    print_separator("1. 📊 统计概览")
    try:
        response = requests.get(f"{BASE_URL}/feedback/statistics")
        data = response.json()
        
        if data.get("success"):
            stats = data["statistics"]
            total = stats["total_likes"] + stats["total_dislikes"]
            like_rate = (stats["total_likes"] / total * 100) if total > 0 else 0
            
            print(f"  总点赞: {stats['total_likes']} 👍")
            print(f"  总点踩: {stats['total_dislikes']} 👎")
            print(f"  总反馈: {total}")
            print(f"  点赞率: {like_rate:.1f}%")
            
            if stats.get("feedback_by_type"):
                print("\n  各资源类型反馈:")
                for rtype, counts in stats["feedback_by_type"].items():
                    print(f"    - {rtype}: 点赞={counts['likes']}, 点踩={counts['dislikes']}")
        else:
            print("  ❌ 获取统计失败")
    except Exception as e:
        print(f"  ❌ 错误: {e}")


def test_disliked():
    """测试被点踩最多的资源"""
    print_separator("2. 👎 被点踩最多的资源 (Top 10)")
    try:
        response = requests.get(f"{BASE_URL}/feedback/disliked?limit=10")
        data = response.json()
        
        if data.get("success"):
            resources = data["resources"]
            if resources:
                for i, res in enumerate(resources, 1):
                    print(f"\n  {i}. 资源ID: {res['resource_id']}")
                    print(f"     点踩次数: {res['dislike_count']}")
                    if res.get("feedbacks"):
                        latest = res["feedbacks"][-1]
                        print(f"     最新反馈: {latest.get('dislike_reason', 'N/A')}")
                        print(f"     用户查询: {latest.get('query', 'N/A')}")
            else:
                print("  🎉 暂无被点踩的资源！")
        else:
            print("  ❌ 获取数据失败")
    except Exception as e:
        print(f"  ❌ 错误: {e}")


def test_suggestions():
    """测试改进建议"""
    print_separator("3. 💡 改进建议 (最新 10 条)")
    try:
        response = requests.get(f"{BASE_URL}/feedback/suggestions?limit=10")
        data = response.json()
        
        if data.get("success"):
            suggestions = data["suggestions"]
            if suggestions:
                for i, sug in enumerate(reversed(suggestions[-10:]), 1):
                    print(f"\n  {i}. 时间: {sug['timestamp'][:19]}")
                    print(f"     查询: {sug.get('query', 'N/A')}")
                    print(f"     建议: {sug['suggestion']}")
                    if sug.get("contact"):
                        print(f"     联系方式: {sug['contact']}")
            else:
                print("  📝 暂无改进建议")
        else:
            print("  ❌ 获取数据失败")
    except Exception as e:
        print(f"  ❌ 错误: {e}")


def test_export():
    """测试导出数据"""
    print_separator("4. 💾 导出反馈数据")
    try:
        response = requests.get(f"{BASE_URL}/feedback/export")
        data = response.json()
        
        if data.get("success"):
            print(f"  ✅ 数据已导出到:")
            print(f"     {data['export_path']}")
        else:
            print("  ❌ 导出失败")
    except Exception as e:
        print(f"  ❌ 错误: {e}")


def main():
    print("\n" + "="*70)
    print("  🎯 用户反馈系统 - 管理员测试工具")
    print("="*70)
    
    try:
        # 检查后端服务是否运行
        print("\n🔍 检查后端服务...")
        requests.get(f"{BASE_URL}/health", timeout=3)
        print("✅ 后端服务运行正常！")
        
        # 运行所有测试
        test_statistics()
        test_disliked()
        test_suggestions()
        test_export()
        
        print_separator("✅ 所有测试完成！")
        print("\n💡 提示:")
        print("  - 反馈数据保存在: backend/data/user_feedback.json")
        print("  - 可以直接编辑该文件查看/删除反馈")
        print("  - 详细使用说明请查看: backend/ADMIN_FEEDBACK_GUIDE.md")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端服务！")
        print("\n💡 请先启动后端服务:")
        print("  cd backend")
        print("  python main.py")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n❌ 错误：连接超时！")
        print("请检查后端服务是否正常运行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
