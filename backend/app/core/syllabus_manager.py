import os
import re
from pathlib import Path
from typing import Dict, List

# 繁简体转换映射表
TRADITIONAL_TO_SIMPLIFIED = {
    '數': '数', '學': '学', '函': '函', '三': '三', '角': '角', '函': '函',
    '幾': '几', '何': '何', '立': '立', '體': '体', '平': '平', '面': '面', '向': '向',
    '量': '量', '解': '解', '析': '析', '概': '概', '念': '念', '性': '性', '質': '质',
    '冪': '幂', '指': '指', '對': '对', '導': '导', '應': '应', '用': '用',
    '列': '列', '機': '机', '率': '率', '統': '统', '計': '计', '原': '原', '理': '理'
}

def _traditional_to_simplified(text: str) -> str:
    """将繁体中文转换为简体中文"""
    result = []
    for char in text:
        result.append(TRADITIONAL_TO_SIMPLIFIED.get(char, char))
    return ''.join(result)

# 学习资源目录路径 - 使用绝对路径，确保从任何目录启动都能找到
# 优先使用环境变量，如果没有则使用相对于本文件的路径
env_path = os.environ.get('LEARNING_RESOURCE_PATH')
if env_path:
    LEARNING_RESOURCE_PATH = Path(env_path)
else:
    # 本文件位于 backend/app/core/syllabus_manager.py
    # 路径层级: syllabus_manager.py -> core -> app -> backend -> Mathemist -> learning_resource
    CURRENT_FILE = Path(__file__).resolve()
    # 向上跳4级: core -> app -> backend -> Mathemist
    PROJECT_ROOT = CURRENT_FILE.parent.parent.parent.parent
    LEARNING_RESOURCE_PATH = PROJECT_ROOT / 'learning_resource'

