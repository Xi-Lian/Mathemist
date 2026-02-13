import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from .state import MathAgentState
import chromadb
from sentence_transformers import SentenceTransformer
from .smart_content_processor import SmartContentProcessor

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_MODEL = "deepseek-chat"

# 初始化DeepSeek模型
try:
    deepseek_llm = ChatDeepSeek(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        temperature=0.3,
        max_tokens=2000
    )
except Exception as e:
    print(f"警告：DeepSeek模型初始化失败: {e}")
    deepseek_llm = None

# 初始化ChromaDB和embedding模型（全局单例）
_chroma_client = None
_embedding_model = None
_content_processor = None

def get_chroma_client():
    """获取ChromaDB客户端（单例模式）"""
    global _chroma_client
    if _chroma_client is None:
        SCRIPT_DIR = Path(__file__).parent.parent.parent
        CHROMA_DB_DIR = SCRIPT_DIR / "backend" / "chroma_db"
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return _chroma_client

def get_content_processor():
    """获取智能内容处理器（单例模式）"""
    global _content_processor
    if _content_processor is None:
        _content_processor = SmartContentProcessor()
    return _content_processor

def get_embedding_model():
    """获取embedding模型（单例模式）"""
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(r"C:\Users\15137\.cache\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\snapshots\e8f8c211226b894fcb81acc59f3b34ba3efd5f42")
        except Exception as e:
            print(f"警告：Embedding模型初始化失败: {e}")
            raise ValueError(f"Embedding模型初始化失败: {e}")
    return _embedding_model

# 模型选择函数
def get_model(task_type: str = "default"):
    """
    根据任务类型选择合适的模型
    
    Args:
        task_type: 任务类型，可选值：intent（意图理解）、lesson_plan（教案生成）、visualization（可视化建议）
    
    Returns:
        选择的语言模型
    """
    # 统一使用DeepSeek模型
    if deepseek_llm is None:
        raise ValueError("DeepSeek模型未初始化，请检查API密钥配置")
    return deepseek_llm

# 意图理解提示词
intent_prompt = ChatPromptTemplate.from_template("""
你是一个高中数学教育智能助手的意图理解模块。

请分析用户的输入，判断用户的意图类型：
1. search: 用户想要搜索数学资源、习题、知识点等（不包含教案生成）
2. generate_lesson_plan: 用户想要生成教案、教学设计，或者查找教案资源
3. visualization: 用户想要获取可视化设计建议、GGB动态数学设计

用户输入：{user_input}

请仅输出一个单词，表示意图类型：search、generate_lesson_plan或visualization

注意：如果用户输入中包含"教案"、"教学设计"、"查找资源"等关键词，应该识别为 generate_lesson_plan。
""")

# 教案生成提示词
lesson_plan_prompt = ChatPromptTemplate.from_template("""
你是一个专业的高中数学教学设计专家。

请根据用户需求、检索到的理论依据和优秀教案共性，生成一个完整的高中数学教案。

用户需求：{user_input}

检索到的教育理论：
{theory_resources}

优秀教案的共性特征：
{lesson_plan_patterns}

教案要求：
1. 包含教学目标、教学重难点、教学方法
2. 包含详细的教学过程（引入、探究、应用、总结）
3. 包含师生活动设计
4. 包含GGB动态数学设计应用点
5. 提供理论依据支持（基于检索到的教育理论）
6. 符合高中学数学教学大纲要求
7. 参考优秀教案的共性特征
8. **重要要求**：在教案的每个相关环节，明确标注使用了哪些理论依据，格式为[理论卡片X：理论名称]，例如[理论卡片一：建构主义学习理论]
9. 在教案结尾处，添加一个"理论依据使用总结"部分，列出本教案使用的所有理论依据及其应用场景

请生成一个结构清晰、内容详实的教案。
""")

# 可视化设计建议提示词
visualization_prompt = ChatPromptTemplate.from_template("""
你是一个专业的GGB动态数学设计专家。

请根据用户需求和检索到的优秀设计示例，提供专业的GGB动态数学设计建议。

用户需求：{user_input}

检索到的优秀设计示例：
{visualization_examples}

可视化设计建议要求：
1. 设计核心思想
2. GGB构建步骤
3. 交互性设计
4. 教学应用场景
5. 预期教学效果
6. 参考检索到的优秀设计示例进行泛化

请提供专业、详细且可操作的可视化设计建议。
""")

