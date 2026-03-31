from .._shared import *


class _ExtractTopicAfterInstructionMixin:
    def _extract_topic_after_instruction(self, query: str, instruction_type: str) -> str:
        """
        提取指令词后的主题
        
        Args:
            query: 查询文本
            instruction_type: 指令类型
            
        Returns:
            提取的主题
        """
        # 移除指令词
        processed_query = query
        
        if instruction_type == "resource_retrieval":
            for keyword in self.instruction_words["resource_retrieval"]:
                if keyword in processed_query:
                    processed_query = processed_query.replace(keyword, "").strip()
        elif instruction_type == "content_generation":
            for keyword in self.instruction_words["content_generation"]:
                if keyword in processed_query:
                    processed_query = processed_query.replace(keyword, "").strip()
        
        # 提取完整主题
        complete_theme = self._extract_complete_theme(processed_query)
        if complete_theme:
            return complete_theme
        
        # 如果没有完整主题，提取核心概念
        concepts = self._extract_core_concepts(processed_query)
        if concepts:
            return concepts[0]
        
        return ""
