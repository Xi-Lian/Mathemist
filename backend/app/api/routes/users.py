"""
用户和备课历史管理路由模块

职责：
- 处理用户注册、登录、偏好设置
- 处理备课历史的创建、查询、搜索、删除

依赖：
- fastapi
- app.api.models (数据模型)
- app.core.user_system (用户系统)
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from app.api.models import (
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    UserPreferencesUpdateRequest,
    LessonPlanHistoryCreateRequest,
    LessonPlanHistoryUpdateRequest,
    LessonPlanHistoryResponse,
    SuccessResponse
)
from app.core.user_system import user_system

router = APIRouter()


@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreateRequest):
    try:
        user = user_system.create_user(
            username=request.username,
            email=request.email
        )
        
        if request.preferences:
            user = user_system.update_user_preferences(
                user.user_id,
                request.preferences
            )
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            preferences=user.preferences,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/login", response_model=UserResponse)
async def login_user(request: UserLoginRequest):
    try:
        user = user_system.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            preferences=user.preferences,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            preferences=user.preferences,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/preferences", response_model=UserResponse)
async def update_user_preferences(user_id: str, request: UserPreferencesUpdateRequest):
    try:
        user = user_system.update_user_preferences(user_id, request.preferences)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            preferences=user.preferences,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/lesson-plan-history", response_model=LessonPlanHistoryResponse)
async def create_lesson_plan_history(user_id: str, request: LessonPlanHistoryCreateRequest):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        history = user_system.create_lesson_plan_history(
            user_id=user_id,
            topic=request.topic,
            chapter=request.chapter,
            textbook=request.textbook,
            teaching_goals=request.teaching_goals,
            teaching_framework=request.teaching_framework,
            lesson_plan_content=request.lesson_plan_content,
            tags=request.tags,
            notes=request.notes
        )
        
        return LessonPlanHistoryResponse(
            history_id=history.history_id,
            user_id=history.user_id,
            topic=history.topic,
            chapter=history.chapter,
            textbook=history.textbook,
            teaching_goals=history.teaching_goals,
            teaching_framework=history.teaching_framework,
            lesson_plan_content=history.lesson_plan_content,
            status=history.status,
            created_at=history.created_at,
            updated_at=history.updated_at,
            tags=history.tags,
            notes=history.notes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/lesson-plan-history", response_model=List[LessonPlanHistoryResponse])
async def get_user_lesson_plan_history(
    user_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        histories = user_system.get_user_lesson_plan_history(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            LessonPlanHistoryResponse(
                history_id=h.history_id,
                user_id=h.user_id,
                topic=h.topic,
                chapter=h.chapter,
                textbook=h.textbook,
                teaching_goals=h.teaching_goals,
                teaching_framework=h.teaching_framework,
                lesson_plan_content=h.lesson_plan_content,
                status=h.status,
                created_at=h.created_at,
                updated_at=h.updated_at,
                tags=h.tags,
                notes=h.notes
            )
            for h in histories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/lesson-plan-history/search", response_model=List[LessonPlanHistoryResponse])
async def search_lesson_plan_history(
    user_id: str,
    keyword: str = Query(...),
    limit: int = Query(50, ge=1, le=100)
):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        histories = user_system.search_lesson_plan_history(
            user_id=user_id,
            keyword=keyword,
            limit=limit
        )
        
        return [
            LessonPlanHistoryResponse(
                history_id=h.history_id,
                user_id=h.user_id,
                topic=h.topic,
                chapter=h.chapter,
                textbook=h.textbook,
                teaching_goals=h.teaching_goals,
                teaching_framework=h.teaching_framework,
                lesson_plan_content=h.lesson_plan_content,
                status=h.status,
                created_at=h.created_at,
                updated_at=h.updated_at,
                tags=h.tags,
                notes=h.notes
            )
            for h in histories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/lesson-plan-history/{history_id}", response_model=LessonPlanHistoryResponse)
async def get_lesson_plan_history(user_id: str, history_id: str):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        history = user_system.get_lesson_plan_history(history_id)
        if not history:
            raise HTTPException(status_code=404, detail="备课历史不存在")
        
        if history.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问此备课历史")
        
        return LessonPlanHistoryResponse(
            history_id=history.history_id,
            user_id=history.user_id,
            topic=history.topic,
            chapter=history.chapter,
            textbook=history.textbook,
            teaching_goals=history.teaching_goals,
            teaching_framework=history.teaching_framework,
            lesson_plan_content=history.lesson_plan_content,
            status=history.status,
            created_at=history.created_at,
            updated_at=history.updated_at,
            tags=history.tags,
            notes=history.notes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/lesson-plan-history/{history_id}", response_model=LessonPlanHistoryResponse)
async def update_lesson_plan_history(
    user_id: str,
    history_id: str,
    request: LessonPlanHistoryUpdateRequest
):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        history = user_system.get_lesson_plan_history(history_id)
        if not history:
            raise HTTPException(status_code=404, detail="备课历史不存在")
        
        if history.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改此备课历史")
        
        update_kwargs = {}
        if request.topic is not None:
            update_kwargs["topic"] = request.topic
        if request.chapter is not None:
            update_kwargs["chapter"] = request.chapter
        if request.textbook is not None:
            update_kwargs["textbook"] = request.textbook
        if request.teaching_goals is not None:
            update_kwargs["teaching_goals"] = request.teaching_goals
        if request.teaching_framework is not None:
            update_kwargs["teaching_framework"] = request.teaching_framework
        if request.lesson_plan_content is not None:
            update_kwargs["lesson_plan_content"] = request.lesson_plan_content
        if request.status is not None:
            update_kwargs["status"] = request.status
        if request.tags is not None:
            update_kwargs["tags"] = request.tags
        if request.notes is not None:
            update_kwargs["notes"] = request.notes
        
        updated_history = user_system.update_lesson_plan_history(
            history_id,
            **update_kwargs
        )
        
        return LessonPlanHistoryResponse(
            history_id=updated_history.history_id,
            user_id=updated_history.user_id,
            topic=updated_history.topic,
            chapter=updated_history.chapter,
            textbook=updated_history.textbook,
            teaching_goals=updated_history.teaching_goals,
            teaching_framework=updated_history.teaching_framework,
            lesson_plan_content=updated_history.lesson_plan_content,
            status=updated_history.status,
            created_at=updated_history.created_at,
            updated_at=updated_history.updated_at,
            tags=updated_history.tags,
            notes=updated_history.notes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/lesson-plan-history/{history_id}", response_model=SuccessResponse)
async def delete_lesson_plan_history(user_id: str, history_id: str):
    try:
        user = user_system.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        history = user_system.get_lesson_plan_history(history_id)
        if not history:
            raise HTTPException(status_code=404, detail="备课历史不存在")
        
        if history.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除此备课历史")
        
        success = user_system.delete_lesson_plan_history(history_id)
        
        return SuccessResponse(
            success=success,
            message="备课历史删除成功" if success else "备课历史删除失败"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))