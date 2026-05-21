#!/usr/bin/env python3
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.model_config import ModelConfig

resource_type_hint = "包含"
can_extract_broad = "可以"

prompt = ChatPromptTemplate.from_messages([
    ("system", f"""你是一个高中数学主题识别专家。你的任务是从用户查询中提取核心数学主题，并判断每个主题属于函数、几何、概率统计、代数中的哪一个板块。

4个板块：函数、几何、概率统计、代数

规则：
1. 提取最具体、最细分的主题（例如："函数的单调性"比"函数"更具体）
2. 如果查询包含多个主题，用逗号分隔
3. 对于每个主题，判断其所属的板块，用冒号分隔主题和板块
4. 输出格式：主题1:板块1,主题2:板块2
5. 只返回主题和板块，不要解释，不要添加任何其他文字
6. 必须返回有效的主题和板块，不能返回空字符串
7. 重要：不要提取过于宽泛的主题，如单独的"函数"、"数学"等，除非查询包含资源类型词（如"选择题"、"习题"等）或有明确的查询意图
8. 重要：忽略查询中的修饰词，如"基础一点的"、"中等难度的"、"高二的"、"难一点的"等，只提取核心数学主题
9. 重要：充分发挥你的数学知识判断能力，将知识点归入最合适的板块

示例：
- 输入："关于函数单调性的教案" -> 输出："函数的单调性:函数"
- 输入："给我找一些三角函数诱导公式的习题" -> 输出："诱导公式:函数"
- 输入："指数函数和对数函数的教案" -> 输出："指数函数:函数,对数函数:函数"
- 输入："平面的教案" -> 输出："平面:几何"
- 输入："空间点的教案" -> 输出："空间点:几何"
- 输入："关于分层抽样的教案" -> 输出："分层抽样:概率统计"
- 输入："复数的教案" -> 输出："复数:代数"
- 输入："分类加法计数原理的练习课课件" -> 输出："分类加法计数原理:概率统计"
- 输入："立体几何练习题" -> 输出："立体几何:几何"

附加信息：原始查询{resource_type_hint}资源类型词，因此{can_extract_broad}提取通用主题如"函数"作为核心主题。"""),
    ("user", "用户查询：{query}\n\n请提取核心主题和所属板块（格式：主题1:板块1,主题2:板块2）：")
])

model_config = ModelConfig()
model = model_config.get_model("intent")
chain = prompt | model | StrOutputParser()

query = "找一下关于分类加法计数原理的练习课课件"
result = chain.invoke({"query": query})
print("查询:", query)
print("LLM输出:", result)