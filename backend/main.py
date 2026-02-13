import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langserve import add_routes
from langgraph.types import StreamMode
from app.graph import create_math_agent_graph
from app.state import MathAgentState
from app.langgraph_api import router as langgraph_api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 验证API密钥配置
def validate_api_keys():
    """
    验证API密钥配置
    """
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    warnings = []
    
    if not deepseek_key or deepseek_key == "your-api-key-here":
        warnings.append("DeepSeek API密钥未配置")
    
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

# 添加 LangGraph API 路由
app.include_router(langgraph_api_router)

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

# 模型配置状态端点
@app.get("/models/status")
async def get_models_status():
    """
    获取模型配置状态
    
    Returns:
        各模型的配置状态信息
    """
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    return {
        "deepseek": {
            "configured": bool(deepseek_key and deepseek_key != "your-api-key-here"),
            "purpose": "统一模型，用于所有任务：意图理解、教案生成、可视化建议"
        },
        "model_assignment": {
            "intent_understanding": "DeepSeek",
            "lesson_plan_generation": "DeepSeek",
            "visualization_suggestions": "DeepSeek",
            "default": "DeepSeek"
        }
    }

# 数学智能体API端点
class MathAgentRequest(BaseModel):
    user_input: str
    chat_history: Optional[list] = None
    context: Optional[dict] = None

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
        math_agent_graph = create_math_agent_graph()
        
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
        logger.info(f"Generating lesson plan for: {request.user_input}")
        
        # 导入必要的函数
        from app.nodes import retrieve_resources, lesson_plan_generation_node
        from app.state import MathAgentState
        
        # 检索资源
        retrieved_resources = retrieve_resources(
            query=request.user_input,
            intent="generate_lesson_plan"
        )
        
        # 创建状态对象
        state = MathAgentState(
            user_input=request.user_input,
            chat_history=request.chat_history or [],
            context=request.context or {},
            intent="generate_lesson_plan",
            retrieved_resources=retrieved_resources
        )
        
        # 直接调用教案生成节点
        result = lesson_plan_generation_node(state)
        
        logger.info(f"Lesson plan generation completed successfully")
        
        # 构建响应
        response = {
            "status": "success",
            "data": {
                "lesson_plan": result.get("lesson_plan"),
                "error": result.get("error")
            }
        }
        
        return response
        
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
        
        # 流式调用LangGraph
        async for chunk in math_agent_graph.astream(
            input_state,
            stream_mode=StreamMode.UPDATES
        ):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error streaming request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 添加LangServe路由
add_routes(
    app,
    create_math_agent_graph(),
    path="/langserve/math-agent"
)

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
            "/math-agent/invoke": "调用数学智能体",
            "/math-agent/stream": "流式调用数学智能体",
            "/langserve/math-agent": "LangServe API"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # 获取端口配置
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True  # 在开发环境中启用热重载
    )
