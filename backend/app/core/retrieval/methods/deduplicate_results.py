from .._shared import *


class _DeduplicateResultsMixin:
    def _deduplicate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        对检索结果进行去重
        
        Args:
            results: 检索结果
        
        Returns:
            去重后的结果
        """
        deduplicated = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        seen_questions = set()
        
        print(f"   📊 开始去重，原始结果数量: {len(results['metadatas'][0])}")
        
        for i, meta in enumerate(results["metadatas"][0]):
            question = meta.get('题干', '') or results["documents"][0][i]
            # 使用题目内容的前150个字符作为去重依据，增加准确性
            question_key = question[:150].strip()
            
            if question_key not in seen_questions:
                seen_questions.add(question_key)
                deduplicated["documents"][0].append(results["documents"][0][i])
                deduplicated["metadatas"][0].append(meta)
                deduplicated["distances"][0].append(results["distances"][0][i])
                deduplicated["ids"][0].append(results["ids"][0][i])
            else:
                print(f"   ⚠️ 去重移除重复题目: {question[:50]}...")
        
        print(f"   📊 去重完成，剩余结果数量: {len(deduplicated['metadatas'][0])}")
        return deduplicated
