from .._shared import *
import json


class _ExtractQueryContextWithLlmMixin:
    def __init__(self):
        super().__init__()
        self._query_context_cache = {}
        self._cache_size_limit = 100

    def _extract_resource_types_from_query(self, query: str) -> List[str]:
        resource_type_keywords = {
            "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课"],
            "课件": ["课件", "PPT", "幻灯片", "演示文稿"],
            "习题": ["习题", "题目", "练习题", "试题", "测试题"],
            "课例": ["课例", "教学视频", "课堂实录", "视频", "微课", "优质课"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "几何画板"],
            "教学大纲": ["教学大纲", "大纲", "课程标准"]
        }

        resource_types = []
        for resource_type, keywords in resource_type_keywords.items():
            if any(kw in query for kw in keywords):
                resource_types.append(resource_type)

        return resource_types

    def _extract_query_context_with_llm(self, query: str) -> Dict[str, Any]:
        query_key = query.strip()
        if query_key in self._query_context_cache:
            print(f"✅ 命中查询理解缓存: '{query_key}'")
            return self._query_context_cache[query_key]

        pre_extracted_resource_types = self._extract_resource_types_from_query(query)
        print(f"🔍 预提取资源类型: {pre_extracted_resource_types}")

        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        system_prompt = """你是一个高中数学教育资源查询理解专家。你的任务是从用户查询中全面提取所有相关信息，包括知识点、板块信息和资源类型等。

【重要】你必须返回一个完整的JSON对象，包含以下所有字段，每个字段都必须有值（如果是空的就返回空字符串或空列表）。

返回格式要求：
1. knowledge_points: 知识点列表（可以多个，用逗号分隔的字符串），提取最具体、最细分的知识点
2. board: 板块名称，必须从"代数"、"几何"、"函数"、"概率统计"中选择一个，不要返回"通用"或空字符串
3. resource_types: 资源类型列表，如["教案", "课件", "习题"]等
4. intent: 查询意图，如"学习"、"教学"、"练习"、"复习"、"比较"等
5. difficulty: 难度要求，"基础"、"中等"、"拔高"或空字符串
6. grade: 年级信息，"高一"、"高二"、"高三"或空字符串
7. exam_form: 考查形式，如"计算"、"证明"、"应用"等或空字符串
8. quantity: 数量要求，整数或0（表示无指定）
9. exclude_keywords: 需要排除的关键词列表，如["平面向量"]，用于排除用户明确表示不需要的资源特征
10. content_requirement: 用户是否对资源内容有具体要求，true或false（见下方详细说明）
11. reasoning: 你的推理过程（用于调试）

【关键】板块识别规则：
- 代数：复数、虚数、数系的扩充、一元二次方程（初中）、因式分解、整式等
- 几何：立体几何、平面几何、解析几何、三角形、圆、椭圆、双曲线、抛物线、向量（平面向量/空间向量）、立体几何初步、空间直线、空间平面、二面角等
- 函数：函数、指数函数、对数函数、三角函数、幂函数、函数的单调性、函数的奇偶性等
- 概率统计：概率、统计、随机抽样、分层抽样、古典概型、排列组合等

特别注意：
- "复数的几何意义"是代数板块，不是几何板块（复数属于代数）
- "平面向量"是几何板块（因为向量是几何的重要内容）
- "空间向量与立体几何"是几何板块
- 如果查询中同时提到代数和几何相关内容，以主要讨论的内容为准

知识点识别规则：
1. 根据用户的查询内容，自己理解和识别知识点，不需要依赖预定义列表
2. 如果查询包含多个知识点，全部提取，不要遗漏任何一个知识点，用逗号分隔
3. 知识点应该简洁明了，如"分层抽样"、"函数的单调性"、"二次函数"、"空间直线"、"空间点"等
4. 几何相关知识点可能包括：立体几何、空间点、空间点线面、空间直线、空间平面、二面角、空间几何体、圆锥、圆锥曲线、椭圆、双曲线、抛物线、平面向量、空间向量等（以上只是示例，不要局限于这些）
5. 只要查询中有明确的主题或概念，都应该识别为知识点
6. 如果查询是"空间直线的教案"，知识点应该是"空间直线"
7. 如果查询是"空间点的教案"，知识点应该是"空间点"
8. 如果查询是"圆锥的课件"，知识点应该是"圆锥"

资源类型识别：
1. 教案、教学设计、教学方案 -> ["教案"]
2. 课件、PPT、幻灯片 -> ["课件"]
3. 习题、题目、练习题、测试题 -> ["习题"]
4. 课例、教学视频、课堂实录 -> ["课例"]
5. GGB、GeoGebra、动态图、ggb文件、ggb、ggb资源 -> ["GGB"]
6. 教学大纲、大纲、课程标准 -> ["教学大纲"]
7. 如果查询包含多个资源类型，全部提取，如"请找一下关于复数的教案和课件"，资源类型应该是["教案", "课件"]
8. 如果查询是"帮我找一下关于二次函数的教案和课件"，资源类型应该是["教案", "课件"]
9. 如果查询是"想要关于立体几何的GGB和教案"，资源类型应该是["GGB", "教案"]
10. 如果没有指定资源类型，返回空列表[]

意图识别：
1. 学习、了解、掌握、理解 -> "学习"
2. 教学、教案、课件 -> "教学"
3. 练习、习题、题目 -> "练习"
4. 复习、巩固、回顾 -> "复习"
5. 比较、对比、区别 -> "比较"
6. 备考、冲刺、模拟 -> "备考"

【重要】实际应用识别：
当查询中包含"应用"、"实际"、"建模"、"实际问题"等关键词时，需要特别注意区分：

1. **纯数学概念** vs **实际应用**：
   - "函数解析式"（纯数学）→ knowledge_points: "函数解析式;换元法;待定系数法"
   - "函数解析式的应用"或"函数的实际应用"（实际应用）→ knowledge_points: "函数建模;实际问题;函数应用"

2. **识别规则**：
   - 如果查询包含"应用"、"实际"、"建模"、"实际问题"、"现实问题"等词 → 优先返回包含"应用"、"建模"、"实际问题"知识点的资源
   - 例如："函数解析式的实际应用" → knowledge_points: "函数建模;实际问题", reasoning: "用户想要的是函数在实际问题中的应用题目，即建立函数模型解决实际问题的题目"
   - 例如："三角函数的应用" → knowledge_points: "三角函数建模;物理应用", reasoning: "用户想要的是三角函数在物理、工程等实际问题中的应用"
   - 例如："二次函数的实际应用" → knowledge_points: "二次函数建模;最值问题;实际问题", reasoning: "用户想要的是二次函数在实际问题（如利润最大化、面积优化等）中的应用"

3. **常见应用场景**：
   - 物理应用：弹簧振动、交流电、运动学等
   - 经济应用：利润最大化、成本最小化、销售问题等
   - 几何应用：面积优化、体积计算、建筑设计等
   - 生活应用：行程问题、工程问题、人口增长等

内容要求识别（content_requirement）：
用户是否对资源内容有具体要求，true表示是，false表示否。

以下情况应该返回true：
1. 用户明确提到需要内容详细、完整、具体，如"详细的内容"、"完整的教案"、"具体的教学过程"等
2. 用户要求内容包含特定元素，如"包含教学目标"、"包含例题"、"包含练习题"等
3. 用户强调要"看内容"或"查看文件"等，表明关注内容本身
4. 习题类查询，用户要求特定类型的题目，如"计算题"、"证明题"、"解答题"等

以下情况应该返回false：
1. 用户只是简单地查找资源，如"找一下xxx的教案"
2. 用户关注的是资源类型而非内容本身，如"想要教案"、"需要课件"
3. 用户没有明确提出内容方面的要求

否定条件识别：
如果查询中包含"不要"、"不是"、"排除"、"不包括"、"剔除"、"过滤"等否定词，需要识别用户不希望出现的资源特征。
- 例如："要平面的教案，不要平面向量" -> exclude_keywords: ["平面向量"]
- 例如："想要关于椭圆的教案，但不是平面向量的" -> exclude_keywords: ["平面向量"]
- 例如："排除立体几何中的平面向量" -> exclude_keywords: ["平面向量"]

难度识别：
1. 基础、简单、容易、入门 -> "基础"
2. 中等、一般、常见、适中 -> "中等"
3. 拔高、难、困难、挑战、压轴、复杂 -> "拔高"  # 【V107.0新增】"复杂"映射到拔高难度

年级识别：
1. 高一、高一上、高一下、高中一年级 -> "高一"
2. 高二、高二上、高二下、高中二年级 -> "高二"
3. 高三、高三上、高三下、高中三年级 -> "高三"

数量识别：
1. "几道"、"一些"、"几个" -> 5
2. "10道"、"5题" -> 10、5
3. 如果没有指定数量 -> 0

【预提取信息】
已预提取资源类型: {pre_extracted_resource_types}，请在此基础上进行确认和补充。

示例：
输入："帮我找一下关于分层抽样的教案"
输出：{{"knowledge_points": "分层抽样", "board": "概率统计", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "reasoning": "查询中提到了'分层抽样'这是知识点，属于概率统计板块，'教案'是资源类型，'帮我找'表明是教学意图，用户没有对内容有具体要求"}}

输入："请找一下关于复数的几何意义的教案"
输出：{{"knowledge_points": "复数的几何意义", "board": "代数", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "reasoning": "查询中提到了'复数的几何意义'这是知识点，复数属于代数板块，'教案'是资源类型，'请找一下'表明是教学意图，用户没有对内容有具体要求"}}

输入："想要关于空间直线的教案"
输出：{{"knowledge_points": "空间直线", "board": "几何", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "reasoning": "查询中提到了'空间直线'这是知识点，属于几何板块，'教案'是资源类型，'想要'表明是教学意图，用户没有对内容有具体要求"}}

输入："想要更多的关于平面的教案，不要平面向量的教案"
输出：{{"knowledge_points": "平面", "board": "几何", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "exclude_keywords": ["平面向量"], "reasoning": "查询中提到了'平面'这是知识点，属于几何板块，'教案'是资源类型，'想要'表明是教学意图，'不要平面向量'表明需要排除'平面向量'相关的资源，用户没有对内容有具体要求"}}

输入："请找一下内容详细的二次函数教案"
输出：{{"knowledge_points": "二次函数", "board": "函数", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'二次函数'这是知识点，属于函数板块，'教案'是资源类型，'内容详细'表明用户对内容有具体要求"}}

输入："请找一下关于二次函数和指数函数的课件"
输出：{{"knowledge_points": "二次函数,指数函数", "board": "函数", "resource_types": ["课件"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "exclude_keywords": [], "reasoning": "查询中提到了'二次函数'和'指数函数'两个知识点，都属于函数板块，'课件'是资源类型，'帮我找'表明是教学意图，用户没有对内容有具体要求"}}

输入："想要关于立体几何和空间向量的教案和GGB"
输出：{{"knowledge_points": "立体几何,空间向量", "board": "几何", "resource_types": ["教案", "GGB"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "exclude_keywords": [], "reasoning": "查询中提到了'立体几何'和'空间向量'两个知识点，都属于几何板块，'教案'和'GGB'是资源类型，'想要'表明是教学意图，用户没有对内容有具体要求"}}

输入："高一基础难度的三角函数练习题"
输出：{{"knowledge_points": "三角函数", "board": "函数", "resource_types": ["习题"], "intent": "练习", "difficulty": "基础", "grade": "高一", "exam_form": "", "quantity": 0, "content_requirement": false, "reasoning": "查询中提到了'三角函数'这是知识点，属于函数板块，'练习题'是资源类型，'练习'表明是练习意图，'基础'是难度要求，'高一'是年级信息，用户没有对习题的具体内容有要求"}}

输入："高二中等难度的圆锥曲线证明题"
输出：{{"knowledge_points": "圆锥曲线", "board": "几何", "resource_types": ["习题"], "intent": "练习", "difficulty": "中等", "grade": "高二", "exam_form": "证明", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'圆锥曲线'这是知识点，属于几何板块，'证明题'是资源类型和考查形式，'练习'表明是练习意图，'中等'是难度要求，'高二'是年级信息，'证明题'表明用户对习题的具体类型有要求"}}

输入："请找一下包含教学目标的平面向量教案"
输出：{{"knowledge_points": "平面向量", "board": "几何", "resource_types": ["教案"], "intent": "教学", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'平面向量'这是知识点，属于几何板块，'教案'是资源类型，'包含教学目标'表明用户对教案的具体内容有要求"}}

输入："我想要详细的平面向量学习内容"
输出：{{"knowledge_points": "平面向量", "board": "几何", "resource_types": [], "intent": "学习", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'平面向量'这是知识点，属于几何板块，'学习'表明是学习意图，'详细的'和'学习内容'表明用户对内容的详细程度有具体要求"}}

输入：“查看一下空间点的相关内容”
输出：{{"knowledge_points": "空间点", "board": "几何", "resource_types": [], "intent": "学习", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'空间点'这是知识点，属于几何板块，'查看'和'相关内容'表明用户想要查看具体的相关内容，对内容有要求"}}

输入：“找一下比较复杂的余弦函数的题目”
输出：{{"knowledge_points": "余弦函数", "board": "函数", "resource_types": ["习题"], "intent": "练习", "difficulty": "拔高", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": false, "reasoning": "查询中提到了'余弦函数'这是知识点，属于函数板块，'题目'是资源类型（习题），'练习'表明是练习意图，'复杂'是难度要求，映射为'拔高'难度，用户没有对习题的具体内容有要求"}}

输入：“我想要函数解析式的实际应用的题目”
输出：{{"knowledge_points": "函数建模;实际问题;函数应用", "board": "函数", "resource_types": ["习题"], "intent": "练习", "difficulty": "", "grade": "", "exam_form": "", "quantity": 0, "content_requirement": true, "reasoning": "查询中提到了'函数解析式的实际应用'，这是指函数在实际问题中的应用，即建立函数模型解决实际问题的题目，如利润最大化、面积优化等应用题，而不是纯数学的函数解析式求解（如换元法、待定系数法等）。用户想要的是包含'应用'、'建模'、'实际问题'知识点的习题。"}}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "用户查询：{query}\n\n请提取完整的查询上下文信息（返回JSON格式）：")
        ])

        model = self.model_config.get_model("intent")
        chain = prompt | model | JsonOutputParser()

        try:
            result = chain.invoke({"query": query, "pre_extracted_resource_types": pre_extracted_resource_types})
            print(f"🤖 LLM查询理解结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

            if len(self._query_context_cache) >= self._cache_size_limit:
                oldest_key = next(iter(self._query_context_cache))
                del self._query_context_cache[oldest_key]
            self._query_context_cache[query_key] = result

            return result
        except Exception as e:
            print(f"❌ LLM查询理解失败: {e}")
            import traceback
            traceback.print_exc()
            raise