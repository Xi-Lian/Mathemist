import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
import re

class LightweightSemanticMatcher:
    def __init__(self):
        self.word_vectors = None
        self._load_word_vectors()
        # 语义要求关键词映射
        self.requirement_keywords = {
            '互动性强': ['互动', '讨论', '小组', '活动', '问答', '游戏', '参与', '交流'],
            '互动性': ['互动', '讨论', '小组', '活动', '问答'],
            '互动': ['互动', '讨论', '活动'],
            '课堂互动': ['互动', '讨论', '小组', '课堂'],
            '小组讨论': ['小组', '讨论', '合作'],
            '活动': ['活动', '互动', '游戏'],
            '生动有趣': ['有趣', '生动', '趣味', '游戏', '故事'],
            '有趣': ['有趣', '趣味', '游戏'],
            '生动': ['生动', '形象', '具体'],
            '趣味': ['趣味', '有趣', '游戏'],
            '游戏化': ['游戏', '趣味', '互动'],
            '深入浅出': ['易懂', '简单', '清晰', '明白'],
            '易懂': ['易懂', '简单', '明白'],
            '简单明了': ['简单', '明了', '清晰'],
            '容易理解': ['容易', '理解', '明白'],
            '探究式': ['探究', '自主', '发现', '探索'],
            '探究': ['探究', '探索', '发现'],
            '自主学习': ['自主', '自学', '独立'],
            '发现学习': ['发现', '探索', '自主'],
            '启发性': ['启发', '引导', '思考', '提问'],
            '启发': ['启发', '引导', '思考'],
            '引导': ['引导', '启发', '指导'],
            '思考': ['思考', '思维', '分析'],
            '系统性': ['系统', '完整', '全面', '体系'],
            '系统': ['系统', '体系', '完整'],
            '完整': ['完整', '全面', '系统'],
            '全面': ['全面', '完整', '系统']
        }
        
        # 资源类型分类
        self.RESOURCE_TYPE_CATEGORIES = {
            '教案类': {'教案', '教学设计', '教学方案', '教学计划', '备课', '导学案', '详案', '简案', '教学反思'},
            '课件类': {'课件', 'PPT', '幻灯片', '演示文稿', '课件资源'},
            '习题类': {'习题', '题目', '练习题', '选择题', '填空题', '解答题', '证明题', '测试题'},
            '大纲类': {'教学大纲', '大纲', '课程标准', '课程计划'},
            '理论类': {'理论', '理论卡片', '知识点', '概念', '定义'},
            '案例类': {'案例', '优秀教案', '优秀案例', '示范课'}
        }
    
    def _load_word_vectors(self):
        try:
            model_path = os.path.join(os.path.dirname(__file__), "word2vec.model")
            if os.path.exists(model_path):
                from gensim.models import KeyedVectors
                self.word_vectors = KeyedVectors.load(model_path)
                print("[INFO] 加载本地词向量模型成功")
            else:
                print("[INFO] 未找到词向量模型，使用关键词匹配作为回退")
                self.word_vectors = None
        except Exception as e:
            print(f"[ERROR] 加载词向量模型失败: {e}")
            self.word_vectors = None
    
    def _get_resource_category(self, resource_type):
        """获取资源类型所属类别"""
        resource_type = resource_type.lower() if resource_type else ''
        for category, types in self.RESOURCE_TYPE_CATEGORIES.items():
            if any(t.lower() in resource_type for t in types):
                return category
        return '其他'
    
    def _get_content_for_semantic_matching(self, doc, meta):
        """
        根据资源类型选择最合适的内容进行语义匹配
        
        Args:
            doc: 文档内容
            meta: 文档元数据（包含resource_type等信息）
        
        Returns:
            用于语义匹配的内容字符串
        """
        resource_type = meta.get('resource_type', '')
        category = self._get_resource_category(resource_type)
        
        title = meta.get('title', '')
        description = meta.get('description', '')
        source_file = meta.get('source_file', '')
        knowledge_tags = meta.get('知识点', '') or meta.get('知识点标签', '')
        
        # 根据资源类型选择不同的内容
        if category == '教案类':
            # 教案类：重点关注教学过程、教学方法、活动设计
            # 使用文档内容（教学过程）+ 标题 + 知识点
            content = f"{doc or ''} {title} {knowledge_tags}"
            return content
            
        elif category == '课件类':
            # 课件类：重点关注课件内容摘要、设计思路、教学用途
            # 使用文档内容（课件要点）+ 标题 + 描述 + 教学用途
            teaching_use = meta.get('教学用途', '') or meta.get('usage', '')
            content = f"{doc or ''} {title} {description} {teaching_use}"
            return content
            
        elif category == '习题类':
            # 习题类：重点关注题目描述、解答过程、难度
            # 使用文档内容（题目+解答）+ 标题 + 难度信息
            difficulty = meta.get('难度', '') or meta.get('difficulty', '')
            content = f"{doc or ''} {title} {difficulty} {knowledge_tags}"
            return content
            
        elif category == '大纲类':
            # 大纲类：重点关注课程目标、教学内容、课时安排
            # 使用文档内容 + 标题 + 知识点
            content = f"{doc or ''} {title} {knowledge_tags}"
            return content
            
        elif category == '理论类':
            # 理论类：重点关注概念定义、原理说明
            # 使用文档内容 + 标题 + 知识点
            content = f"{doc or ''} {title} {knowledge_tags}"
            return content
            
        elif category == '案例类':
            # 案例类：重点关注案例描述、分析过程
            # 使用文档内容 + 标题 + 描述
            content = f"{doc or ''} {title} {description}"
            return content
            
        elif resource_type.lower() == 'ggb' or 'ggb' in resource_type.lower():
            # GGB资源：重点关注教学用途、演示步骤、章节信息
            # V41.4新增：确保教学用途字段被包含在匹配中
            teaching_use = meta.get('教学用途', '') or meta.get('purpose', '')
            chapter = meta.get('章节', '')
            steps = meta.get('演示步骤', '') or meta.get('作图步骤', '')
            filename = meta.get('ggb文件名', '')
            content = f"{doc or ''} {title} {teaching_use} {chapter} {steps} {filename} {knowledge_tags}"
            return content
            
        else:
            # 默认：使用所有可用内容
            content = f"{doc or ''} {title} {description} {knowledge_tags}"
            return content
    
    def encode_text(self, text):
        if not text:
            return np.zeros(100)
        
        if self.word_vectors is None:
            return self._keyword_based_encode(text)
        
        words = text.split()
        vectors = []
        for word in words:
            if word in self.word_vectors:
                vectors.append(self.word_vectors[word])
        
        if vectors:
            return np.mean(vectors, axis=0)
        else:
            return np.zeros(self.word_vectors.vector_size)
    
    def _keyword_based_encode(self, text):
        features = []
        
        for req, keywords in self.requirement_keywords.items():
            count = sum(1 for kw in keywords if kw in text)
            features.append(count)
        
        char_counts = {}
        for char in text[:100]:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        common_chars = ['的', '是', '在', '有', '和', '了', '我', '你', '他', '她']
        for char in common_chars:
            features.append(char_counts.get(char, 0))
        
        if features:
            max_val = max(features) if max(features) > 0 else 1
            features = [f / max_val for f in features]
        
        while len(features) < 100:
            features.append(0.0)
        
        return np.array(features[:100])
    
    def calculate_similarity(self, text1, text2):
        keyword_similarity = self._keyword_based_similarity(text1, text2)
        if keyword_similarity > 0:
            return keyword_similarity
        
        vec1 = self.encode_text(text1)
        vec2 = self.encode_text(text2)
        
        try:
            similarity = cosine_similarity([vec1], [vec2])[0][0]
            return float(similarity)
        except:
            return self._jaccard_similarity(text1, text2)
    
    def calculate_similarity_with_resource_type(self, requirement, doc, meta):
        """
        根据资源类型计算语义相似度
        
        Args:
            requirement: 用户的语义要求（如"互动性强"）
            doc: 文档内容
            meta: 文档元数据（包含resource_type）
        
        Returns:
            语义相似度分数 (0-1)
        """
        content = self._get_content_for_semantic_matching(doc, meta)
        return self.calculate_similarity(requirement, content)
    
    def _keyword_based_similarity(self, requirement, content):
        if requirement in self.requirement_keywords:
            keywords = self.requirement_keywords[requirement]
            matched = sum(1 for kw in keywords if kw in content)
            if matched > 0:
                return matched / len(keywords)
        return 0.0
    
    def _jaccard_similarity(self, text1, text2):
        words1 = set(re.findall(r'[\u4e00-\u9fa5]+', text1))
        words2 = set(re.findall(r'[\u4e00-\u9fa5]+', text2))
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

semantic_matcher = LightweightSemanticMatcher()