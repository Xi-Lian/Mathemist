"""
向量数据库构建模块
用于基于资源汇总表构建ChromaDB向量数据库
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import requests
import json
import time

import chromadb
from chromadb.config import Settings

from .resource_table_parser import ResourceTableParser
from .model_config import model_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 板块路径映射
BOARD_PATH_MAPPING = {
    "01-函数": "函数",
    "02-几何": "几何",
    "02- 立体几何": "几何",
    "02-立体几何": "几何",
    "03-概率与统计": "概率统计",
}

# 不需要分板块的资源类型（这些资源没有固定的板块归属）
RESOURCE_TYPES_NO_BOARD = {"theory", "优秀教案共性", "excellent_case"}

# 习题资源类型
EXERCISE_RESOURCE_TYPES = {"exercise", "习题", "题目"}


class ExerciseAnalyzer:
    """习题分析器（使用 DeepSeek）"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "sk-your-deepseek-api-key")
        self.llm_client = None
        self._init_llm_client()

    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            logger.info("习题分析器已使用 DeepSeek")
        except Exception as e:
            logger.warning(f"初始化LLM客户端失败: {e}")
    
    def analyze_exercise(self, exercise_data):
        """分析习题"""
        if not self.llm_client:
            logger.warning("LLM客户端未初始化，跳过分析")
            return {}
        
        content_parts = []
        
        for key, value in exercise_data.items():
            if key == 'analysis':
                continue
            
            if value and isinstance(value, str):
                if value.lower().endswith(('.png', '.jpg', '.jpeg')):
                    content_parts.append(f"{key}: [图片文件]")
                else:
                    content_parts.append(f"{key}: {value}")
        
        content_text = "\n".join(content_parts)
        
        prompt = """请详细分析以下数学题：

{content}

请按以下JSON格式返回分析结果：
{{
    "知识点": ["知识点1", "知识点2", ...],
    "题型": "选择题/填空题/解答题/证明题/计算题/应用题",
    "核心考点": "简要描述核心考察内容",
    "涉及公式": ["公式1", "公式2", ...],
    "解题思路": "简要描述解题思路",
    "考察能力": ["运算能力", "逻辑推理", "空间想象", "数学建模", "数据分析"],
    "题目分类": "基础题/综合题/压轴题",
    "是否需要画图": true/false,
    "预估解题时间": "分钟数"
}}

要求：
1. 知识点要具体（如"指数函数的单调性"而非"函数"）
2. 所有字段都要填写，不要留空
3. 解题思路要简明扼要
""".format(content=content_text)
        
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # 使用增强的JSON解析方法
            return self._parse_json_with_fallback(content)
        
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {}
    
    def _parse_json_with_fallback(self, content):
        """增强的JSON解析方法，包含多级回退策略"""
        if not content:
            logger.warning("LLM返回空内容")
            return {}
        
        import re
        
        # 策略1：直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 策略2：移除markdown代码块
        cleaned = content.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # 策略3：提取JSON对象并清理
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            json_str = json_match.group()
            
            # 策略4：处理数学公式中的特殊字符
            # 移除$符号（数学公式标记）
            cleaned_json = re.sub(r'\$([^$]+)\$', r'\1', json_str)
            
            # 处理转义问题 - 移除反斜杠或转义它们
            # 将 \s, \n, \t 等转义字符保留，但处理其他反斜杠
            cleaned_json = cleaned_json.replace('\\', '\\\\')
            
            # 恢复合法的JSON转义
            cleaned_json = cleaned_json.replace('\\\\n', '\\n')
            cleaned_json = cleaned_json.replace('\\\\t', '\\t')
            cleaned_json = cleaned_json.replace('\\\\r', '\\r')
            cleaned_json = cleaned_json.replace('\\\\"', '\\"')
            
            # 策略5：移除多余的空格和换行
            cleaned_json = cleaned_json.replace('\n', ' ').replace('\r', '')
            
            try:
                return json.loads(cleaned_json)
            except json.JSONDecodeError:
                pass
            
            # 策略6：处理JSON中的HTML实体
            cleaned_json = cleaned_json.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            try:
                return json.loads(cleaned_json)
            except json.JSONDecodeError:
                pass
            
            # 策略7：使用更宽松的JSON解析（容错解析）
            result = self._parse_json_tolerant(cleaned_json)
            if result:
                return result
            
            logger.error(f"JSON解析失败，尝试了所有策略")
            logger.error(f"原始内容片段: {content[:200]}...")
            return {}
        
        logger.error(f"未找到JSON对象，内容片段: {content[:100]}...")
        return {}
    
    def _parse_json_tolerant(self, json_str):
        """容错JSON解析器，处理常见格式问题"""
        import re
        
        try:
            # 尝试直接解析
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # 尝试修复常见问题
        fixed = json_str
        
        # 修复未转义的引号
        # 在值中找到未转义的引号并转义
        in_string = False
        escape = False
        result = []
        
        for i, char in enumerate(fixed):
            if escape:
                result.append(char)
                escape = False
            elif char == '\\':
                result.append(char)
                escape = True
            elif char == '"':
                if in_string:
                    # 检查前一个字符是否是冒号或逗号（属性名结束）
                    # 如果不是，可能是值中的引号
                    prev_pos = i - 1
                    while prev_pos >= 0 and fixed[prev_pos] in ' \t\n':
                        prev_pos -= 1
                    if prev_pos >= 0 and fixed[prev_pos] not in [':', ',', '{', '[']:
                        # 这可能是值中的引号，需要转义
                        result.append('\\')
                result.append(char)
                in_string = not in_string
            else:
                result.append(char)
        
        fixed = ''.join(result)
        
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.debug(f"容错解析失败: {str(e)[:50]}")
            return {}
    
    def _escape_quotes_in_values(self, json_str):
        """转义JSON值中的未转义引号"""
        import re
        
        # 找到所有在引号内的内容
        # 这是一个简化的实现，可能无法处理所有情况
        result = []
        in_string = False
        escape = False
        
        for char in json_str:
            if escape:
                result.append(char)
                escape = False
            elif char == '\\':
                result.append(char)
                escape = True
            elif char == '"':
                if in_string:
                    # 检查是否是有效的字符串结束
                    # 向前查找，看是否是属性名或值
                    result.append(char)
                    in_string = False
                else:
                    result.append(char)
                    in_string = True
            elif in_string and char == '"':
                # 在字符串内部的引号需要转义
                result.append('\\')
                result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)


