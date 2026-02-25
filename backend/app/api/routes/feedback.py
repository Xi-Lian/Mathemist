"""
用户反馈API路由
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.core.user_feedback import get_feedback_system

router = APIRouter(prefix="/feedback", tags=["feedback"])


class ResourceFeedbackRequest(BaseModel):
    """资源反馈请求"""
    resource_id: str = Field(..., description="资源ID")
    is_like: bool = Field(..., description="是否点赞（True=点赞，False=点踩）")
    query: str = Field(default="", description="用户查询")
    resource_type: str = Field(default="", description="资源类型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="资源元数据")
    dislike_reason: str = Field(default="", description="点踩原因")


class ImprovementSuggestionRequest(BaseModel):
    """建议反馈请求"""
    query: str = Field(default="", description="用户查询")
    suggestion: str = Field(..., description="建议内容")
    contact: str = Field(default="", description="联系方式")


@router.post("/resource")
async def record_resource_feedback(request: ResourceFeedbackRequest):
    """
    记录资源反馈（点赞/点踩）
    
    **状态码说明：**
    - 200: 成功
    - 400: 请求参数错误
    - 422: 数据验证失败
    - 500: 服务器内部错误
    
    **请求字段：**
    - resource_id: 资源ID（必填）
    - is_like: 是否点赞（True=点赞，False=点踩）（必填）
    - query: 用户查询（可选）
    - resource_type: 资源类型（可选）
    - metadata: 资源元数据（可选）
    - dislike_reason: 点踩原因（可选，当is_like为false时建议填写）
    """
    try:
        if not request.resource_id or request.resource_id.strip() == "":
            return {
                "success": False,
                "message": "resource_id 不能为空",
                "error_code": "INVALID_RESOURCE_ID"
            }, status.HTTP_400_BAD_REQUEST
        
        feedback_system = get_feedback_system()
        success = feedback_system.record_resource_feedback(
            resource_id=request.resource_id,
            is_like=request.is_like,
            query=request.query,
            resource_type=request.resource_type,
            metadata=request.metadata,
            dislike_reason=request.dislike_reason
        )
        
        if success:
            return {
                "success": True,
                "message": "资源反馈已成功记录"
            }
        else:
            return {
                "success": False,
                "message": "记录反馈失败，请稍后重试",
                "error_code": "RECORD_FAILED"
            }, status.HTTP_500_INTERNAL_SERVER_ERROR
            
    except Exception as e:
        return {
            "success": False,
            "message": f"服务器错误: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post("/suggestion")
async def record_improvement_suggestion(request: ImprovementSuggestionRequest):
    """
    记录建议反馈
    
    **状态码说明：**
    - 200: 成功
    - 400: 请求参数错误
    - 422: 数据验证失败
    - 500: 服务器内部错误
    
    **请求字段：**
    - query: 用户查询（可选）
    - suggestion: 建议内容（必填）
    - contact: 联系方式（可选）
    """
    try:
        if not request.suggestion or request.suggestion.strip() == "":
            return {
                "success": False,
                "message": "suggestion 不能为空",
                "error_code": "INVALID_SUGGESTION"
            }, status.HTTP_400_BAD_REQUEST
        
        feedback_system = get_feedback_system()
        success = feedback_system.record_improvement_suggestion(
            query=request.query,
            suggestion=request.suggestion,
            contact=request.contact
        )
        
        if success:
            return {
                "success": True,
                "message": "建议反馈已成功记录"
            }
        else:
            return {
                "success": False,
                "message": "记录建议失败，请稍后重试",
                "error_code": "RECORD_FAILED"
            }, status.HTTP_500_INTERNAL_SERVER_ERROR
            
    except Exception as e:
        return {
            "success": False,
            "message": f"服务器错误: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/statistics")
async def get_feedback_statistics():
    """获取反馈统计信息"""
    feedback_system = get_feedback_system()
    stats = feedback_system.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/suggestions")
async def get_improvement_suggestions(limit: int = 100):
    """获取改进建议"""
    feedback_system = get_feedback_system()
    suggestions = feedback_system.get_improvement_suggestions(limit=limit)
    return {"success": True, "suggestions": suggestions}


@router.get("/disliked")
async def get_disliked_resources(limit: int = 50):
    """获取被点踩最多的资源"""
    feedback_system = get_feedback_system()
    resources = feedback_system.get_disliked_resources(limit=limit)
    return {"success": True, "resources": resources}


@router.get("/export")
async def export_feedback_data():
    """导出反馈数据"""
    feedback_system = get_feedback_system()
    export_path = feedback_system.export_feedback_data()
    if export_path:
        return {"success": True, "export_path": export_path}
    else:
        raise HTTPException(status_code=500, detail="导出失败")
