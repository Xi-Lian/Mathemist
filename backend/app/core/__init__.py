"""
核心功能模块

提供数学智能助手的各项核心功能：
- 模型配置和管理
- 资源分类
- 资源检索
- 意图理解
- 教案生成
- 可视化建议
- GGB设计建议
- 响应构建
"""

from .model_config import (
    ModelConfig,
    model_config,
    get_model,
    get_embedding_model,
    get_chroma_client,
    get_content_processor
)

from .resource_classifier import (
    ResourceClassifier,
    classify_resource
)

from .resource_retriever import (
    ResourceRetriever,
    retrieve_resources
)

from .intent_analyzer import (
    IntentAnalyzer,
    intent_understanding_node
)

from .lesson_plan_generator import (
    LessonPlanGenerator,
    lesson_plan_generation_node
)

from .visualization_advisor import (
    VisualizationAdvisor,
    visualization_suggestions_node
)

from .ggb_design_advisor import (
    GGBDesignAdvisor,
    generate_ggb_innovation_suggestions
)

from .response_builder import (
    ResponseBuilder,
    response_formatting_node
)

from .unified_lesson_plan_system import (
    UnifiedLessonPlanSystem,
    unified_lesson_plan_system
)

from .lesson_plan_exporter import (
    LessonPlanExporter,
    lesson_plan_exporter,
    export_lesson_plan_all
)

from .user_system import (
    UserSystem,
    user_system
)

__all__ = [
    # 模型配置
    "ModelConfig",
    "model_config",
    "get_model",
    "get_embedding_model",
    "get_chroma_client",
    "get_content_processor",
    
    # 资源分类
    "ResourceClassifier",
    "classify_resource",
    
    # 资源检索
    "ResourceRetriever",
    "retrieve_resources",
    
    # 意图理解
    "IntentAnalyzer",
    "intent_understanding_node",
    
    # 教案生成（核心引擎，向后兼容）
    "LessonPlanGenerator",
    "lesson_plan_generation_node",
    
    # 统一教案系统
    "UnifiedLessonPlanSystem",
    "unified_lesson_plan_system",
    
    # 可视化建议
    "VisualizationAdvisor",
    "visualization_suggestions_node",
    
    # GGB设计建议
    "GGBDesignAdvisor",
    "generate_ggb_innovation_suggestions",
    
    # 响应构建
    "ResponseBuilder",
    "response_formatting_node",
    
    # 教案导出
    "LessonPlanExporter",
    "lesson_plan_exporter",
    "export_lesson_plan_all",
    
    # 用户系统
    "UserSystem",
    "user_system"
]
