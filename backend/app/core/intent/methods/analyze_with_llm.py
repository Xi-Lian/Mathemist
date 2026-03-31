from .._shared import *


class _AnalyzeWithLlmMixin:
    def _analyze_with_llm(self, user_input: str) -> Dict[str, Any]:
        """
        使用LLM进行意图理解
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图分析结果
        """
        print("🤖 调用DeepSeek模型进行意图理解...")
        
        # 获取模型
        model = self.model_config.get_model("intent")
        
        # 构建链
        chain = self.prompt_template | model | StrOutputParser()
        
        # 调用模型
        model_response = chain.invoke({"user_input": user_input})
        
        print(f"🤖 模型响应: {model_response}")
        
        # 解析模型响应
        return self._parse_llm_response(model_response)