class ExerciseAnalysisLoader:
    """加载已保存的习题分析结果"""

    def __init__(self, analysis_dir=None):
        if analysis_dir is None:
            self.analysis_dir = os.path.join(
                str(Path(__file__).parent.parent.parent.parent),
                'learning_resource',
                'exercise_analysis'
            )
        else:
            self.analysis_dir = analysis_dir

        self.analysis_cache = {}
        self.stem_cache = {}
        self._load_all_analysis()

    def _load_all_analysis(self):
        if not os.path.exists(self.analysis_dir):
            return

        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.analysis_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        exercise_id = data.get('exercise_id')
                        if exercise_id:
                            self.analysis_cache[exercise_id] = data

                        original_resource = data.get('original_resource', {})
                        source_file = original_resource.get('source_file', '') or data.get('source_file', '')
                        title = original_resource.get('title', '') or data.get('title', '')
                        stem = original_resource.get('题干', '') or data.get('题干', '')

                        if source_file and title:
                            cache_key = (source_file.lower().strip(), title.lower().strip())
                            self.stem_cache[cache_key] = data.get('analysis')
                        elif source_file:
                            cache_key = source_file.lower().strip()
                            self.stem_cache[cache_key] = data.get('analysis')

                        if stem:
                            stem_key = stem.lower().strip()[:200]
                            self.stem_cache[('stem', stem_key)] = data.get('analysis')
                except Exception as e:
                    logger.warning(f"加载分析结果失败: {filename}, {e}")

        logger.info(f"已加载 {len(self.analysis_cache)} 条分析结果")

    def get_analysis(self, resource):
        resource_type = resource.get('resource_type', '')
        source_file = resource.get('source_file', '')
        title = resource.get('title', '')
        stem = resource.get('题干', '')

        source_file_lower = source_file.lower().strip()
        title_lower = title.lower().strip()
        stem_lower = stem.lower().strip()[:200] if stem else ''

        if stem_lower:
            cache_key = ('stem', stem_lower)
            if cache_key in self.stem_cache:
                return self.stem_cache[cache_key]

        cache_key = (source_file_lower, title_lower)
        if cache_key in self.stem_cache:
            return self.stem_cache[cache_key]

        cache_key = source_file_lower
        if cache_key in self.stem_cache:
            return self.stem_cache[cache_key]

        exercise_id = f"{resource_type}_{hash(source_file + title) % 100000}"

        possible_ids = [
            exercise_id,
            f"{resource_type.lower()}_{hash(source_file + title) % 100000}",
            f"exercise_{hash(source_file + title) % 100000}",
        ]

        for eid in possible_ids:
            if eid in self.analysis_cache:
                return self.analysis_cache[eid].get('analysis')

        return None


