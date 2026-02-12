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

def get_chroma_client():
    """获取ChromaDB客户端（单例模式）"""
    global _chroma_client
    if _chroma_client is None:
        SCRIPT_DIR = Path(__file__).parent.parent.parent
        CHROMA_DB_DIR = SCRIPT_DIR / "backend" / "chroma_db"
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return _chroma_client

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
    
    # 教案相关关键词
    lesson_plan_keywords = [
        "教案", "教学设计", "教学大纲", "导学案", "说课稿",
        "lesson", "teaching", "syllabus", "design"
    ]
    
    # 可视化相关关键词
    visualization_keywords = [
        "ggb", "geogebra", "可视化", "动态", "图象", "图像",
        "visualization", "dynamic", "graph", "plot"
    ]
    
    # 习题相关关键词
    exercise_keywords = [
        "习题", "练习", "题目", "答案", "试题",
        "exercise", "practice", "problem", "answer", "question"
    ]
    
    # 统计各类型的关键词匹配数
    lesson_plan_score = sum(1 for kw in lesson_plan_keywords if kw in source_lower or kw in content_lower)
    visualization_score = sum(1 for kw in visualization_keywords if kw in source_lower or kw in content_lower)
    exercise_score = sum(1 for kw in exercise_keywords if kw in source_lower or kw in content_lower)
    
    # 根据得分判断类型
    scores = {
        "lesson_plan": lesson_plan_score,
        "visualization": visualization_score,
        "exercise": exercise_score
    }
    
    max_score = max(scores.values())
    
    if max_score == 0:
        return "theory"
    
    # 返回得分最高的类型
    for resource_type, score in scores.items():
        if score == max_score:
            return resource_type
    
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
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"📦 查询结果: {results}")
        
        theory_resources = []
        lesson_plan_patterns = []
        visualization_examples = []
        general_resources = []
        
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
                    general_resources.append(resource)
                else:
                    theory_resources.append(resource)
        
        print(f"✅ 检索完成: 理论资源{len(theory_resources)}条, 教案{len(lesson_plan_patterns)}条, 可视化{len(visualization_examples)}条, 通用{len(general_resources)}条")
        
        return {
            "theory_resources": theory_resources,
            "lesson_plan_patterns": lesson_plan_patterns,
            "visualization_examples": visualization_examples,
            "general_resources": general_resources
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
        user_input = state.user_input or ""
        
        print(f"🔍 意图理解节点开始")
        print(f"📝 用户输入: {user_input}")
        
        if not user_input:
            print("⚠️ 用户输入为空，使用默认意图")
            return {
                "intent": "search",  # 默认意图
                "current_step": "intent_understanding",
                "error": "用户输入为空"
            }
        
        # 使用DeepSeek模型进行意图理解
        model = get_model("intent")
        print(f"🤖 意图理解使用的模型: {type(model).__name__}")
        
        intent_chain = intent_prompt | model | StrOutputParser()
        print(f"🔗 意图理解链: {type(intent_chain).__name__}")
        
        intent = intent_chain.invoke({"user_input": user_input})
        print(f"🎯 模型返回的原始意图: {intent}")
        
        # 确保 intent 不是 None
        if intent is None:
            print("⚠️ 模型返回 None，使用默认意图")
            intent = "search"
        
        print(f"✅ 识别到的意图: {intent}")
        
        # 标准化意图输出
        intent = intent.strip().lower()
        if intent not in ["search", "generate_lesson_plan", "visualization"]:
            intent = "search"  # 默认意图
        
        print(f"📋 标准化后的意图: {intent}")
        
        return {
            "intent": intent,
            "current_step": "intent_understanding",
            "error": None
        }
    except Exception as e:
        print(f"❌ 意图理解节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "intent": "search",  # 默认意图
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
        user_input = state.user_input or ""
        intent = state.intent or "search"
        
        print(f"🔍 资源检索节点开始")
        print(f"📝 用户输入: {user_input}")
        print(f"🎯 意图: {intent}")
        
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
        
        # 准备理论依据文本
        theory_text = "\n".join([
            f"- {r.get('title', '理论')}: {r.get('content', '')}"
            for r in retrieved_resources.get("theory_resources", [])
        ])
        
        # 准备教案共性文本
        patterns_text = "\n".join([
            f"- {r.get('title', '共性')}: {r.get('content', '')}"
            for r in retrieved_resources.get("lesson_plan_patterns", [])
        ])
        
        # 使用DeepSeek模型生成教案
        model = get_model("lesson_plan")
        print(f"教案生成使用的模型: {type(model).__name__}")
        
        lesson_plan_chain = lesson_plan_prompt | model | StrOutputParser()
        lesson_plan = lesson_plan_chain.invoke({
            "user_input": state.user_input,
            "theory_resources": theory_text if theory_text else "暂无相关理论依据",
            "lesson_plan_patterns": patterns_text if patterns_text else "暂无优秀教案共性"
        })
        
        print(f"教案生成完成，长度: {len(lesson_plan)} 字符")
        
        return {
            "lesson_plan": lesson_plan,
            "current_step": "lesson_plan_generation",
            "error": None
        }
    except Exception as e:
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
        
        theory_resources = resources.get("theory_resources", [])
        lesson_plan_patterns = resources.get("lesson_plan_patterns", [])
        visualization_examples = resources.get("visualization_examples", [])
        general_resources = resources.get("general_resources", [])
        
        if not any([theory_resources, lesson_plan_patterns, visualization_examples, general_resources]):
            search_results = "未找到相关资源。请尝试使用其他关键词或描述更具体的需求。"
        else:
            results_parts = []
            
            if lesson_plan_patterns:
                results_parts.append("【教案资源】")
                for r in lesson_plan_patterns[:5]:
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    relevance = r.get('relevance', 0)
                    
                    # 清理内容：移除多余的空行、符号和表格格式
                    content_lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('|') and not line.startswith('-') and not line.startswith('>'):
                            content_lines.append(line)
                    
                    content_preview = ' '.join(content_lines[:2]) if content_lines else '暂无内容'
                    if len(content_preview) > 150:
                        content_preview = content_preview[:150] + '...'
                    
                    results_parts.append(f"\n{title}")
                    results_parts.append(f"  {content_preview}")
                    results_parts.append(f"  相似度: {relevance:.1%}")
            
            if theory_resources:
                results_parts.append("\n\n【理论资源】")
                for r in theory_resources[:3]:
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    relevance = r.get('relevance', 0)
                    
                    content_lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('|') and not line.startswith('-'):
                            content_lines.append(line)
                    
                    content_preview = ' '.join(content_lines[:2]) if content_lines else '暂无内容'
                    if len(content_preview) > 150:
                        content_preview = content_preview[:150] + '...'
                    
                    results_parts.append(f"\n{title}")
                    results_parts.append(f"  {content_preview}")
                    results_parts.append(f"  相似度: {relevance:.1%}")
            
            if visualization_examples:
                results_parts.append("\n\n【可视化示例】")
                for r in visualization_examples[:3]:
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    relevance = r.get('relevance', 0)
                    
                    content_lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('|') and not line.startswith('-'):
                            content_lines.append(line)
                    
                    content_preview = ' '.join(content_lines[:2]) if content_lines else '暂无内容'
                    if len(content_preview) > 150:
                        content_preview = content_preview[:150] + '...'
                    
                    results_parts.append(f"\n{title}")
                    results_parts.append(f"  {content_preview}")
                    results_parts.append(f"  相似度: {relevance:.1%}")
            
            if general_resources:
                results_parts.append("\n\n【通用资源】")
                for r in general_resources[:3]:
                    title = r.get('title', '未知')
                    content = r.get('content', '')
                    relevance = r.get('relevance', 0)
                    
                    content_lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('|') and not line.startswith('-'):
                            content_lines.append(line)
                    
                    content_preview = ' '.join(content_lines[:2]) if content_lines else '暂无内容'
                    if len(content_preview) > 150:
                        content_preview = content_preview[:150] + '...'
                    
                    results_parts.append(f"\n{title}")
                    results_parts.append(f"  {content_preview}")
                    results_parts.append(f"  相似度: {relevance:.1%}")
            
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
        
        return {
            "response": response,
            "current_step": "response_formatting",
            "error": None
        }
    except Exception as e:
        return {
            "response": "响应格式化失败",
            "current_step": "response_formatting",
            "error": f"响应格式化失败: {str(e)}"
        }
