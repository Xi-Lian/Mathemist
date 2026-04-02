from .._shared import *


class _CreatePromptTemplateMixin:
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建意图理解的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template(
            """
你是高中数学助手的意图分类器。只做分类，不做解释。

可选 primary_intent 只有 4 个：
- search
- generate_lesson_plan
- visualization
- conversation

资源类型只允许从下面选择，未明确提到就返回空数组：
["习题", "教案", "课件", "课例", "GGB", "教学大纲", "资料"]

判定规则：
- 用户在“找/要/给我/推荐/有没有/来几道/来一些”已有资源，判为 search。
- 用户只说“主题 + 资源类型”，例如“对数教案”“二次函数习题”，默认判为 search。
- 用户明确要求“生成/设计/编写/写一份”教案或教学方案，判为 generate_lesson_plan。
- 用户明确要求 GeoGebra、GGB、动态图、可视化设计，判为 visualization。
- 用户是在打招呼、确认、追问能力边界，或者只给出一个模糊主题但还没说明要搜资源/生成教案/做可视化，判为 conversation。
- 不要过度推断资源类型。

严格要求：
- 只输出一个 JSON 对象
- 不要输出代码块
- 不要输出额外解释

输出格式：
{{
  "primary_intent": "search",
  "user_needs": "一句话描述用户需求",
  "resource_types": ["习题"],
  "intents": [
    {{"type": "search", "confidence": 0.95}},
    {{"type": "generate_lesson_plan", "confidence": 0.10}},
    {{"type": "visualization", "confidence": 0.10}},
    {{"type": "conversation", "confidence": 0.10}}
  ]
}}

示例：
用户输入：查找指数函数习题
输出：{{"primary_intent":"search","user_needs":"用户想要查找指数函数相关的习题资源","resource_types":["习题"],"intents":[{{"type":"search","confidence":0.95}},{{"type":"generate_lesson_plan","confidence":0.10}},{{"type":"visualization","confidence":0.10}},{{"type":"conversation","confidence":0.10}}]}}

用户输入：对数教案
输出：{{"primary_intent":"search","user_needs":"用户想要查找教案相关的资源","resource_types":["教案"],"intents":[{{"type":"search","confidence":0.95}},{{"type":"generate_lesson_plan","confidence":0.15}},{{"type":"visualization","confidence":0.10}},{{"type":"conversation","confidence":0.10}}]}}

用户输入：生成指数函数的教案
输出：{{"primary_intent":"generate_lesson_plan","user_needs":"用户想要生成指数函数教案","resource_types":["教案"],"intents":[{{"type":"generate_lesson_plan","confidence":0.95}},{{"type":"search","confidence":0.20}},{{"type":"visualization","confidence":0.10}},{{"type":"conversation","confidence":0.05}}]}}

用户输入：生成二次函数的GGB动态图设计
输出：{{"primary_intent":"visualization","user_needs":"用户想要生成二次函数的GGB动态图设计建议","resource_types":["GGB"],"intents":[{{"type":"visualization","confidence":0.95}},{{"type":"search","confidence":0.20}},{{"type":"generate_lesson_plan","confidence":0.10}},{{"type":"conversation","confidence":0.05}}]}}

用户输入：你好
输出：{{"primary_intent":"conversation","user_needs":"用户在进行问候或闲聊","resource_types":[],"intents":[{{"type":"conversation","confidence":0.95}},{{"type":"search","confidence":0.10}},{{"type":"generate_lesson_plan","confidence":0.05}},{{"type":"visualization","confidence":0.05}}]}}

用户输入：对数
输出：{{"primary_intent":"conversation","user_needs":"用户只给出了模糊主题，需要先确认是搜资源、生成教案还是做可视化","resource_types":[],"intents":[{{"type":"conversation","confidence":0.90}},{{"type":"search","confidence":0.35}},{{"type":"generate_lesson_plan","confidence":0.20}},{{"type":"visualization","confidence":0.10}}]}}

用户输入：{user_input}
"""
        )


# 向后兼容的函数接口
