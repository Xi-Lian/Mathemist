#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_semantic_gate():
    print("模拟语义门控检查逻辑")
    print("="*60)

    import jieba

    # 模拟_extract_theme_keywords函数
    def _extract_theme_keywords(core_theme):
        keywords = []
        if isinstance(core_theme, str):
            themes = [t.strip() for t in core_theme.split(',') if t.strip()]
            for theme in themes:
                keywords.append(theme)
                if '指数函数' in theme:
                    keywords.extend(['指数函数', '指数', 'exponential'])
                elif '幂函数' in theme:
                    keywords.extend(['幂函数', '幂'])
                elif '对数函数' in theme:
                    keywords.extend(['对数函数', '对数', 'log'])
                elif '三角函数' in theme:
                    keywords.extend(['三角函数', '三角', 'sin', 'cos', 'tan'])
                else:
                    jieba_keywords = list(jieba.cut(theme))
                    keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
        return list(set(keywords))

    # 模拟_normalize_match_text函数
    def _normalize_match_text(text):
        if not text:
            return ""
        text = text.lower()
        replacements = {
            'Ａ': 'a', 'Ｂ': 'b', 'Ｃ': 'c', 'Ｄ': 'd',
            '０': '0', '１': '1', '２': '2', '３': '3',
            'Ⅰ': '1', 'Ⅱ': '2', 'Ⅲ': '3', 'Ⅳ': '4'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    # 测试1: 核心主题是"组合数"
    core_theme = "组合数"
    theme_keywords = _extract_theme_keywords(core_theme)
    print(f"核心主题: '{core_theme}'")
    print(f"提取的关键词: {theme_keywords}")

    # 测试2: 检查"组合数的综合应用(习题课)"是否匹配
    doc = "组合数的综合应用"
    title = "组合数的综合应用(习题课)"
    knowledge_tags = ""  # 空的
    source_file = "6.2 排列与组合"
    teaching_use = "练习课课件"

    text = _normalize_match_text(f"{doc} {title} {knowledge_tags} {source_file} {teaching_use}")
    print(f"\n检查文本: '{text}'")
    print(f"是否包含'组合数': {'组合数' in text}")
    print(f"是否包含'组合': {'组合' in text}")

    has_direct_match = any(_normalize_match_text(kw) in text for kw in theme_keywords)
    print(f"\nhas_direct_match: {has_direct_match}")

    # 测试3: 检查"排列组合"是否匹配
    doc2 = "排列与组合"
    title2 = "6.2 排列与组合"
    text2 = _normalize_match_text(f"{doc2} {title2} {knowledge_tags} {source_file} {teaching_use}")
    print(f"\n检查文本2: '{text2}'")

    has_direct_match2 = any(_normalize_match_text(kw) in text2 for kw in theme_keywords)
    print(f"has_direct_match2: {has_direct_match2}")

    # 测试4: 使用实际向量检索的结果
    print("\n" + "="*60)
    print("使用实际向量检索结果检查")

    import chromadb
    from app.core.model_config import model_config

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    prob_coll = client.get_collection("math_resources_probability")
    embedding_model = model_config.get_embedding_model()

    query_emb = embedding_model.encode(["组合数 练习课 课件"])
    results = prob_coll.query(
        query_embeddings=query_emb.tolist(),
        n_results=10,
        where={"resource_type": "courseware"},
        include=["documents", "metadatas", "distances"]
    )

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0][:5],
        results['metadatas'][0][:5],
        results['distances'][0][:5]
    ), 1):
        title = meta.get('title', '') or ''
        teaching_use = meta.get('教学用途', '') or ''
        content = meta.get('内容', '') or ''  # 注意：这是metadata中的内容字段

        # 构建text（不使用knowledge_tags，因为它不存在）
        text = _normalize_match_text(f"{doc} {title} {content} {source_file} {teaching_use}")

        has_direct_match = any(_normalize_match_text(kw) in text for kw in theme_keywords)

        print(f"\n[{i}] distance={dist:.4f}, has_direct_match={has_direct_match}")
        print(f"    doc: {doc[:30]}...")
        print(f"    title: {title[:40]}")
        print(f"    content: {content[:40]}")
        print(f"    teaching_use: {teaching_use}")

        # 检查是否包含"组合数"
        print(f"    包含'组合数': {'组合数' in text}")
        print(f"    包含'组合': {'组合' in text}")

if __name__ == "__main__":
    test_semantic_gate()