def classify_resource(source: str, content: str) -> str:
    """
    根据文件路径和内容智能分类资源
    
    Args:
        source: 文件路径
        content: 文件内容
    
    Returns:
        资源类型: "lesson_plan", "visualization", "exercise", "theory"
    """
    # 确保 source 和 content 不是 None
    if source is None:
        source = ""
    if content is None:
        content = ""
    
    source_lower = source.lower()
    content_lower = content.lower()
    
    # 优先识别理论卡片
    if "理论卡片" in content or "核心观点" in content or "教学启发" in content:
        return "theory"
    
    # 教案相关关键词
    lesson_plan_keywords = [
        "教案", "教学设计", "导学案", "说课稿",
        "lesson", "teaching", "design"
    ]
    
    # 教学大纲相关关键词（单独识别）
    syllabus_keywords = [
        "教学大纲", "syllabus", "课程标准", "课程大纲"
    ]
    
    # 课件相关关键词
    courseware_keywords = [
        "课件", "ppt", "pptx", "演示文稿", "slides",
        "courseware", "presentation"
    ]
    
    # 课例相关关键词
    lesson_case_keywords = [
        "课例", "课堂实录", "教学视频", "教学案例",
        "lesson case", "classroom", "video"
    ]
    
    # GGB相关关键词
    ggb_keywords = [
        "ggb", "geogebra", ".ggb", "动态数学",
        "geogebra"
    ]
    
    # 可视化相关关键词
    visualization_keywords = [
        "可视化", "动态", "图象", "图像",
        "visualization", "dynamic", "graph", "plot"
    ]
    
    # 习题相关关键词
    exercise_keywords = [
        "习题", "练习", "题目", "答案", "试题",
        "exercise", "practice", "problem", "answer", "question"
    ]
    
    # 统计各类型的关键词匹配数
    lesson_plan_score = sum(1 for kw in lesson_plan_keywords if kw in source_lower or kw in content_lower)
    syllabus_score = sum(1 for kw in syllabus_keywords if kw in source_lower or kw in content_lower)
    courseware_score = sum(1 for kw in courseware_keywords if kw in source_lower or kw in content_lower)
    lesson_case_score = sum(1 for kw in lesson_case_keywords if kw in source_lower or kw in content_lower)
    ggb_score = sum(1 for kw in ggb_keywords if kw in source_lower or kw in content_lower)
    visualization_score = sum(1 for kw in visualization_keywords if kw in source_lower or kw in content_lower)
    exercise_score = sum(1 for kw in exercise_keywords if kw in source_lower or kw in content_lower)
    
    # 根据得分判断类型
    scores = {
        "lesson_plan": lesson_plan_score,
        "syllabus": syllabus_score,
        "courseware": courseware_score,
        "lesson_case": lesson_case_score,
        "ggb": ggb_score,
        "visualization": visualization_score,
        "exercise": exercise_score
    }
    
    max_score = max(scores.values())
    
    if max_score == 0:
        return "theory"
    
    # 返回得分最高的类型
    for resource_type, score in scores.items():
        if score == max_score and score > 0:
            return resource_type
    
    # 默认返回theory
    return "theory"

