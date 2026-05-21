import os
import sys
import logging

# 解决 Windows 控制台编码问题 - 设置默认输出为 UTF-8
if sys.platform == "win32":
    import io
    # 重设标准输出和错误流的编码为 UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量，确保子进程也使用 UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 首先设置 HuggingFace 镜像源，避免连接超时
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 首先加载环境变量（必须在导入 app.core 之前！）
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langserve import add_routes
from langgraph.types import StreamMode
from app.state import MathAgentState
from app.langgraph_api import router as langgraph_api_router
from app.core import generate_ggb_innovation_suggestions
from app.core.model_config import model_config
from app.api.routes import feedback_router
from app.api.routes.ggb import router as ggb_router

# 延迟导入 create_math_agent_graph，避免启动时卡住
def get_math_agent_graph():
    from app.graph import create_math_agent_graph
    return create_math_agent_graph()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 验证API密钥配置
def validate_api_keys():
    """
    验证API密钥配置
    """
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    openai_compat_key = os.getenv("OPENAI_COMPAT_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    
    warnings = []
    deepseek_ready = bool(deepseek_key and deepseek_key != "your-api-key-here")
    openai_compat_ready = bool(openai_compat_key and openai_compat_key != "your-api-key-here")
    
    if provider not in {"auto", "deepseek", "openai_compatible"}:
        warnings.append(f"未知 LLM_PROVIDER={provider}，应为 auto/deepseek/openai_compatible")
        provider = "auto"

    if provider == "deepseek" and not deepseek_ready:
        warnings.append("LLM_PROVIDER=deepseek 但 DEEPSEEK_API_KEY 未配置")
    elif provider == "openai_compatible" and not openai_compat_ready:
        warnings.append("LLM_PROVIDER=openai_compatible 但 OPENAI_COMPAT_API_KEY/OPENAI_API_KEY 未配置")
    elif provider == "auto" and not (deepseek_ready or openai_compat_ready):
        warnings.append("未检测到可用模型密钥（DEEPSEEK_API_KEY 或 OPENAI_COMPAT_API_KEY/OPENAI_API_KEY）")
    
    if warnings:
        logger.warning(f"API密钥配置警告: {', '.join(warnings)}")
        logger.warning("请在.env文件中配置相应的API密钥")
    
    return len(warnings) == 0

# 验证API密钥
api_keys_valid = validate_api_keys()

# 创建FastAPI应用
app = FastAPI(
    title="高中数学资源智能体 API",
    description="提供高中数学教案生成、资源检索、可视化设计建议等功能",
    version="1.0.0"
)

# 配置CORS
# 从环境变量读取允许的源，支持多个域名，用逗号分隔
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS配置: 允许的源: {allowed_origins}")

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "service": "math-agent-api",
        "api_keys_configured": api_keys_valid
    }

# Info端点（用于前端检查graph状态）
@app.get("/info")
async def info_check():
    """
    Info端点
    用于前端检查graph状态
    """
    return {
        "status": "healthy",
        "service": "math-agent-api",
        "api_keys_configured": api_keys_valid
    }

