from .._shared import *


class _BuildMixin:
    def build(self, state: Any) -> str:
        """
        构建最终响应
        
        Args:
            state: 状态对象，包含意图、教案、建议等（可以是 MathAgentState 对象或字典）
        
        Returns:
            格式化的响应文本
        """
        print(f"\n====================================")
        print(f"📤 响应生成开始")
        
        # V33.0改进：记录开始时间
        self.start_time = time.time()
        
        try:
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 检查意图类型
            if hasattr(state, 'intent'):
                intent = state.intent
            else:
                intent = state.get("intent", "search")
            
            # 对于搜索意图，不使用已有的 response，而是重新构建响应
            # 这样可以确保使用最新的分层展示逻辑
            if intent == "search":
                print(f"🔀 搜索意图，重新构建响应以使用最新的分层展示逻辑")
                response = self._build_search_response(state)
                print(f"✅ 响应生成成功，长度: {len(response)}字符")
                return response
            
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 优先检查是否已经有响应（非搜索意图）
            response = self._get_state_value(state, "response", "")
            if response:
                print(f"🔀 发现已有响应，直接返回")
                print(f"✅ 响应生成成功，长度: {len(response)}字符")
                return response
            
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 检查是否有多个处理过的意图
            processed_intents = self._get_state_value(state, "processed_intents", [])
            
            if processed_intents and len(processed_intents) > 1:
                print(f"🎯 检测到多意图处理结果: {processed_intents}")
                response = self._build_multi_intent_response(state, processed_intents)
            else:
                # 单个意图处理
                if hasattr(state, 'intent'):
                    intent = state.intent
                else:
                    intent = state.get("intent", "search")
                print(f"🎯 单个意图: {intent}")
                
                if intent == "generate_lesson_plan":
                    response = self._build_lesson_plan_response(state)
                elif intent == "visualization":
                    response = self._build_visualization_response(state)
                else:
                    response = self._build_search_response(state)
            
            print(f"✅ 响应生成成功，长度: {len(response)}字符")
            
            return response
            
        except Exception as e:
            print(f"❌ 响应生成失败: {str(e)}")
            return self._get_error_response(str(e))