# 资源检索函数（使用ChromaDB进行语义检索）
def retrieve_resources(query: str, intent: str) -> Dict[str, Any]:
    """
    根据查询和意图检索相关资源
    使用ChromaDB进行语义检索
    
    Args:
        query: 用户查询
        intent: 用户意图
    
    Returns:
        检索结果字典，包含理论依据、教案共性、可视化示例等
    """
    try:
        print(f"🔍 retrieve_resources 开始")
        print(f"📝 查询: {query}")
        print(f"🎯 意图: {intent}")
        
        SCRIPT_DIR = Path(__file__).parent.parent.parent
        CHROMA_DB_DIR = SCRIPT_DIR / "backend" / "chroma_db"
        COLLECTION_NAME = "knowledge_base"
        
        print(f"📁 ChromaDB 路径: {CHROMA_DB_DIR}")
        
        if not os.path.exists(CHROMA_DB_DIR):
            print(f"⚠️  ChromaDB数据库不存在，请先运行 python backend/scripts/ingest.py 构建知识库")
            return {
                "theory_resources": [],
                "lesson_plan_patterns": [],
                "visualization_examples": [],
                "general_resources": []
            }
        
        client = get_chroma_client()
        print(f"🔗 ChromaDB 客户端: {type(client).__name__}")
        
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"📚 集合: {COLLECTION_NAME}")
        
        model = get_embedding_model()
        print(f"🤖 Embedding 模型: {type(model).__name__}")
        
        query_embedding = model.encode([query], normalize_embeddings=True).tolist()
        print(f"📊 查询向量维度: {len(query_embedding[0])}")
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=20,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"📦 查询结果: {results}")
        
        theory_resources = []
        lesson_plan_patterns = []
        visualization_examples = []
        general_resources = []
        courseware_resources = []
        lesson_case_resources = []
        ggb_resources = []
        syllabus_resources = []
        exercise_resources = []
        
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] and i < len(results["metadatas"][0]) else {}
                source = metadata.get("source", "")
                distance = results["distances"][0][i] if results["distances"] and results["distances"][0] and i < len(results["distances"][0]) else 0
                
                resource = {
                    "title": Path(source).stem if source else "未知",
                    "content": doc,
                    "source": source,
                    "relevance": 1 - distance
                }
                
                # 使用智能分类函数
                resource_type = classify_resource(source, doc)
                
                if resource_type == "lesson_plan":
                    lesson_plan_patterns.append(resource)
                elif resource_type == "visualization":
                    visualization_examples.append(resource)
                elif resource_type == "exercise":
                    exercise_resources.append(resource)
                elif resource_type == "courseware":
                    courseware_resources.append(resource)
                elif resource_type == "lesson_case":
                    lesson_case_resources.append(resource)
                elif resource_type == "ggb":
                    ggb_resources.append(resource)
                elif resource_type == "syllabus":
                    syllabus_resources.append(resource)
                else:
                    theory_resources.append(resource)
        
        print(f"✅ 检索完成: 理论资源{len(theory_resources)}条, 教案{len(lesson_plan_patterns)}条, 习题{len(exercise_resources)}条, 可视化{len(visualization_examples)}条, 通用{len(general_resources)}条, 课件{len(courseware_resources)}条, 课例{len(lesson_case_resources)}条, GGB{len(ggb_resources)}条, 教学大纲{len(syllabus_resources)}条")
        
        return {
            "theory_resources": theory_resources,
            "lesson_plan_patterns": lesson_plan_patterns,
            "exercise_resources": exercise_resources,
            "visualization_examples": visualization_examples,
            "general_resources": general_resources,
            "courseware_resources": courseware_resources,
            "lesson_case_resources": lesson_case_resources,
            "ggb_resources": ggb_resources,
            "syllabus_resources": syllabus_resources
        }
        
    except Exception as e:
        print(f"❌ 资源检索失败: {str(e)}")
        return {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "visualization_examples": [],
            "general_resources": []
        }

