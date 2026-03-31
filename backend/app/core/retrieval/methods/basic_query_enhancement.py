from .._shared import *


class _BasicQueryEnhancementMixin:
    def _basic_query_enhancement(self, query: str) -> str:
        """
        基础查询增强，处理常见的查询模式
        
        Args:
            query: 原始查询
            
        Returns:
            增强后的查询
        """
        enhanced_query = query
        
        # V52.0改进：将"例子"转换为"习题"
        if "例子" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '例子' -> '习题'")
        
        # V52.0改进：将"实例"转换为"习题"
        if "实例" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '实例' -> '习题'")
        
        # V52.0改进：将"案例"转换为"习题"
        if "案例" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '案例' -> '习题'")
        
        # V52.0改进：将"生活中应用"转换为"应用题"
        if "生活中应用" in query or "在生活中应用" in query:
            if "应用题" not in query:
                enhanced_query = enhanced_query + " 应用题"
                print(f"   🔍 V52.0基础增强: '生活中应用' -> '应用题'")
        
        # V52.0改进：将"实际应用"转换为"应用题"
        if "实际应用" in query and "应用题" not in query:
            enhanced_query = enhanced_query + " 应用题"
            print(f"   🔍 V52.0基础增强: '实际应用' -> '应用题'")
        
        # V52.0改进：将"实际问题的应用"转换为"应用题"
        if "实际问题的应用" in query or "实际问题的应用题" in query:
            if "应用题" not in query:
                enhanced_query = enhanced_query + " 应用题"
                print(f"   🔍 V52.0基础增强: '实际问题的应用' -> '应用题'")
        
        return enhanced_query
    
    # V51.0改进：动态调整检索数量