# 模型配置状态端点
@app.get("/models/status")
async def get_models_status():
    """
    获取模型配置状态
    
    Returns:
        各模型的配置状态信息
    """
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    openai_compat_key = os.getenv("OPENAI_COMPAT_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    openai_compat_base_url = os.getenv("OPENAI_COMPAT_BASE_URL") or os.getenv("OPENAI_BASE_URL", "")
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    
    return {
        "provider": {
            "configured": provider,
            "resolved": model_config.get_llm_provider()
        },
        "deepseek": {
            "configured": bool(deepseek_key and deepseek_key != "your-api-key-here"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "purpose": "可用于所有任务：意图理解、教案生成、可视化建议"
        },
        "openai_compatible": {
            "configured": bool(openai_compat_key and openai_compat_key != "your-api-key-here"),
            "model": os.getenv("OPENAI_COMPAT_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "base_url_configured": bool(openai_compat_base_url),
            "purpose": "可用于 OpenAI 格式兼容服务（含第三方网关）"
        },
        "model_assignment": {
            "intent_understanding": "统一模型",
            "lesson_plan_generation": "统一模型",
            "visualization_suggestions": "统一模型",
            "default": model_config.get_llm_provider()
        }
    }

# GGB创新设计建议请求模型
class GGBInnovationRequest(BaseModel):
    chapter: str
    topic: str
    teaching_purpose: str
    existing_ggb_info: Optional[str] = None

# 数学智能体API端点
class MathAgentRequest(BaseModel):
    user_input: str
    chat_history: Optional[list] = None
    context: Optional[dict] = None

# 兼容旧的API端点（用于前端）
class QueryRequest(BaseModel):
    query: str
    intent: str = "search"
    resource_types: Optional[List[str]] = None

@app.post("/api/query")
async def api_query(request: QueryRequest) -> Dict[str, Any]:
    """
    兼容旧的API端点，用于前端
    """
    # 转换为MathAgentRequest格式
    math_request = MathAgentRequest(
        user_input=request.query,
        chat_history=[],
        context={
            "intent": request.intent,
            "resource_types": request.resource_types
        }
    )
    
    # 调用现有的math-agent/invoke端点
    return await invoke_math_agent(math_request)

@app.post("/math-agent/invoke")
async def invoke_math_agent(request: MathAgentRequest) -> Dict[str, Any]:
    """
    调用数学智能体
    
    Args:
        request: 包含用户输入、对话历史和上下文的请求对象
    
    Returns:
        智能体处理结果
    """
    try:
        print(f"====================================")
        print(f"收到请求: {request.user_input}")
        print(f"====================================")
        logger.info(f"Processing user input: {request.user_input}")
        
        # 构建输入状态
        input_state = MathAgentState(
            user_input=request.user_input,
            chat_history=request.chat_history or [],
            context=request.context or {}
        )
        
        logger.info(f"Input state: {input_state}")
        
        # 重新创建math_agent_graph实例，确保使用最新的节点函数
        math_agent_graph = get_math_agent_graph()
        
        print(f"开始调用LangGraph...")
        print(f"输入状态类型: {type(input_state)}")
        print(f"输入状态内容: {input_state}")
        
        # 调用LangGraph
        result = await math_agent_graph.ainvoke(input_state)
        
        print(f"LangGraph调用完成")
        print(f"结果类型: {type(result)}")
        print(f"结果内容: {result}")
        logger.info(f"Result: {result}")
        logger.info(f"Processing completed successfully")
        
        # 构建响应
        response = {
            "status": "success",
            "data": {
                "intent": result.get("intent"),
                "intents": result.get("intents"),
                "lesson_plan": result.get("lesson_plan"),
                "visualization_suggestions": result.get("visualization_suggestions"),
                "retrieved_resources": result.get("retrieved_resources"),
                "exercise_details": result.get("exercise_details", []),
                "current_step": result.get("current_step"),
                "chat_history": result.get("chat_history"),
                "error": result.get("error")
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 直接生成教案的端点
@app.post("/math-agent/generate-lesson-plan")
async def generate_lesson_plan(request: MathAgentRequest) -> Dict[str, Any]:
    """
    直接生成教案，绕过意图理解节点
    
    Args:
        request: 包含用户输入、对话历史和上下文的请求对象
    
    Returns:
        教案生成结果
    """
    try:
        # 重新创建math_agent_graph实例
        math_agent_graph = get_math_agent_graph()
        
        # 构建输入状态，强制设置意图为generate_lesson_plan
        input_state = MathAgentState(
            user_input=request.user_input,
            chat_history=request.chat_history or [],
            context=request.context or {},
            intent="generate_lesson_plan"
        )
        
        # 调用LangGraph
        result = await math_agent_graph.ainvoke(input_state)
        
        return {
            "status": "success",
            "data": {
                "lesson_plan": result.get("lesson_plan"),
                "retrieved_resources": result.get("retrieved_resources"),
                "exercise_details": result.get("exercise_details", []),
                "current_step": result.get("current_step"),
                "error": result.get("error")
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating lesson plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 流式调用端点
@app.post("/math-agent/stream")
async def stream_math_agent(request: MathAgentRequest):
    """
    流式调用数学智能体
    
    Args:
        request: 包含用户输入、对话历史和上下文的请求对象
    
    Returns:
        流式处理结果
    """
    try:
        logger.info(f"Streaming user input: {request.user_input}")
        
        # 构建输入状态
        input_state = {
            "user_input": request.user_input,
            "chat_history": request.chat_history or [],
            "context": request.context or {}
        }
        
        # 重新创建math_agent_graph实例，确保使用最新的节点函数
        math_agent_graph = get_math_agent_graph()
        
        # 流式调用LangGraph
        async for chunk in math_agent_graph.astream(
            input_state,
            stream_mode=StreamMode.UPDATES
        ):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error streaming request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 添加 LangGraph API 路由（必须在 LangServe 之前）
app.include_router(langgraph_api_router)

# 添加 API 路由
app.include_router(feedback_router)

# 添加 GeoGebra 设计建议 API 路由
app.include_router(ggb_router)

# 添加 LangServe 路由
# 延迟导入，避免启动时卡住
def add_langserve_routes():
    from app.graph import create_math_agent_graph
    math_agent_graph = create_math_agent_graph()
    add_routes(
        app,
        math_agent_graph,
        path="/langgraph/math-agent"
    )

# 调用添加LangServe路由的函数
add_langserve_routes()

# ============================================
# GGB创新设计建议 API
# ============================================
@app.post("/ggb/innovation-suggestions")
async def get_ggb_innovation_suggestions(request: GGBInnovationRequest):
    """
    获取GGB创新设计建议
    
    Args:
        request: GGB创新设计建议请求
        
    Returns:
        GGB创新设计建议
    """
    try:
        suggestions = generate_ggb_innovation_suggestions(
            chapter=request.chapter,
            topic=request.topic,
            teaching_purpose=request.teaching_purpose,
            existing_ggb_info=request.existing_ggb_info
        )
        
        return {
            "status": "success",
            "data": {
                "suggestions": suggestions
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating GGB suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================
# 静态文件服务
# ============================================
# 挂载静态文件目录
import os
from pathlib import Path
# 使用绝对路径确保正确找到静态文件目录
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning(f"静态文件目录不存在，跳过挂载: {static_dir}")

# 几何图形库页面
@app.get("/geometry-library")
async def geometry_library():
    """
    几何图形库页面
    """
    return FileResponse("geometry_library.html")

# 画图建议 + 图形库组合页面
@app.get("/geometry-with-suggestions")
async def geometry_with_suggestions():
    """
    画图建议 + 图形库组合页面
    """
    return FileResponse("geometry_with_suggestions.html")

# 组合页面别名
@app.get("/combined-geometry")
async def geometry_with_suggestions_alias():
    """
    画图建议 + 图形库组合页面
    """
    return FileResponse("geometry_with_suggestions.html")

@app.on_event("startup")
def preload_runtime_dependencies():
    """
    应用启动时预热关键依赖，避免首个检索请求现场冷启动。
    """
    preload_embedding = os.getenv("PRELOAD_EMBEDDING_ON_STARTUP", "1").strip().lower() in {
        "1", "true", "yes", "on"
    }

    if not preload_embedding:
        logger.info("跳过 embedding 预热：PRELOAD_EMBEDDING_ON_STARTUP=0")
        return

    logger.info("开始预热运行时依赖")
    try:
        model_config.get_embedding_model()
        logger.info("Embedding 预热完成")
    except Exception as e:
        logger.warning(f"Embedding 预热失败，服务继续启动: {e}")

    try:
        model_config.get_chroma_client()
        logger.info("ChromaDB 客户端预热完成")
    except Exception as e:
        logger.warning(f"ChromaDB 客户端预热失败，服务继续启动: {e}")

# 根路径
@app.get("/")
async def root():
    """
    根路径
    """
    return {
        "message": "高中数学资源智能体 API",
        "endpoints": {
            "/health": "健康检查",
            "/info": "信息检查",
            "/models/status": "模型配置状态",
            "/math-agent/invoke": "调用数学智能体",
            "/math-agent/stream": "流式调用数学智能体",
            "/ggb/innovation-suggestions": "获取GGB创新设计建议",
            "/langserve/math-agent": "LangServe API",
            "/geometry-library": "几何图形库",
            "/geometry-with-suggestions": "画图建议 + 图形库",
            "/combined-geometry": "画图建议 + 图形库（别名）",
            "/demo-suggestions": "设计建议演示"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # 获取端口配置
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False
    )