# 意图理解节点
def intent_understanding_node(state: MathAgentState) -> Dict[str, Any]:
    """
    意图理解节点
    分析用户输入，确定用户意图
    """
    try:
        # 确保 user_input 存在
        user_input = ""
        if hasattr(state, 'user_input'):
            user_input = getattr(state, 'user_input', '')
        elif isinstance(state, dict):
            user_input = state.get('user_input', '')
        
        # 确保 user_input 是字符串
        user_input = str(user_input) if user_input else ''
        
        print(f"\n====================================")
        print(f"🔍 意图理解节点开始")
        print(f"📝 用户输入: {user_input}")
        print(f"📋 state 类型: {type(state)}")
        print(f"📋 state 内容: {state}")
        
        if not user_input:
            print("⚠️ 用户输入为空，使用默认意图")
            return {
                "intent": "search",
                "intents": [{"type": "search", "confidence": 1.0}],
                "current_step": "intent_understanding",
                "error": "用户输入为空"
            }
        
        # 使用DeepSeek模型进行意图理解
        print("🤖 调用DeepSeek模型进行意图理解...")
        model = get_model("intent")
        
        # 构建提示词，让模型返回1个或多个意图
        
        intent_prompt = ChatPromptTemplate.from_template("""
你是一个高中数学教育智能助手的意图理解模块。

请分析用户的输入，判断用户可能的意图类型和置信度。
可能的意图类型包括：
1. search: 用户想要搜索数学资源、习题、知识点等
2. generate_lesson_plan: 用户想要生成教案、教学设计，或者查找教案资源
3. visualization: 用户想要获取可视化设计建议、GGB动态数学设计

用户输入：{user_input}

请输出一个JSON对象，包含以下字段：
- primary_intent: 主要意图
- intents: 一个数组，包含所有可能的意图及其置信度，格式为[{{"type": "意图类型", "confidence": 置信度}}]

示例输出：
{{"primary_intent": "generate_lesson_plan", "intents": [{{"type": "generate_lesson_plan", "confidence": 0.9}}, {{"type": "visualization", "confidence": 0.8}}, {{"type": "search", "confidence": 0.1}}]}}
""")
        
        # 构建链
        intent_chain = intent_prompt | model | StrOutputParser()
        
        # 调用模型
        model_response = intent_chain.invoke({"user_input": user_input})
        
        print(f"🤖 模型响应: {model_response}")
        
        # 解析模型响应
        import json
        try:
            parsed_response = json.loads(model_response)
            primary_intent = parsed_response.get("primary_intent", "search")
            intents = parsed_response.get("intents", [{"type": "search", "confidence": 1.0}])
            
            # 确保 intents 是一个列表
            if not isinstance(intents, list):
                intents = [{"type": "search", "confidence": 1.0}]
            
            print(f"✅ 意图理解成功")
            print(f"📋 主要意图: {primary_intent}")
            print(f"📋 所有意图: {intents}")
            
            return {
                "intent": primary_intent,
                "intents": intents,
                "current_step": "intent_understanding",
                "error": None
            }
        except json.JSONDecodeError:
            # 模型返回格式错误，使用关键词匹配作为备用
            print("⚠️ 模型返回格式错误，使用关键词匹配作为备用")
            user_input_lower = user_input.lower()
            
            # 检查是否包含教案相关关键词
            has_lesson_plan_keyword = any(keyword in user_input_lower for keyword in ["教案", "教学设计", "生成教案", "教学计划", "备课"])
            print(f"📋 包含教案关键词: {has_lesson_plan_keyword}")
            
            # 检查是否包含可视化相关关键词
            has_visualization_keyword = any(keyword in user_input_lower for keyword in ["ggb", "可视化", "动态数学", "几何画板", "图形设计"])
            print(f"📋 包含可视化关键词: {has_visualization_keyword}")
            
            # 确定意图
            if has_lesson_plan_keyword and has_visualization_keyword:
                print("✅ 同时包含教案和可视化关键词")
                return {
                    "intent": "generate_lesson_plan",
                    "intents": [
                        {"type": "generate_lesson_plan", "confidence": 0.9},
                        {"type": "visualization", "confidence": 0.8},
                        {"type": "search", "confidence": 0.1}
                    ],
                    "current_step": "intent_understanding",
                    "error": "模型返回格式错误，使用关键词匹配"
                }
            elif has_lesson_plan_keyword:
                print("✅ 只包含教案关键词")
                return {
                    "intent": "generate_lesson_plan",
                    "intents": [
                        {"type": "generate_lesson_plan", "confidence": 0.9},
                        {"type": "search", "confidence": 0.1},
                        {"type": "visualization", "confidence": 0.1}
                    ],
                    "current_step": "intent_understanding",
                    "error": "模型返回格式错误，使用关键词匹配"
                }
            elif has_visualization_keyword:
                print("✅ 只包含可视化关键词")
                return {
                    "intent": "visualization",
                    "intents": [
                        {"type": "visualization", "confidence": 0.9},
                        {"type": "search", "confidence": 0.1},
                        {"type": "generate_lesson_plan", "confidence": 0.1}
                    ],
                    "current_step": "intent_understanding",
                    "error": "模型返回格式错误，使用关键词匹配"
                }
            else:
                print("⚠️ 没有匹配关键词，使用默认意图")
                return {
                    "intent": "search",
                    "intents": [
                        {"type": "search", "confidence": 0.9},
                        {"type": "generate_lesson_plan", "confidence": 0.1},
                        {"type": "visualization", "confidence": 0.1}
                    ],
                    "current_step": "intent_understanding",
                    "error": "模型返回格式错误，使用关键词匹配"
                }
    except Exception as model_error:
        # 模型调用失败，使用关键词匹配作为备用
        print(f"❌ 模型调用失败: {str(model_error)}")
        print("🔄 使用关键词匹配作为备用")
        user_input = ""
        if hasattr(state, 'user_input'):
            user_input = getattr(state, 'user_input', '')
        elif isinstance(state, dict):
            user_input = state.get('user_input', '')
        
        # 确保 user_input 是字符串
        user_input = str(user_input) if user_input else ''
        
        user_input_lower = user_input.lower()
        
        # 检查是否包含教案相关关键词
        has_lesson_plan_keyword = any(keyword in user_input_lower for keyword in ["教案", "教学设计", "生成教案", "教学计划", "备课"])
        print(f"📋 包含教案关键词: {has_lesson_plan_keyword}")
        
        # 检查是否包含可视化相关关键词
        has_visualization_keyword = any(keyword in user_input_lower for keyword in ["ggb", "可视化", "动态数学", "几何画板", "图形设计"])
        print(f"📋 包含可视化关键词: {has_visualization_keyword}")
        
        # 确定意图
        if has_lesson_plan_keyword and has_visualization_keyword:
            print("✅ 同时包含教案和可视化关键词")
            return {
                "intent": "generate_lesson_plan",
                "intents": [
                    {"type": "generate_lesson_plan", "confidence": 0.9},
                    {"type": "visualization", "confidence": 0.8},
                    {"type": "search", "confidence": 0.1}
                ],
                "current_step": "intent_understanding",
                "error": "模型调用失败，使用关键词匹配"
            }
        elif has_lesson_plan_keyword:
            print("✅ 只包含教案关键词")
            return {
                "intent": "generate_lesson_plan",
                "intents": [
                    {"type": "generate_lesson_plan", "confidence": 0.9},
                    {"type": "search", "confidence": 0.1},
                    {"type": "visualization", "confidence": 0.1}
                ],
                "current_step": "intent_understanding",
                "error": "模型调用失败，使用关键词匹配"
            }
        elif has_visualization_keyword:
            print("✅ 只包含可视化关键词")
            return {
                "intent": "visualization",
                "intents": [
                    {"type": "visualization", "confidence": 0.9},
                    {"type": "search", "confidence": 0.1},
                    {"type": "generate_lesson_plan", "confidence": 0.1}
                ],
                "current_step": "intent_understanding",
                "error": "模型调用失败，使用关键词匹配"
            }
        else:
            print("⚠️ 没有匹配关键词，使用默认意图")
            return {
                "intent": "search",
                "intents": [
                    {"type": "search", "confidence": 0.9},
                    {"type": "generate_lesson_plan", "confidence": 0.1},
                    {"type": "visualization", "confidence": 0.1}
                ],
                "current_step": "intent_understanding",
                "error": "模型调用失败，使用关键词匹配"
            }
    except Exception as e:
        print(f"❌ 意图理解节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "intent": "search",
            "intents": [{"type": "search", "confidence": 1.0}],
            "current_step": "intent_understanding",
            "error": f"意图理解失败: {str(e)}"
        }

