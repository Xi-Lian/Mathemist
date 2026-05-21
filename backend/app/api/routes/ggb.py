"""
GeoGebra 设计建议 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from app.core.ggb_design_advisor import generate_ggb_innovation_suggestions

router = APIRouter(prefix="/ggb", tags=["ggb"])


class InnovationSuggestionRequest(BaseModel):
    """创新建议请求模型"""
    chapter: str
    topic: str
    teaching_purpose: str
    existing_ggb_info: Optional[str] = None


class InnovationSuggestionResponse(BaseModel):
    """创新建议响应模型"""
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/innovation-suggestions", response_model=InnovationSuggestionResponse)
async def get_innovation_suggestions(request: InnovationSuggestionRequest):
    """
    获取 GeoGebra 创新设计建议
    
    Args:
        request: 包含章节、主题、教学用途的请求
        
    Returns:
        包含设计建议的响应
    """
    try:
        # 调用核心函数生成建议
        result = generate_ggb_innovation_suggestions(
            chapter=request.chapter,
            topic=request.topic,
            teaching_purpose=request.teaching_purpose,
            existing_ggb_info=request.existing_ggb_info
        )
        
        # 检查是否有错误
        if "error" in result and result["error"]:
            return InnovationSuggestionResponse(
                status="error",
                error=result["error"]
            )
        
        # 返回成功结果
        return InnovationSuggestionResponse(
            status="success",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成建议失败: {str(e)}"
        )
