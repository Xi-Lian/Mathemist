"""
GGB 资源检索器

职责：
- 从 Excel 文件中加载 GGB 信息
- 根据章节和主题检索相关的 GGB 案例
- 提供结构化的参考信息用于 AI 生成建议

依赖：
- pandas (Excel 文件读取)
- os (文件路径操作)
"""

import os
import pandas as pd
from typing import List, Dict, Optional


class GGBResourceRetriever:
    """GGB 资源检索器"""
    
    def __init__(self, resource_dir: str = None):
        """
        初始化 GGB 资源检索器
        
        Args:
            resource_dir: 资源目录路径，默认为 learning_resource
        """
        if resource_dir is None:
            # 默认使用项目根目录下的 learning_resource
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            resource_dir = os.path.join(project_root, "learning_resource")
        
        self.resource_dir = resource_dir
        self.ggb_dataframes = {}  # 缓存已加载的 DataFrame
        
        # 预加载所有 GGB 信息表
        self._preload_ggb_files()
    
    def _preload_ggb_files(self):
        """预加载所有 GGB 信息表"""
        ggb_files = [
            "函数-ggb信息.xlsx",
            "立体几何-ggb信息.xlsx",
            "概率与统计-ggb信息.xlsx"
        ]
        
        for filename in ggb_files:
            filepath = os.path.join(self.resource_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_excel(filepath)
                    # 提取章节名称作为 key（从文件名推断）
                    chapter_key = filename.replace("-ggb信息.xlsx", "")
                    self.ggb_dataframes[chapter_key] = df
                    print(f"✅ 加载 GGB 信息表: {filename} ({len(df)} 条记录)")
                except Exception as e:
                    print(f"⚠️ 加载失败 {filename}: {e}")
            else:
                print(f"⚠️ 文件不存在: {filepath}")
    
    def retrieve_related_ggb(
        self, 
        chapter: str, 
        topic: str, 
        top_k: int = 3
    ) -> List[Dict[str, str]]:
        """
        检索相关的 GGB 资源
        
        Args:
            chapter: 章节名称（如 "三角函数"、"立体几何"）
            topic: 主题名称（如 "正弦函数图像"）
            top_k: 返回最相关的 K 个结果
        
        Returns:
            相关 GGB 资源列表，每个元素包含：
            - ggb_filename: GGB 文件名
            - drawing_steps: 作图步骤
            - demo_steps: 演示步骤
            - teaching_purpose: 教学用途
        """
        results = []
        
        # 1. 确定要搜索的 DataFrame
        target_dfs = []
        
        # 尝试精确匹配章节
        for key, df in self.ggb_dataframes.items():
            if key in chapter or chapter in key:
                target_dfs.append((key, df))
        
        # 如果没有精确匹配，搜索所有 DataFrame
        if not target_dfs:
            target_dfs = list(self.ggb_dataframes.items())
        
        # 2. 在每个 DataFrame 中搜索
        for chapter_key, df in target_dfs:
            # 查找包含 topic 的行
            matched_rows = []
            
            for idx, row in df.iterrows():
                # 检查 ggb文件名 是否包含 topic
                ggb_filename = str(row.get('ggb文件名', ''))
                if topic in ggb_filename or ggb_filename in topic:
                    matched_rows.append(row)
                    continue
                
                # 检查 教学用途 是否包含 topic 关键词
                teaching_purpose = str(row.get('教学用途', ''))
                if topic in teaching_purpose:
                    matched_rows.append(row)
                    continue
            
            # 添加到结果列表
            for row in matched_rows[:top_k]:
                result = {
                    'ggb_filename': str(row.get('ggb文件名', '')),
                    'drawing_steps': str(row.get('作图步骤', '')) if pd.notna(row.get('作图步骤')) else '',
                    'demo_steps': str(row.get('演示步骤', '')) if pd.notna(row.get('演示步骤')) else '',
                    'teaching_purpose': str(row.get('教学用途', '')) if pd.notna(row.get('教学用途')) else '',
                    'chapter_source': chapter_key
                }
                results.append(result)
                
                # 如果已经找到足够的结果，提前退出
                if len(results) >= top_k:
                    break
            
            if len(results) >= top_k:
                break
        
        return results
    
    def load_all_ggb_knowledge(self) -> str:
        """
        加载所有 GGB 信息表的完整知识
        
        Returns:
            所有 GGB 资源的结构化文本（用于 AI 学习）
        """
        knowledge_text = "\n\n## 📚 GeoGebra 资源知识库（完整）\n\n"
        
        for chapter_key, df in self.ggb_dataframes.items():
            knowledge_text += f"### 【{chapter_key}】章节的 GGB 资源\n\n"
            
            # 遍历所有行，提取关键信息
            for idx, row in df.iterrows():
                ggb_filename = str(row.get('ggb文件名', ''))
                drawing_steps = str(row.get('作图步骤', '')) if pd.notna(row.get('作图步骤')) else ''
                demo_steps = str(row.get('演示步骤', '')) if pd.notna(row.get('演示步骤')) else ''
                teaching_purpose = str(row.get('教学用途', '')) if pd.notna(row.get('教学用途')) else ''
                
                # 只添加有内容的条目
                if ggb_filename and (drawing_steps or demo_steps or teaching_purpose):
                    knowledge_text += f"**资源**: {ggb_filename}\n"
                    if drawing_steps:
                        knowledge_text += f"- 作图要点: {drawing_steps[:200]}\n"  # 限制长度
                    if demo_steps:
                        knowledge_text += f"- 演示要点: {demo_steps[:200]}\n"
                    if teaching_purpose:
                        knowledge_text += f"- 教学目标: {teaching_purpose[:200]}\n"
                    knowledge_text += "\n"
            
            knowledge_text += "---\n\n"
        
        return knowledge_text
    
    def load_all_syllabus_knowledge(self) -> str:
        """
        加载所有章节的教学大纲完整知识
        
        Returns:
            所有教学大纲的结构化文本
        """
        syllabus_files = [
            "函数教学大纲.md",
            "立体几何教学大纲.md",
            "概率与统计教学大纲.md"
        ]
        
        knowledge_text = "\n\n## 📖 数学教学大纲（完整）\n\n"
        
        for filename in syllabus_files:
            filepath = os.path.join(self.resource_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取章节标题
                        chapter_name = filename.replace("教学大纲.md", "")
                        knowledge_text += f"### 【{chapter_name}】教学大纲\n\n"
                        knowledge_text += content[:1500] + "...\n\n"  # 每个大纲最多1500字符
                        knowledge_text += "---\n\n"
                except Exception as e:
                    print(f"⚠️ 读取教学大纲失败 {filename}: {e}")
        
        return knowledge_text
    
    def load_teaching_syllabus(self, chapter: str) -> str:
        """
        加载对应章节的教学大纲
        
        Args:
            chapter: 章节名称
        
        Returns:
            教学大纲内容（截取前 800 字符）
        """
        # 映射章节名称到文件名
        chapter_to_file = {
            "函数": "函数教学大纲.md",
            "立体几何": "立体几何教学大纲.md",
            "概率与统计": "概率与统计教学大纲.md",
            "三角函数": "函数教学大纲.md",  # 三角函数属于函数章节
        }
        
        # 尝试匹配
        syllabus_filename = None
        for key, filename in chapter_to_file.items():
            if key in chapter:
                syllabus_filename = filename
                break
        
        if not syllabus_filename:
            # 尝试通用匹配
            for filename in ["函数教学大纲.md", "立体几何教学大纲.md", "概率与统计教学大纲.md"]:
                filepath = os.path.join(self.resource_dir, filename)
                if os.path.exists(filepath):
                    syllabus_filename = filename
                    break
        
        if not syllabus_filename:
            return ""
        
        # 读取文件
        filepath = os.path.join(self.resource_dir, syllabus_filename)
        if not os.path.exists(filepath):
            return ""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 截取前 800 字符，避免提示词过长
                return content[:800] + "..." if len(content) > 800 else content
        except Exception as e:
            print(f"⚠️ 读取教学大纲失败: {e}")
            return ""
    
    def format_syllabus_info(self, chapter: str) -> str:
        """
        格式化教学大纲信息
        
        Args:
            chapter: 章节名称
        
        Returns:
            格式化的教学大纲信息
        """
        syllabus_content = self.load_teaching_syllabus(chapter)
        if not syllabus_content:
            return ""
        
        return f"\n\n## 📖 教学大纲要求\n\n{syllabus_content}\n\n"


# 全局实例（单例模式）
_ggb_retriever_instance = None


def get_ggb_retriever() -> GGBResourceRetriever:
    """获取 GGB 资源检索器单例"""
    global _ggb_retriever_instance
    if _ggb_retriever_instance is None:
        _ggb_retriever_instance = GGBResourceRetriever()
    return _ggb_retriever_instance