# 资源检索节点
def resource_retrieval_node(state: MathAgentState) -> Dict[str, Any]:
    """
    资源检索节点
    根据用户意图和输入检索相关资源
    """
    try:
        # 确保 user_input 和 intent 存在
        if isinstance(state, dict):
            user_input = state.get("user_input", "")
            intent = state.get("intent", "search")
            intents = state.get("intents", [])
        else:
            user_input = getattr(state, "user_input", "")
            intent = getattr(state, "intent", "search")
            intents = getattr(state, "intents", [])
        
        print(f"🔍 资源检索节点开始")
        print(f"📝 用户输入: {user_input}")
        print(f"🎯 意图: {intent}")
        print(f"🎯 意图列表: {intents}")
        
        # 调用资源检索函数
        retrieved_resources = retrieve_resources(
            query=user_input,
            intent=intent
        )
        
        # 确保 retrieved_resources 不是 None
        if retrieved_resources is None:
            print("⚠️ retrieve_resources 返回 None，使用空字典")
            retrieved_resources = {
                "theory_resources": [],
                "lesson_plan_patterns": [],
                "visualization_examples": [],
                "general_resources": []
            }
        
        print(f"📊 检索到 {len(retrieved_resources.get('theory_resources', []))} 条理论资源")
        print(f"📊 检索到 {len(retrieved_resources.get('lesson_plan_patterns', []))} 条教案共性")
        print(f"📊 检索到 {len(retrieved_resources.get('visualization_examples', []))} 条可视化示例")
        
        return {
            "retrieved_resources": retrieved_resources,
            "intent": intent,
            "intents": intents,
            "current_step": "resource_retrieval",
            "error": None
        }
    except Exception as e:
        print(f"❌ 资源检索节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "retrieved_resources": {
                "theory_resources": [],
                "lesson_plan_patterns": [],
                "visualization_examples": [],
                "general_resources": []
            },
            "intent": intent,
            "intents": intents,
            "current_step": "resource_retrieval",
            "error": f"资源检索失败: {str(e)}"
        }