class SyllabusManager:
    """教学大纲管理器 - 启动时加载，内存索引，支持关键词+语义混合检索"""
    
    def __init__(self):
        self.chapters: Dict[str, dict] = {}  # 章节索引
        self.vector_model = None  # 轻量级向量化模型
        self._chapter_terms = []  # 动态提取的章节术语列表（从文件中自动获取）
        self._initialize()
    
    def _initialize(self):
        """启动时一次性初始化：加载文件 + 解析章节 + 生成向量"""
        # 1. 加载轻量级向量化模型
        self._load_vector_model()
        
        # 2. 加载并解析所有大纲文件
        self._load_all_syllabus()
    
    def _load_vector_model(self):
        """加载轻量级语义向量化模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.vector_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[INFO] 语义向量化模型加载成功")
        except Exception as e:
            self.vector_model = None
            import traceback
            print("[WARNING] 语义向量化模型加载失败, 将使用纯关键词匹配模式")
            print("[WARNING] 错误信息: " + str(e)[:200])
    
    def _load_all_syllabus(self):
        """加载所有大纲文件并解析章节"""
        syllabus_patterns = ["*教学大纲*.md", "*课程标准*.md"]
        
        for pattern in syllabus_patterns:
            for filepath in LEARNING_RESOURCE_PATH.glob(pattern):
                self._parse_syllabus_file(filepath)
    
    def _parse_syllabus_file(self, filepath: Path):
        """解析单个大纲文件，提取章节内容"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 按主题块解析：主题标题(#) + 多个章节(##) + 教学提示 + 学业要求
            current_topic = ""
            topic_content = ""
            chapters_in_topic = []
            
            for line in lines:
                # 主题标题
                if line.startswith('# '):
                    # 处理前一个主题
                    if current_topic and chapters_in_topic:
                        self._add_topic_with_chapters(current_topic, topic_content, chapters_in_topic, filepath.name)
                    
                    current_topic = line[2:].strip()
                    topic_content = line + '\n'
                    chapters_in_topic = []
                
                # 章节标题
                elif line.startswith('## '):
                    chapters_in_topic.append(line[3:].strip())
                    topic_content += line + '\n'
                
                # 其他内容（教学提示、学业要求等）
                else:
                    topic_content += line + '\n'
            
            # 处理最后一个主题
            if current_topic and chapters_in_topic:
                self._add_topic_with_chapters(current_topic, topic_content, chapters_in_topic, filepath.name)
                
        except Exception as e:
            print(f"解析文件 {filepath} 失败: {e}")
    
    def _add_topic_with_chapters(self, topic_name: str, topic_content: str, chapters: List[str], filename: str):
        """将主题内容关联到该主题下的所有章节"""
        # 为每个章节创建专属内容
        for chapter_name in chapters:
            # 将章节名称添加到术语列表（用于检索匹配）
            if chapter_name not in self._chapter_terms:
                self._chapter_terms.append(chapter_name)
            
            # 提取该章节专属的教学提示和学业要求
            chapter_specific_content = self._extract_chapter_content(topic_content, chapter_name)
            teaching_notes = self._extract_section(chapter_specific_content, '【教学提示】')
            academic_requirements = self._extract_section(chapter_specific_content, '【学业要求】')
            
            # 创建章节专属内容：章节标题 + 所属主题 + 该章节的教学提示 + 该章节的学业要求
            chapter_full_content = f"# {topic_name}\n\n"  # 主题标题
            chapter_full_content += f"## {chapter_name}\n\n"  # 章节标题
            
            # 添加主题下的所有章节列表（让用户了解主题结构）
            chapter_full_content += "### 本主题包含以下章节:\n"
            for chap in chapters:
                if chap == chapter_name:
                    chapter_full_content += f"- **{chap}** (当前章节)\n"
                else:
                    chapter_full_content += f"- {chap}\n"
            chapter_full_content += "\n"
            
            # 添加该章节的教学提示
            if teaching_notes:
                chapter_full_content += teaching_notes + '\n\n'
            
            # 添加该章节的学业要求
            if academic_requirements:
                chapter_full_content += academic_requirements + '\n'
            
            # 生成向量（如果模型可用）
            vector = None
            if self.vector_model:
                try:
                    text_for_vector = f"{chapter_name}\n{topic_content[:500]}"
                    vector = self.vector_model.encode(text_for_vector)
                except Exception as e:
                    print(f"生成向量失败 {chapter_name}: {e}")
            
            # 使用复合键：主题名_章节名，避免同一章节在不同主题中被覆盖
            chapter_key = f"{topic_name}_{chapter_name}"
            
            # 保存章节信息
            self.chapters[chapter_key] = {
                'content': chapter_full_content.strip(),
                'filename': filename,
                'vector': vector,
                'topic': topic_name,
                'chapter': chapter_name
            }
    
    def _extract_chapter_content(self, topic_content: str, chapter_name: str) -> str:
        """提取指定章节的内容（从章节标题开始到下一个章节标题结束）"""
        lines = topic_content.split('\n')
        result = []
        in_chapter = False
        chapter_found = False
        
        for line in lines:
            # 检查是否是章节标题
            if line.startswith('## '):
                current_chapter = line[3:].strip()
                if current_chapter == chapter_name:
                    in_chapter = True
                    chapter_found = True
                    result.append(line)
                elif in_chapter:
                    # 遇到下一个章节，停止提取
                    break
            elif in_chapter:
                result.append(line)
        
        # 如果没有找到独立的章节内容，返回整个主题内容（兼容旧格式）
        if not chapter_found:
            return topic_content
        
        extracted = '\n'.join(result).strip()
        
        # 如果提取的内容只包含章节标题和空行，返回整个主题内容
        # 这处理了教学提示在所有章节标题之后的情况
        if len(extracted) < 100 or (len(extracted.split('\n')) <= 5 and not '【' in extracted):
            return topic_content
        
        return extracted
    
    def _extract_section(self, content: str, section_title: str) -> str:
        """提取指定标题的内容，确保只保留一个标题"""
        lines = content.split('\n')
        result = []
        in_section = False
        title_added = False
        
        for line in lines:
            if section_title in line:
                if not title_added:
                    result.append(section_title)
                    title_added = True
                in_section = True
                continue
            
            # 检查是否进入下一个主要部分（只检测其他带【】的标题）
            if '【' in line and '】' in line and line != section_title:
                # 检查是否是其他章节标题（如【教学提示】、【学业要求】等）
                if line.strip().startswith('【'):
                    in_section = False
            
            if in_section and title_added:
                result.append(line)
        
        return '\n'.join(result).strip()
    
    def _extract_chapter_specific_notes(self, chapter_name: str, teaching_notes: str) -> str:
        """提取与特定章节相关的教学提示内容"""
        # 章节名称变体列表（用于匹配不同的表述方式）
        chapter_variants = [
            chapter_name,
            chapter_name.replace('、', ''),  # 移除顿号
        ]
        
        # 针对章节的教学提示通常以"XX的教学"开头
        chapter_prefixes = [c + '的教学' for c in chapter_variants]
        
        # 常见章节名称列表（用于检测章节切换）
        all_chapters = ['函数概念与性质', '幂函数、指数函数、对数函数', '三角函数', '函数的应用', 
                       '数列', '一元函数导数及其应用', '平面向量及其应用', '立体几何初步', 
                       '空间向量与立体几何', '平面解析几何', '概率', '统计', '计数原理']
        
        lines = teaching_notes.split('\n')
        relevant_lines = []
        in_chapter_section = False
        found_chapter_specific = False
        
        for line in lines:
            # 保留教学提示标题
            if '【教学提示】' in line:
                relevant_lines.append(line)
                continue
            
            # 跳过空行
            if not line.strip():
                if in_chapter_section:
                    relevant_lines.append(line)
                continue
            
            # 检查是否以章节名开头（如"三角函数的教学"）
            matched_prefix = None
            for prefix in chapter_prefixes:
                if line.startswith(prefix):
                    matched_prefix = prefix
                    break
            
            if matched_prefix:
                relevant_lines.append(line)
                in_chapter_section = True
                found_chapter_specific = True
                continue
            
            # 如果已经进入章节特定部分，继续收集直到遇到下一个章节的教学部分
            if in_chapter_section:
                # 检查是否是下一个章节的教学部分（以"XX的教学"开头）
                next_chapter_found = False
                for next_chapter in all_chapters:
                    # 检查多种可能的开头形式
                    if line.startswith(next_chapter + '的教学') or \
                       line.startswith(next_chapter[:4] + '的教学') or \
                       line.startswith(next_chapter[:2] + '的教学'):
                        next_chapter_found = True
                        break
                
                if next_chapter_found:
                    break
                relevant_lines.append(line)
        
        # 如果找到了章节特定内容，返回这些内容
        if found_chapter_specific and len(relevant_lines) > 1:
            return '\n'.join(relevant_lines)
        else:
            # 如果没有找到特定内容，返回完整的教学提示
            return teaching_notes
    
    def _add_chapter(self, chapter_name: str, content: str, filename: str):
        """添加章节到索引（兼容旧接口）"""
        self._add_topic_with_chapters(chapter_name, content, [chapter_name], filename)
    
    def _keyword_match(self, query: str) -> List[tuple]:
        """关键词匹配：章节名 + 内容，返回带匹配分数的结果"""
        # 定义停用词（只保留最常见的中文停用词，不包含教育领域术语）
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己',
            '它', '这', '那', '此', '其', '某', '每', '各', '所有', '任何', '一些', '许多', '少数', '几个', '全部', '任何', '其他', '另外', '还有', '以及', '等等',
            '因为', '所以', '但是', '然而', '虽然', '如果', '假如', '要是', '只要', '只有', '除非', '否则', '无论', '不管', '尽管', '即使', '万一'
        }
        
        # 将查询转换为简体中文（处理繁体输入）
        query = _traditional_to_simplified(query)
        
        # 使用动态提取的章节术语列表（从教学大纲文件中自动获取）
        # 这样无论添加什么板块的教学大纲，系统都能自动识别
        multi_word_terms = self._chapter_terms.copy()
        
        # 检查是否有完整的多词术语匹配
        matched_terms = []
        for term in multi_word_terms:
            if term in query.lower():
                matched_terms.append(term)
        
        # 如果找到多词术语，使用它们作为关键词
        if matched_terms:
            query_words = matched_terms
        else:
            # 使用jieba进行中文分词
            import jieba
            query_words = [word.strip() for word in jieba.cut(query.lower()) if word.strip()]
            query_words = [w for w in query_words if w not in stop_words and len(w) > 1]

            if not query_words:
                # 如果过滤后没有关键词，返回空列表（让调用方处理）
                return []
        
        matches = []
        
        for chapter_name, data in self.chapters.items():
            chapter_name_lower = chapter_name.lower()
            content_lower = data['content'].lower()
            score = 0
            
            # 计算匹配分数
            for word in query_words:
                if word in chapter_name_lower:
                    # 章节名精确匹配权重最高
                    if chapter_name_lower == word:
                        score += 20
                    elif chapter_name_lower.startswith(word):
                        score += 15
                    else:
                        score += 10
                if word in content_lower:
                    score += 1
            
            if score > 0:
                matches.append((chapter_name, score))
        
        # 按匹配分数降序排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """计算余弦相似度"""
        if vec1 is None or vec2 is None:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """混合检索：关键词匹配 + 语义相似度排序"""
        # 获取带匹配分数的候选结果
        scored_candidates = self._keyword_match(query)
        
        if not scored_candidates:
            # 如果没有匹配，返回所有章节（按名称排序）
            candidates = sorted(list(self.chapters.keys()))[:top_k]
        else:
            # 提取章节名（已按匹配分数排序）
            candidates = [item[0] for item in scored_candidates]
        
        # 如果语义模型可用，进一步优化排序
        if self.vector_model and len(candidates) > 1:
            try:
                query_vector = self.vector_model.encode(query)
                similarities = []
                
                for chapter_name in candidates:
                    chapter_vector = self.chapters[chapter_name]['vector']
                    if chapter_vector is not None:
                        similarity = self._cosine_similarity(query_vector, chapter_vector)
                        similarities.append((chapter_name, similarity))
                
                if similarities:
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    candidates = [item[0] for item in similarities[:top_k]]
            except Exception as e:
                print(f"语义排序失败: {e}")
                # 保持关键词匹配的排序结果
        
        results = []
        for chapter_key in candidates[:top_k]:
            data = self.chapters[chapter_key]
            # 使用数据中存储的章节名称（而不是复合键）
            chapter_name = data.get('chapter', chapter_key)
            
            # 获取匹配分数（从 scored_candidates 中查找）
            score = None
            if scored_candidates:
                for item in scored_candidates:
                    if item[0] == chapter_key:
                        score = item[1]
                        break
            
            results.append({
                'chapter': chapter_name,
                'content': data['content'],
                'filename': data['filename'],
                'topic': data['topic'],
                'score': score  # 添加分数字段
            })
        
        return results

# 创建全局单例
syllabus_manager = SyllabusManager()
