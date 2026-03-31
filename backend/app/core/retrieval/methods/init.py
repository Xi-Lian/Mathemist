from .._shared import *


class _InitMixin:
    def __init__(self, learning_resource_path: str = None):
        """
        初始化资源检索器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        self.model_config = model_config
        
        if learning_resource_path is None:
            current_dir = Path(__file__).parent.parent.parent
            learning_resource_path = current_dir / 'learning_resource'
        
        self.learning_resource_path = Path(learning_resource_path).resolve()
        
        self.vector_db_builder = VectorDatabaseBuilder(str(self.learning_resource_path))
        self.parser = ResourceTableParser(str(self.learning_resource_path))
        
        self.content_extractor = get_content_feature_extractor()
        
        from ...grade_metadata_enricher import get_grade_enricher
        self.grade_enricher = get_grade_enricher()
        
        from ...content_feature_extractor import SubjectiveIntentInterpreter
        self.subjective_interpreter = SubjectiveIntentInterpreter()
        
        # 初始化主题匹配器
        self.theme_matcher = get_theme_matcher()
        
        # V60.0改进：使用动态配置加载器，从配置文件加载知识点层级结构
        # 这样当资源库扩展时，只需更新配置文件，无需修改代码
        self.config_loader = get_config_loader()
        self.knowledge_hierarchy = self.config_loader.get_knowledge_hierarchy()
        
        # V60.0改进：从配置文件加载意图模式
        self.query_intent_patterns = self.config_loader.get_intent_patterns()
        
        # V53.1改进：动态生成相关主题列表，基于knowledge_hierarchy
        # 不再硬编码具体主题，而是从knowledge_hierarchy中提取所有主题
        self.all_themes = self.config_loader.get_all_themes()
        
        # V60.0改进：使用配置加载器动态获取函数相关主题
        # 通过parent_topic判断，而不是硬编码关键词
        self.function_related_themes = self.config_loader.get_function_related_themes()
        
        # V53.1改进：动态生成所有主题的关键词列表
        # 用于年级匹配等场景，避免硬编码
        self.all_theme_keywords = self.config_loader.get_all_keywords()
    
    # V51.0改进：动态查询意图识别方法