# 教案生成节点
def lesson_plan_generation_node(state: MathAgentState) -> Dict[str, Any]:
    """
    教案生成节点
    根据用户需求和检索到的理论依据、优秀教案共性生成教案
    """
    try:
        # 确保 retrieved_resources 存在
        retrieved_resources = state.retrieved_resources or {}
        
        # 提取理论卡片信息并格式化
        theory_resources = retrieved_resources.get("theory_resources", [])
        formatted_theories = []
        
        for i, theory in enumerate(theory_resources, 1):
            title = theory.get('title', f'理论卡片{i}')
            content = theory.get('content', '')
            
            # 尝试从内容中提取理论名称
            theory_name = title
            if '理论卡片' in content:
                # 提取理论卡片标题
                lines = content.split('\n')
                for line in lines:
                    if '理论卡片' in line:
                        theory_name = line.strip()
                        break
            
            formatted_theories.append({
                'id': i,
                'name': theory_name,
                'content': content
            })
        
        # 准备理论依据文本
        theory_text = "\n".join([
            f"理论卡片{i}: {theory['name']}\n{theory['content']}"
            for i, theory in enumerate(formatted_theories, 1)
        ])
        
        # 准备教案共性文本
        patterns_text = "\n".join([
            f"- {r.get('title', '共性')}: {r.get('content', '')}"
            for r in retrieved_resources.get("lesson_plan_patterns", [])
        ])
        
        # 使用DeepSeek模型生成教案
        model = get_model("lesson_plan")
        print(f"教案生成使用的模型: {type(model).__name__}")
        print(f"提取到 {len(formatted_theories)} 个理论卡片")
        
        # 修改模型参数，确保生成完整教案
        if hasattr(model, 'max_tokens'):
            original_max_tokens = model.max_tokens
            model.max_tokens = 4000  # 增加token限制，确保完整输出
        
        lesson_plan_chain = lesson_plan_prompt | model | StrOutputParser()
        lesson_plan = lesson_plan_chain.invoke({
            "user_input": state.user_input,
            "theory_resources": theory_text if theory_text else "暂无相关理论依据",
            "lesson_plan_patterns": patterns_text if patterns_text else "暂无优秀教案共性"
        })
        
        # 恢复原始max_tokens
        if hasattr(model, 'max_tokens'):
            model.max_tokens = original_max_tokens
        
        print(f"教案生成完成，长度: {len(lesson_plan)} 字符")
        
        return {
            "lesson_plan": lesson_plan,
            "current_step": "lesson_plan_generation",
            "error": None
        }
    except Exception as e:
        print(f"教案生成节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "lesson_plan": None,
            "current_step": "lesson_plan_generation",
            "error": f"教案生成失败: {str(e)}"
        }

# 可视化设计建议节点
def visualization_suggestion_node(state: MathAgentState) -> Dict[str, Any]:
    """
    可视化设计建议节点
    为用户提供GGB动态数学设计建议，基于检索到的可视化设计示例
    """
    try:
        # 确保 retrieved_resources 存在
        retrieved_resources = state.retrieved_resources or {}
        
        # 准备可视化示例文本
        examples_text = "\n".join([
            f"- {r.get('title', '示例')}: {r.get('content', '')}"
            for r in retrieved_resources.get("visualization_examples", [])
        ])
        
        # 使用DeepSeek模型生成可视化设计建议
        visualization_chain = visualization_prompt | get_model("visualization") | StrOutputParser()
        visualization_suggestions = visualization_chain.invoke({
            "user_input": state.user_input,
            "visualization_examples": examples_text if examples_text else "暂无相关设计示例"
        })
        
        return {
            "visualization_suggestions": visualization_suggestions,
            "current_step": "visualization_suggestion",
            "error": None
        }
    except Exception as e:
        return {
            "visualization_suggestions": None,
            "current_step": "visualization_suggestion",
            "error": f"可视化设计建议生成失败: {str(e)}"
        }

