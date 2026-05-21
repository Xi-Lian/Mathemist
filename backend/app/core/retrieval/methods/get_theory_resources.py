from .._shared import *


class _GetTheoryResourcesMixin:
    def get_theory_resources(self) -> List[Dict[str, Any]]:
        """
        获取所有理论资源（用于教案生成）
        
        Returns:
            理论资源列表
        """
        try:
            # 获取客户端
            client = self.vector_db_builder.get_chroma_client()
            # 理论资源属于通用板块，从math_resources_general集合中获取
            collection = client.get_collection(name="math_resources_general")
            
            # 查询所有理论资源
            results = collection.get(
                where={"resource_type": "theory"},
                include=["documents", "metadatas"]
            )
            
            theory_resources = []
            
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                
                resource = {
                    "title": metadata.get('title', ''),
                    "content": doc,
                    "source": metadata.get('source_file', ''),
                    "metadata": metadata
                }
                
                theory_resources.append(resource)
            
            return theory_resources
            
        except Exception as e:
            print(f"❌ 获取理论资源失败: {str(e)}")
            return []


# 向后兼容的函数接口