class VectorDatabaseBuilder:
    """向量数据库构建器"""

    # 板块集合名称映射
    BOARD_COLLECTION_MAPPING = {
        "函数": "math_resources_function",
        "几何": "math_resources_geometry",
        "概率统计": "math_resources_probability",
        "代数": "math_resources_algebra",
        "通用": "math_resources_general",
    }

    @staticmethod
    def get_collection_name_by_board(board_name: str) -> str:
        """
        根据板块名称获取对应的集合名称

        Args:
            board_name: 板块名称

        Returns:
            集合名称
        """
        return VectorDatabaseBuilder.BOARD_COLLECTION_MAPPING.get(board_name, "math_resources")

    @staticmethod
    def get_collection_name_by_theme(core_theme: str, knowledge_hierarchy: Dict = None) -> str:
        """
        根据核心主题获取对应的板块集合名称

        Args:
            core_theme: 核心主题
            knowledge_hierarchy: 知识层次结构（可选）

        Returns:
            板块集合名称
        """
        if not core_theme:
            return "math_resources_general"

        theme_lower = core_theme.lower()

        # 统计相关的主题关键词
        statistics_keywords = ["概率", "统计", "抽样", "分层抽样", "随机抽样", "系统抽样",
                              "总体", "样本", "回归", "相关", "概率与统计"]

        # 函数相关的主题关键词
        function_keywords = ["函数", "单调性", "奇偶性", "周期性", "对称性", "零点",
                           "指数", "对数", "三角", "幂", "二次", "一次函数", "二次函数"]

        # 代数相关的主题关键词（优先级高于几何，因为"复数的几何意义"这类主题容易误判）
        algebra_keywords = ["代数", "复数", "虚数", "数系", "数系扩充", "复平面", "共轭复数", "几何意义"]

        # 几何相关的主题关键词（放在代数之后，避免"复数的几何意义"被误判为几何）
        geometry_keywords = ["几何", "立体几何", "平面几何", "解析几何", "向量", "空间",
                           "圆", "椭圆", "双曲线", "抛物线", "直线", "平面"]

        # 检查是否是统计相关主题
        if any(kw in core_theme for kw in statistics_keywords):
            return "math_resources_probability"
        # 检查是否是函数相关主题
        elif any(kw in core_theme for kw in function_keywords):
            return "math_resources_function"
        # 检查是否是代数相关主题（优先于几何）
        elif any(kw in core_theme for kw in algebra_keywords):
            return "math_resources_algebra"
        # 检查是否是几何相关主题
        elif any(kw in core_theme for kw in geometry_keywords):
            return "math_resources_geometry"

        if knowledge_hierarchy:
            theme_info = knowledge_hierarchy.get(core_theme, {})
            parent_topic = theme_info.get("parent_topic", "")
            if parent_topic:
                if "概率" in parent_topic or "统计" in parent_topic:
                    return "math_resources_probability"
                elif "函数" in parent_topic:
                    return "math_resources_function"
                elif "几何" in parent_topic:
                    return "math_resources_geometry"

        return "math_resources_general"
    
    def __init__(self, learning_resource_path: str, db_path: str = None):
        """
        初始化向量数据库构建器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
            db_path: 向量数据库存储路径
        """
        # 确保learning_resource_path是绝对路径
        input_path = Path(learning_resource_path).resolve()
        
        # 如果输入路径是learning_resource或learning-resource文件夹本身，使用它
        if (input_path.name == 'learning_resource' or input_path.name == 'learning-resource') and input_path.exists():
            self.learning_resource_path = input_path
        else:
            # 从backend/app/core/vector_database_builder.py向上查找项目根目录
            # __file__ = backend/app/core/vector_database_builder.py
            # parent.parent.parent = backend
            # parent.parent.parent.parent = Mathemist
            backend_dir = Path(__file__).parent.parent.parent
            lr_path = backend_dir / 'learning_resource'
            if lr_path.exists():
                self.learning_resource_path = lr_path
            else:
                # 尝试查找learning-resource文件夹（使用连字符）
                lr_path = backend_dir / 'learning-resource'
                if lr_path.exists():
                    self.learning_resource_path = lr_path
                else:
                    # 尝试从backend目录的上级目录查找
                    project_root = backend_dir.parent
                    lr_path = project_root / 'learning_resource'
                    if lr_path.exists():
                        self.learning_resource_path = lr_path
                    else:
                        # 尝试查找learning-resource文件夹（使用连字符）
                        lr_path = project_root / 'learning-resource'
                        if lr_path.exists():
                            self.learning_resource_path = lr_path
                        else:
                            # 尝试从当前工作目录向上查找
                            current_dir = Path.cwd()
                            for _ in range(5):  # 最多向上查找5级
                                lr_path = current_dir / 'learning_resource'
                                if lr_path.exists():
                                    self.learning_resource_path = lr_path
                                    break
                                # 尝试查找learning-resource文件夹（使用连字符）
                                lr_path = current_dir / 'learning-resource'
                                if lr_path.exists():
                                    self.learning_resource_path = lr_path
                                    break
                                current_dir = current_dir.parent
                            else:
                                # 如果仍然找不到，使用输入路径作为learning_resource路径
                                self.learning_resource_path = input_path
        
        # 打印最终使用的learning_resource路径
        logger.info(f"使用learning_resource路径: {self.learning_resource_path}")
        
        # 使用正确的learning_resource_path初始化ResourceTableParser
        self.parser = ResourceTableParser(str(self.learning_resource_path))
        # 使用全局单例model_config，避免重复创建模型实例
        self.model_config = model_config
        
        # 设置数据库路径
        if db_path is None:
            # 默认路径：backend/chroma_db（与服务实际使用的路径一致）
            current_dir = Path(__file__).parent.parent.parent
            db_path = current_dir / 'chroma_db'
        
        self.db_path = Path(db_path).resolve()
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB配置
        self.COLLECTION_NAME = "math_resources"
        
        # 初始化习题分析器
        self.exercise_analyzer = None
        deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY', 'sk-b1bbbcbf88504b1c96e70da79772ff16')
        if deepseek_api_key:
            try:
                self.exercise_analyzer = ExerciseAnalyzer(deepseek_api_key)
                logger.info("习题分析器初始化成功")
            except Exception as e:
                logger.warning(f"习题分析器初始化失败: {e}")
        
        # 初始化分析结果加载器（优先使用已保存的分析结果）
        self.analysis_loader = ExerciseAnalysisLoader()
    
    def _resolve_image_paths(self, resource):
        """
        解析资源中的图片路径
        
        Args:
            resource: 资源字典
        
        Returns:
            处理后的资源字典（图片字段转换为完整URL）
        """
        processed = resource.copy()
        
        # 云端存储基础URL
        base_urls = [
            "https://math-1415627924.cos.ap-guangzhou.myqcloud.com/math-teaching-resources/",
            "https://math-1415627924.cos.ap-guangzhou.myqcloud.com/"
        ]
        
        # 获取基础路径
        cloud_link = resource.get('云端链接', '')
        base_path = ""
        
        if cloud_link:
            # 从云端链接提取基础路径
            for url in base_urls:
                if url in cloud_link:
                    base_path = cloud_link[:cloud_link.rfind('/') + 1]
                    break
        
        # 如果没有找到基础路径，使用默认路径
        if not base_path:
            base_path = base_urls[0]
        
        # 处理所有字段中的图片
        for key, value in processed.items():
            if isinstance(value, str):
                # 检查是否是图片文件名（只有文件名，没有路径）
                if (value.endswith('.png') or value.endswith('.jpg') or value.endswith('.jpeg')) and '/' not in value:
                    # 构建完整URL
                    full_url = base_path + value
                    processed[key] = full_url
                    logger.debug(f"    解析图片路径: {key} = {value} -> {full_url}")
        
        return processed
        
    def get_chroma_client(self) -> chromadb.Client:
        """
        获取ChromaDB客户端
        
        Returns:
            ChromaDB客户端
        """
        client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        return client
    
    def get_embedding_model(self):
        """
        获取embedding模型
        
        Returns:
            embedding模型
        """
        return self.model_config.get_embedding_model()
    
    def _get_resource_board(self, source_file: str, resource_type: str, title: str = "") -> str:
        """
        根据资源路径和标题获取资源所属板块

        Args:
            source_file: 资源路径
            resource_type: 资源类型
            title: 资源标题

        Returns:
            板块名称，如果无法确定则返回None
        """
        if resource_type in RESOURCE_TYPES_NO_BOARD:
            return "通用"

        if not source_file:
            return None

        # 首先检查文件名、标题或路径是否包含复数或虚数
        filename = source_file.split("/")[-1]
        
        # V42.0新增：从课件汇总表文件名中提取板块信息
        # 课件汇总表文件名格式："函数-课件汇总.xlsx"、"立体几何-课件汇总.xlsx"、"概率与统计-课件汇总.xlsx"
        if "-课件汇总" in filename:
            if "函数" in filename:
                logger.info(f"从课件汇总表文件名中提取到板块: '函数'")
                return "函数"
            elif "立体几何" in filename or "几何" in filename:
                logger.info(f"从课件汇总表文件名中提取到板块: '几何'")
                return "几何"
            elif "概率与统计" in filename or "概率统计" in filename:
                logger.info(f"从课件汇总表文件名中提取到板块: '概率统计'")
                return "概率统计"
            elif "代数" in filename:
                logger.info(f"从课件汇总表文件名中提取到板块: '代数'")
                return "代数"

        # V43.0修复：课件资源直接按汇总表文件名分类，不再检查课件本身的文件名
        if resource_type == 'courseware':
            # 课件资源已经通过课件汇总表文件名确定了板块，直接返回（已在前面处理）
            # 如果到这里还没返回，说明汇总表文件名没有匹配到已知板块
            logger.debug(f"课件资源未能从汇总表文件名确定板块: {source_file}")
            return None

        if "复数" in filename or "虚数" in filename or "复数" in title or "虚数" in title or "复数" in source_file or "虚数" in source_file:
            logger.info(f"从文件名、标题或路径中提取到板块: '代数' (包含复数/虚数)")
            return "代数"

        # 特殊处理 GGB 资源
        if resource_type == 'ggb':
            if "函数" in filename:
                logger.info(f"从文件名中提取到板块: '函数' (GGB资源)")
                return "函数"
            elif "几何" in filename:
                logger.info(f"从文件名中提取到板块: '几何' (GGB资源)")
                return "几何"
            elif "概率" in filename or "统计" in filename:
                logger.info(f"从文件名中提取到板块: '概率统计' (GGB资源)")
                return "概率统计"

        # 特殊处理教学大纲资源
        if resource_type == 'syllabus':
            if "函数" in filename:
                logger.info(f"从文件名中提取到板块: '函数' (教学大纲资源)")
                return "函数"
            elif "几何" in filename:
                logger.info(f"从文件名中提取到板块: '几何' (教学大纲资源)")
                return "几何"
            elif "概率" in filename or "统计" in filename:
                logger.info(f"从文件名中提取到板块: '概率统计' (教学大纲资源)")
                return "概率统计"

        # 调试信息
        logger.debug(f"检查资源路径: '{source_file}'")
        logger.debug(f"板块路径映射: {BOARD_PATH_MAPPING}")

        # 首先尝试匹配路径前缀（适用于本地资源）
        for path_prefix, board_name in BOARD_PATH_MAPPING.items():
            if path_prefix in source_file:
                logger.debug(f"匹配到路径前缀: '{path_prefix}', 板块: '{board_name}'")
                return board_name

        # 然后尝试从路径中提取板块信息（适用于云端资源）
        # 云端资源路径格式：math-teaching-resources/03-概率与统计/01-教案/目录/文件名
        if "/" in source_file:
            parts = source_file.split("/")
            # 查找板块名称 - 检查路径部分是否包含板块名称或路径前缀
            for part in parts:
                # 先检查是否匹配路径前缀（如"03-概率与统计"）
                for path_prefix, board_name in BOARD_PATH_MAPPING.items():
                    if path_prefix in part:
                        logger.debug(f"从路径中提取到板块前缀: '{path_prefix}', 板块: '{board_name}' (from part '{part}')")
                        return board_name
                # 再检查是否包含板块名称（如"概率统计"）
                for board_name in BOARD_PATH_MAPPING.values():
                    if board_name in part:
                        logger.debug(f"从路径中提取到板块: '{board_name}' (from part '{part}')")
                        return board_name
                # 特殊处理：检查路径部分是否包含板块名称的变体
                # 例如"概率与统计"包含"概率统计"
                if '概率' in part:
                    logger.debug(f"从路径中提取到板块: '概率统计' (from part '{part}')")
                    return "概率统计"
                if '函数' in part:
                    logger.debug(f"从路径中提取到板块: '函数' (from part '{part}')")
                    return "函数"
                if '几何' in part:
                    logger.debug(f"从路径中提取到板块: '几何' (from part '{part}')")
                    return "几何"

        # 最后尝试从文件名中提取板块信息
        # 特殊处理概率与统计板块（文件名可能包含"概率与统计"但我们需要返回"概率统计"）
        if "概率与统计" in filename:
            logger.debug(f"从文件名中提取到板块: '概率统计'")
            return "概率统计"
        # 特殊处理代数板块
        if "代数" in filename:
            logger.info(f"从文件名中提取到板块: '代数'")
            return "代数"
        # 处理其他板块
        for board_name in BOARD_PATH_MAPPING.values():
            if board_name in filename:
                logger.debug(f"从文件名中提取到板块: '{board_name}'")
                return board_name

        logger.debug(f"未匹配到任何板块路径前缀")
        return None

    def build_vector_database(self, force_rebuild: bool = False, batch_size: int = 50) -> bool:
        """
        构建向量数据库（分板块版本）

        Args:
            force_rebuild: 是否强制重建数据库
            batch_size: 分批生成向量和写库的批次大小

        Returns:
            是否构建成功
        """
        try:
            # 获取ChromaDB客户端
            client = self.get_chroma_client()

            # 检查集合是否存在
            collection_exists = self.COLLECTION_NAME in [col.name for col in client.list_collections()]

            if collection_exists and not force_rebuild:
                logger.info(f"向量数据库已存在: {self.db_path}")
                logger.info("如需重新构建，请使用 force_rebuild=True")
                return True

            # 如果存在且需要重建，删除旧集合
            if collection_exists and force_rebuild:
                logger.info("删除旧向量数据库...")
                client.delete_collection(name=self.COLLECTION_NAME)

            # 解析所有资源汇总表
            logger.info("解析资源汇总表...")
            all_resources = self.parser.parse_all_tables()

            # 需要在代数和几何板块共享的资源类型
            SHARED_RESOURCE_TYPES = {"exercise", "习题", "题目", "lesson_case", "课例", "courseware", "课件", "syllabus", "教学大纲"}

            # 按板块分组资源
            board_resources: Dict[str, Dict[str, List]] = {
                "函数": {},
                "几何": {},
                "概率统计": {},
                "代数": {},
                "通用": {},
            }

            # 获取embedding模型
            embedding_model = self.get_embedding_model()

            # 先统计各板块资源数量
            total_resources = 0
            for resource_type, resources in all_resources.items():
                for resource in resources:
                    source_file = resource.get('source_file', '')
                    title = resource.get('title', '')
                    board = self._get_resource_board(source_file, resource_type, title)
                    if board:
                        if resource_type not in board_resources[board]:
                            board_resources[board][resource_type] = []
                        board_resources[board][resource_type].append(resource)
                        total_resources += 1

            # 将几何板块的习题、课例、课件、教学大纲共享给代数板块
            for resource_type in SHARED_RESOURCE_TYPES:
                if resource_type in board_resources.get("几何", {}):
                    resources_to_share = board_resources["几何"][resource_type]
                    if resources_to_share:
                        if resource_type not in board_resources["代数"]:
                            board_resources["代数"][resource_type] = []
                        # 深拷贝资源并修改板块标记
                        for res in resources_to_share:
                            shared_res = res.copy()
                            shared_res['_source_board'] = '几何'
                            board_resources["代数"][resource_type].append(shared_res)
                        logger.info(f"将几何板块的{resource_type}资源共享给代数板块: {len(resources_to_share)}条")

            logger.info(f"资源统计：总计{total_resources}条资源")
            for board, types in board_resources.items():
                board_total = sum(len(res) for res in types.values())
                if board_total > 0:
                    logger.info(f"  - {board}板块: {board_total}条")

            # 创建板块集合并写入数据
            total_written = 0
            for board_name, collection_name in self.BOARD_COLLECTION_MAPPING.items():
                if board_name not in board_resources:
                    continue

                board_data = board_resources[board_name]
                board_total = sum(len(res) for res in board_data.values())

                if board_total == 0:
                    logger.info(f"跳过空的板块集合: {board_name}")
                    continue

                # 删除旧集合（如果存在）
                if collection_name in [col.name for col in client.list_collections()]:
                    logger.info(f"删除旧板块集合: {collection_name}")
                    client.delete_collection(name=collection_name)

                # 创建新集合
                logger.info(f"创建板块集合: {collection_name}")
                collection = client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": f"数学教学资源向量数据库 - {board_name}板块",
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 200,
                        "hnsw:M": 16
                    }
                )

                resource_id = 0
                # 处理该板块下所有类型的资源
                for resource_type, resources in board_data.items():
                    logger.info(f"  处理{board_name}-{resource_type}资源，共{len(resources)}条...")

                    batch_documents = []
                    batch_metadatas = []
                    batch_ids = []

                    for resource in resources:
                        # ===== 习题资源特殊处理：先加载分析结果 =====
                        analysis = None
                        if resource_type.lower() in EXERCISE_RESOURCE_TYPES:
                            logger.debug(f"    处理习题资源: {resource.get('title', '未知')}")

                            # 优先从已保存的分析结果中获取
                            if self.analysis_loader:
                                analysis = self.analysis_loader.get_analysis(resource)

                            # 如果没有保存的分析结果，调用LLM分析
                            if analysis is None and self.exercise_analyzer:
                                logger.debug(f"    调用LLM分析习题")
                                processed_resource = self._resolve_image_paths(resource)
                                analysis = self.exercise_analyzer.analyze_exercise(processed_resource)
                                time.sleep(1)  # 避免请求过快

                            # 如果有分析结果，写入resource（format_resource_for_search会读取）
                            if analysis:
                                resource['analysis'] = analysis
                        # =============================================

                        # 格式化资源为搜索文本（此时analysis已加载，format_resource_for_search会读取analysis）
                        document = self.parser.format_resource_for_search(resource)

                        # 准备元数据
                        from ..config.resource_type_config import get_db_type
                        db_resource_type = get_db_type(resource_type) or resource_type
                        filtered_resource = {k: v for k, v in resource.items() if k not in ['resource_type', 'source_file', 'title', 'analysis']}
                        
                        # 【V64.0改进】确保 analysis_json 字段被正确写入元数据
                        if 'analysis' in resource and resource['analysis']:
                            try:
                                filtered_resource['analysis_json'] = json.dumps(resource['analysis'], ensure_ascii=False)
                                logger.debug(f"    [V64.0] 已为 {resource.get('title', '')} 注入 analysis_json")
                            except Exception as e:
                                logger.warning(f"    [V64.0] 序列化 analysis 失败: {e}")
                        
                        metadata = {
                            'resource_type': db_resource_type,
                            'source_file': resource.get('source_file', ''),
                            'title': resource.get('title', ''),
                            'board': board_name,  # 添加板块信息到元数据
                            **filtered_resource
                        }

                        batch_documents.append(document)
                        batch_metadatas.append(metadata)
                        batch_ids.append(f"{board_name}_{resource_type}_{resource_id}")
                        resource_id += 1

                        if len(batch_documents) >= batch_size:
                            logger.info(f"    批量生成向量并写库: {resource_type}, 批次大小={len(batch_documents)}")
                            embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
                            collection.add(
                                documents=batch_documents,
                                metadatas=batch_metadatas,
                                ids=batch_ids,
                                embeddings=embeddings
                            )
                            total_written += len(batch_documents)
                            batch_documents = []
                            batch_metadatas = []
                            batch_ids = []

                    if batch_documents:
                        logger.info(f"    批量生成向量并写库: {resource_type}, 批次大小={len(batch_documents)}")
                        embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
                        collection.add(
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                            ids=batch_ids,
                            embeddings=embeddings
                        )
                        total_written += len(batch_documents)

                logger.info(f"{board_name}板块集合构建完成，共{total_written}条记录")

            logger.info(f"向量数据库构建完成，共{total_written}条记录")
            logger.info(f"数据库路径: {self.db_path}")
            logger.info(f"板块集合: {list(self.BOARD_COLLECTION_MAPPING.values())}")

            return True

        except Exception as e:
            logger.error(f"构建向量数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_database_exists(self) -> bool:
        """
        检查向量数据库是否存在
        
        Returns:
            是否存在
        """
        try:
            client = self.get_chroma_client()
            collections = client.list_collections()
            collection_names = [col.name for col in collections]
            
            # 检查分板块集合是否存在
            expected_collections = list(self.BOARD_COLLECTION_MAPPING.values())
            existing_board_collections = [col for col in collection_names if col in expected_collections]
            
            # 如果至少有一个板块集合存在，就认为数据库存在
            return len(existing_board_collections) > 0
        except Exception as e:
            logger.error(f"检查向量数据库失败: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            client = self.get_chroma_client()
            collection = client.get_collection(name=self.COLLECTION_NAME)
            
            count = collection.count()
            
            # 获取所有资源的类型统计
            results = collection.get(include=['metadatas'])
            type_stats = {}
            
            for metadata in results['metadatas']:
                resource_type = metadata.get('resource_type', 'unknown')
                type_stats[resource_type] = type_stats.get(resource_type, 0) + 1
            
            return {
                'total_count': count,
                'type_stats': type_stats,
                'db_path': str(self.db_path)
            }
            
        except Exception as e:
            logger.error(f"获取向量数据库统计信息失败: {str(e)}")
            return {
                'total_count': 0,
                'type_stats': {},
                'db_path': str(self.db_path),
                'error': str(e)
            }
    
    def reset_database(self) -> bool:
        """
        重置向量数据库
        
        Returns:
            是否重置成功
        """
        try:
            client = self.get_chroma_client()
            
            # 删除集合
            if self.COLLECTION_NAME in [col.name for col in client.list_collections()]:
                client.delete_collection(name=self.COLLECTION_NAME)
                logger.info("向量数据库已删除")
            
            return True
            
        except Exception as e:
            logger.error(f"重置向量数据库失败: {str(e)}")
            return False