# 搜索结果处理节点
def search_result_processing_node(state: MathAgentState) -> Dict[str, Any]:
    """
    搜索结果处理节点
    格式化搜索结果并返回给用户
    """
    try:
        # 确保 retrieved_resources 存在
        resources = state.retrieved_resources or {}
        
        # 理论卡片不显示在搜索结果中（仅用于教案生成）
        theory_resources = resources.get("theory_resources", [])
        lesson_plan_patterns = resources.get("lesson_plan_patterns", [])
        exercise_resources = resources.get("exercise_resources", [])
        visualization_examples = resources.get("visualization_examples", [])
        general_resources = resources.get("general_resources", [])
        courseware_resources = resources.get("courseware_resources", [])
        lesson_case_resources = resources.get("lesson_case_resources", [])
        ggb_resources = resources.get("ggb_resources", [])
        syllabus_resources = resources.get("syllabus_resources", [])
        
        # 获取智能内容处理器
        content_processor = get_content_processor()
        
        if not any([lesson_plan_patterns, exercise_resources, visualization_examples, general_resources, courseware_resources, lesson_case_resources, ggb_resources, syllabus_resources]):
            search_results = "未找到相关资源。请尝试使用其他关键词或描述更具体的需求。"
        else:
            results_parts = []
            
            # 去重函数
            def deduplicate_resources(resources_list):
                seen_titles = set()
                unique_resources = []
                for r in resources_list:
                    title = r.get('title', '未知')
                    if title not in seen_titles:
                        seen_titles.add(title)
                        unique_resources.append(r)
                return unique_resources
            
            # 排序函数 - 按相似度降序
            def sort_by_relevance(resources_list):
                return sorted(resources_list, key=lambda x: x.get('relevance', 0), reverse=True)
            
            # 教案资源处理
            if lesson_plan_patterns:
                unique_plans = deduplicate_resources(lesson_plan_patterns)
                sorted_plans = sort_by_relevance(unique_plans)
                results_parts.append("【教案资源】")
                for r in sorted_plans[:5]:  # 增加到显示前5条
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 使用智能内容处理器
                    processed = content_processor.process_content(content, "lesson_plan", 300)
                    content_preview = processed['summary']
                    
                    results_parts.append(f"\n📚 {title}")
                    results_parts.append(f"   内容: {content_preview}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # 习题资源处理
            if exercise_resources:
                unique_exercises = deduplicate_resources(exercise_resources)
                sorted_exercises = sort_by_relevance(unique_exercises)
                results_parts.append("\n\n【习题资源】")
                for r in sorted_exercises[:5]:  # 增加到显示前5条
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 检查是否包含题目文件名
                    filename_info = extract_filename_from_content(content)
                    
                    # 判断是否为图片题目
                    is_image_question = any(ext in filename_info.lower() if filename_info else '' for ext in ['.png', '.jpg', '.jpeg', '.gif'])
                    
                    if is_image_question and filename_info:
                        # 图片题目：直接显示文件名
                        content_preview = f"【图片题目】{filename_info}"
                    elif is_image_question:
                        # 图片题目但无文件名
                        content_preview = "【图片题目】请查看题目文件"
                    else:
                        # 文字题目：使用智能内容处理器
                        processed = content_processor.process_content(content, "exercise", 400)
                        content_preview = processed['summary']
                    
                    results_parts.append(f"\n📝 {title}")
                    results_parts.append(f"   内容: {content_preview}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
                    
                    # 不再重复显示文件信息，因为已经在内容中显示了
            
            # 可视化示例处理
            if visualization_examples:
                unique_visuals = deduplicate_resources(visualization_examples)
                sorted_visuals = sort_by_relevance(unique_visuals)
                results_parts.append("\n\n【可视化示例】")
                for r in sorted_visuals[:3]:  # 保持显示前3条
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 使用智能内容处理器
                    processed = content_processor.process_content(content, "visualization", 250)
                    content_preview = processed['summary']
                    
                    results_parts.append(f"\n🎨 {title}")
                    results_parts.append(f"   内容: {content_preview}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # 通用资源处理
            if general_resources:
                unique_general = deduplicate_resources(general_resources)
                sorted_general = sort_by_relevance(unique_general)
                results_parts.append("\n\n【通用资源】")
                for r in sorted_general[:3]:  # 保持显示前3条
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 使用智能内容处理器
                    processed = content_processor.process_content(content, "general", 300)
                    content_preview = processed['summary']
                    
                    results_parts.append(f"\n📄 {title}")
                    results_parts.append(f"   内容: {content_preview}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # 课件资源处理
            if courseware_resources:
                unique_courseware = deduplicate_resources(courseware_resources)
                sorted_courseware = sort_by_relevance(unique_courseware)
                results_parts.append("\n\n【课件资源】")
                for r in sorted_courseware[:5]:  # 增加到显示前5条
                    title = r.get('title', '未知')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 课件只显示文件名
                    results_parts.append(f"\n📊 {title}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # 课例资源处理
            if lesson_case_resources:
                unique_lesson_cases = deduplicate_resources(lesson_case_resources)
                sorted_lesson_cases = sort_by_relevance(unique_lesson_cases)
                results_parts.append("\n\n【课例资源】")
                for r in sorted_lesson_cases[:5]:  # 增加到显示前5条
                    title = r.get('title', '未知')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 课例只显示文件名
                    results_parts.append(f"\n🎬 {title}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # GGB资源处理
            if ggb_resources:
                unique_ggb = deduplicate_resources(ggb_resources)
                sorted_ggb = sort_by_relevance(unique_ggb)
                results_parts.append("\n\n【GGB资源】")
                for r in sorted_ggb[:5]:  # 增加到显示前5条
                    title = r.get('title', '未知')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # GGB只显示文件名
                    results_parts.append(f"\n🔧 {title}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            # 教学大纲处理
            if syllabus_resources:
                unique_syllabus = deduplicate_resources(syllabus_resources)
                sorted_syllabus = sort_by_relevance(unique_syllabus)
                results_parts.append("\n\n【教学大纲】")
                for r in sorted_syllabus[:3]:  # 保持显示前3条
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    source = r.get('source', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理路径
                    clean_source = source.replace('\\', '/').strip()
                    
                    # 教学大纲：匹配用户要求的内容并输出
                    user_input = state.user_input if hasattr(state, 'user_input') else ''
                    processed = content_processor.process_content(content, "general", 500)
                    content_preview = processed['summary']
                    
                    results_parts.append(f"\n📋 {title}")
                    results_parts.append(f"   内容: {content_preview}")
                    results_parts.append(f"   相似度: {relevance:.1%}")
                    results_parts.append(f"   文件路径: {clean_source}")
            
            search_results = "\n".join(results_parts)
        
        return {
            "search_results": search_results,
            "current_step": "search_result_processing",
            "error": None
        }
    except Exception as e:
        return {
            "search_results": "搜索结果处理失败",
            "current_step": "search_result_processing",
            "error": f"搜索结果处理失败: {str(e)}"
        }

def extract_filename_from_content(content: str) -> str:
    """
    从内容中提取题目文件名
    
    Args:
        content: 资源内容
    
    Returns:
        提取的文件名信息，如果没有则返回空字符串
    """
    import re
    
    # 查找表格中的文件名
    # 文件名通常在表格的最后一列，以文件扩展名结尾
    file_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov', '.pptx', '.ppt', '.pdf', '.ggb', '.ggb']
    
    # 查找所有可能的文件名
    found_files = []
    for ext in file_extensions:
        # 查找以文件扩展名结尾的内容
        pattern = rf'([^\s\|]+{ext})'
        matches = re.findall(pattern, content)
        for match in matches:
            filename = match.strip()
            if filename and len(filename) > 4:  # 至少5个字符
                found_files.append(filename)
    
    # 返回找到的第一个文件名
    if found_files:
        return found_files[0]
    
    return ""

# 响应格式化节点
def response_formatting_node(state: MathAgentState) -> Dict[str, Any]:
    """
    响应格式化节点
    根据不同的意图和执行结果，格式化最终响应
    """
    try:
        # 确保 intent 存在
        intent = state.intent or "search"
        
        # 根据意图生成不同的响应
        if intent == "search":
            response = state.search_results if state.search_results else "搜索功能正在建设中"
        elif intent == "generate_lesson_plan":
            response = state.lesson_plan if state.lesson_plan else "教案生成失败"
        elif intent == "visualization":
            response = state.visualization_suggestions if state.visualization_suggestions else "可视化建议生成失败"
        else:
            response = "未知的意图类型"
        
        # 获取现有消息列表
        messages = state.messages if hasattr(state, 'messages') and state.messages else []
        
        # 添加AI响应消息
        ai_message = {
            "role": "assistant",
            "content": response
        }
        
        return {
            "response": response,
            "messages": messages + [ai_message],
            "current_step": "response_formatting",
            "error": None
        }
    except Exception as e:
        return {
            "response": "响应格式化失败",
            "messages": state.messages if hasattr(state, 'messages') and state.messages else [],
            "current_step": "response_formatting",
            "error": f"响应格式化失败: {str(e)}"
        }
