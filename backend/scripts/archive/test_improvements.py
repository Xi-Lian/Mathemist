import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.retrieval.retrieve_helpers.single_theme import execute_single_theme_retrieval
import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 创建模拟的retriever对象
class MockRetriever:
    DEFAULT_N_RESULTS = 50
    
    def _adjust_retrieval_count(self, query, detected_intents, n_results, resource_types=None):
        return n_results

# 测试查询
query = "组合数的练习课课件"
resource_types = ["课件", "PPT", "教学设计", "习题"]

# 执行检索
retriever = MockRetriever()
query_to_use, core_theme, results = execute_single_theme_retrieval(
    retriever=retriever,
    collection=prob_coll,
    query=query,
    core_theme="组合数",
    n_results=50,
    resource_types=resource_types,
    question_type=None
)

print(f"\n检索完成，核心主题: '{core_theme}'")
if results and results.get('documents'):
    print(f"找到 {len(results['documents'][0])} 条结果")

    # 统计组合数练习课课件的数量
    combo_count = 0
    print("\n检索结果中的组合数练习课课件:")
    for i, meta in enumerate(results['metadatas'][0]):
        title = meta.get('title', '')
        teaching_use = meta.get('教学用途', '')
        dist = results['distances'][0][i]
        
        if teaching_use == '练习课课件' and '组合' in title:
            combo_count += 1
            print(f"{combo_count}. 标题: {title}")
            print(f"   教学用途: {teaching_use}")
            print(f"   距离: {dist:.4f}")
            print()

    print(f"\n共找到 {combo_count} 条组合数练习课课件")

    # 检查数据库中总共有多少条组合数练习课课件
    all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])
    total_combo = 0
    for meta in all_courseware['metadatas']:
        if meta.get('教学用途') == '练习课课件' and '组合' in meta.get('title', ''):
            total_combo += 1

    print(f"数据库中共有 {total_combo} 条组合数练习课课件")
    print(f"召回率: {combo_count}/{total_combo} = {combo_count/total_combo*100:.1f}%")
else:
    print("未找到任何结果")
