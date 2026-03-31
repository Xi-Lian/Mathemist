from .._shared import *


class _GenerateQueryEmbeddingMixin:
    def _generate_query_embedding(self, query: str, embedding_model) -> List[float]:
        """
        生成查询的向量表示
        
        Args:
            query: 查询文本
            embedding_model: Embedding模型
        
        Returns:
            查询向量
        """
        query_embedding = embedding_model.encode(
            [query], 
            normalize_embeddings=True
        ).tolist()
        
        print(f"📊 查询向量维度: {len(query_embedding[0])}")
        
        return query_embedding
