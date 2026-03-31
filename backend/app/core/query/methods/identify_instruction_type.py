from .._shared import *


class _IdentifyInstructionTypeMixin:
    def _identify_instruction_type(self, query: str) -> str:
        """
        识别指令类型
        
        Args:
            query: 查询文本
            
        Returns:
            指令类型: "resource_retrieval", "content_generation", 或空字符串
        """
        # 优先识别资源获取类指令
        for keyword in self.instruction_words["resource_retrieval"]:
            if keyword in query:
                logger.info(f"识别到资源获取指令: {keyword}")
                return "resource_retrieval"
        
        # 然后识别内容生成类指令
        for keyword in self.instruction_words["content_generation"]:
            if keyword in query:
                logger.info(f"识别到内容生成指令: {keyword}")
                return "content_generation"
        
        # 没有识别到明确指令
        return ""
