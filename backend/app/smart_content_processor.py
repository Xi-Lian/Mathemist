#!/usr/bin/env python3
# 智能内容处理模块

import re
import jieba
import jieba.analyse
from typing import List, Dict, Tuple, Optional

class SmartContentProcessor:
    """智能内容处理器"""
    
    def __init__(self):
        # 初始化关键词提取
        self.stop_words = self._get_stop_words()
    
    def _get_stop_words(self):
        """获取停用词"""
        stop_words = [
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要',
            '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '教学', '内容', '学习', '学生', '教师', '课程'
        ]
        return stop_words
    
    def process_content(self, content: str, resource_type: str = "general", max_length: int = 300) -> Dict[str, any]:
        """
        智能处理内容
        
        Args:
            content: 原始内容
            resource_type: 资源类型 (general, lesson_plan, theory, visualization, exercise)
            max_length: 最大显示长度
            
        Returns:
            处理后的内容信息
        """
        # 基础处理
        content = self._clean_content(content)
        
        # 根据资源类型选择处理策略
        if resource_type == "exercise":
            return self._process_exercise(content, max_length)
        elif resource_type == "lesson_plan":
            return self._process_lesson_plan(content, max_length)
        elif resource_type == "theory":
            return self._process_theory(content, max_length)
        elif resource_type == "visualization":
            return self._process_visualization(content, max_length)
        else:
            return self._process_general(content, max_length)
    
    def _clean_content(self, content: str) -> str:
        """清理内容"""
        # 移除Markdown/HTML标签
        content = re.sub(r'{[^}]+}', '', content)  # 移除 {width=...} 等标签
        content = re.sub(r'\|', ' ', content)  # 移除表格分隔符
        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        # 移除首尾空白
        content = content.strip()
        return content
    
    def extract_keywords(self, content: str, top_k: int = 5) -> List[str]:
        """提取关键词"""
        try:
            keywords = jieba.analyse.extract_tags(content, topK=top_k, withWeight=False)
            # 过滤停用词
            keywords = [kw for kw in keywords if kw not in self.stop_words]
            return keywords[:top_k]
        except:
            return []
    
    def generate_summary(self, content: str, max_length: int = 150) -> str:
        """生成摘要"""
        # 清理内容
        content = self._clean_content(content)
        
        # 移除学科网等广告内容
        content = re.sub(r'学科网.*?教育资源门户.*?资讯\.', '', content)
        content = re.sub(r'学科网\(www\.zxxk\.com\).*', '', content)
        
        # 清理多余的标点符号
        content = re.sub(r'[。]+', '。', content)
        
        # 简单摘要生成：提取前几句话
        sentences = re.split(r'[。！？；]', content)
        summary = ""
        
        for sentence in sentences:
            if sentence and len(summary) + len(sentence) <= max_length:
                summary += sentence + "。"
            elif len(summary) >= max_length:
                break
        
        return summary if summary else content[:max_length] + "..."
    
    def _process_exercise(self, content: str, max_length: int) -> Dict[str, any]:
        """处理习题内容"""
        # 提取题目结构
        questions = self._extract_questions(content)
        
        if questions:
            # 构建习题摘要
            summary_parts = []
            total_length = 0
            
            for i, question in enumerate(questions[:3]):  # 最多显示3个题目
                q_summary = f"【题目{i+1}】{question[:100]}..." if len(question) > 100 else f"【题目{i+1}】{question}"
                if total_length + len(q_summary) <= max_length:
                    summary_parts.append(q_summary)
                    total_length += len(q_summary)
                else:
                    break
            
            summary = "\n".join(summary_parts)
            has_more = len(questions) > len(summary_parts)
        else:
            # 普通内容处理
            summary = self.generate_summary(content, max_length)
            has_more = len(content) > len(summary)
        
        return {
            "summary": summary,
            "has_more": has_more,
            "original_length": len(content),
            "processed_length": len(summary),
            "resource_type": "exercise"
        }
    
    def _extract_questions(self, content: str) -> List[str]:
        """提取题目"""
        # 简单的题目提取规则
        questions = []
        
        # 匹配常见题目格式
        patterns = [
            r'\d+\.\s*(.*?)(?=\d+\.|$)',  # 1. 题目内容
            r'【题目\d+】\s*(.*?)(?=【题目\d+】|$)',  # 【题目1】题目内容
            r'[A-Z]\.\s*(.*?)(?=[A-Z]\.|$)',  # A. 选项内容
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            questions.extend([m.strip() for m in matches if m.strip()])
        
        # 如果没有匹配到题目，按段落分割
        if not questions:
            paragraphs = content.split('\n')
            questions = [p.strip() for p in paragraphs if p.strip()]
        
        return questions
    
    def _process_lesson_plan(self, content: str, max_length: int) -> Dict[str, any]:
        """处理教案内容"""
        # 提取教案结构
        structure = self._extract_lesson_structure(content)
        
        if structure:
            # 构建教案摘要
            summary_parts = []
            total_length = 0
            
            for section, section_content in structure.items():
                section_summary = f"【{section}】{section_content[:80]}..." if len(section_content) > 80 else f"【{section}】{section_content}"
                if total_length + len(section_summary) <= max_length:
                    summary_parts.append(section_summary)
                    total_length += len(section_summary)
                else:
                    break
            
            summary = "\n".join(summary_parts)
            has_more = len(structure) > len(summary_parts)
        else:
            # 普通内容处理
            summary = self.generate_summary(content, max_length)
            has_more = len(content) > len(summary)
        
        return {
            "summary": summary,
            "has_more": has_more,
            "original_length": len(content),
            "processed_length": len(summary),
            "resource_type": "lesson_plan"
        }
    
    def _extract_lesson_structure(self, content: str) -> Dict[str, str]:
        """提取教案结构"""
        structure = {}
        
        # 常见教案 sections
        sections = [
            "教学目标", "教学重难点", "教学方法", "教学过程", 
            "导入", "新课讲授", "巩固练习", "小结", "作业"
        ]
        
        for section in sections:
            # 改进的正则表达式，避免匹配到其他section
            other_sections = [s for s in sections if s != section]
            if other_sections:
                pattern = f"{section}[：:](.*?)(?={('|'.join(other_sections))}|$)"
            else:
                pattern = f"{section}[：:](.*)$"
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                structure[section] = self._clean_content(matches[0].strip())
        
        return structure
    
    def _process_theory(self, content: str, max_length: int) -> Dict[str, any]:
        """处理理论内容"""
        # 提取知识点
        keywords = self.extract_keywords(content, top_k=3)
        summary = self.generate_summary(content, max_length)
        
        # 添加关键词到摘要
        if keywords:
            keyword_str = "【关键词】" + ", ".join(keywords)
            if len(summary) + len(keyword_str) <= max_length:
                summary = keyword_str + "\n" + summary
        
        has_more = len(content) > len(summary)
        
        return {
            "summary": summary,
            "has_more": has_more,
            "original_length": len(content),
            "processed_length": len(summary),
            "resource_type": "theory"
        }
    
    def _process_visualization(self, content: str, max_length: int) -> Dict[str, any]:
        """处理可视化内容"""
        # 提取可视化类型和描述
        viz_elements = self._extract_visualization_elements(content)
        
        if viz_elements:
            summary_parts = []
            total_length = 0
            
            for element in viz_elements[:2]:  # 最多显示2个可视化元素
                element_summary = f"【可视化】{element[:120]}..." if len(element) > 120 else f"【可视化】{element}"
                if total_length + len(element_summary) <= max_length:
                    summary_parts.append(element_summary)
                    total_length += len(element_summary)
                else:
                    break
            
            summary = "\n".join(summary_parts)
            has_more = len(viz_elements) > len(summary_parts)
        else:
            # 普通内容处理
            summary = self.generate_summary(content, max_length)
            has_more = len(content) > len(summary)
        
        return {
            "summary": summary,
            "has_more": has_more,
            "original_length": len(content),
            "processed_length": len(summary),
            "resource_type": "visualization"
        }
    
    def _extract_visualization_elements(self, content: str) -> List[str]:
        """提取可视化元素"""
        elements = []
        
        # 匹配可视化相关内容
        patterns = [
            r'图表[:：](.*?)(?=图表|$)',
            r'图像[:：](.*?)(?=图像|$)',
            r'图示[:：](.*?)(?=图示|$)',
            r'可视化[:：](.*?)(?=可视化|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            elements.extend([m.strip() for m in matches if m.strip()])
        
        # 如果没有匹配到，按段落分割
        if not elements:
            paragraphs = content.split('\n')
            elements = [p.strip() for p in paragraphs if p.strip()]
        
        return elements
    
    def _process_general(self, content: str, max_length: int) -> Dict[str, any]:
        """处理通用内容"""
        summary = self.generate_summary(content, max_length)
        has_more = len(content) > len(summary)
        
        return {
            "summary": summary,
            "has_more": has_more,
            "original_length": len(content),
            "processed_length": len(summary),
            "resource_type": "general"
        }
    
    def split_content(self, content: str, chunk_size: int = 500) -> List[str]:
        """分段显示内容"""
        chunks = []
        current_chunk = ""
        
        sentences = re.split(r'[。！？；]', content)
        
        for sentence in sentences:
            if sentence:
                if len(current_chunk) + len(sentence) <= chunk_size:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

# 测试
if __name__ == "__main__":
    processor = SmartContentProcessor()
    
    # 测试习题内容
    exercise_content = """
    1. 下列各式中，是函数的个数为(　　)
    ①y＝6；②y＝－x2；③y＝4－x；④y＝x－2＋1－x．
    A．4 B．3 C．2 D．1
    
    2. 函数f(x)＝1x－2－(x－4)0的定义域是(　　)
    A．[2，＋∞) B．(2，＋∞) C．(2，4)∪(4，＋∞) D．(2，4)∩(4，＋∞)
    
    3. 若函数y＝f(x)的定义域为[－1，1]，则 y＝f(|x|－1)的定义域为(　　)
    A．[－1，1] B．[－1，0] C．[0，1] D．[－2，2]
    """
    
    print("=== 测试习题处理 ===")
    result = processor.process_content(exercise_content, "exercise", 300)
    print(f"摘要: {result['summary']}")
    print(f"是否有更多内容: {result['has_more']}")
    print(f"原始长度: {result['original_length']}")
    print(f"处理后长度: {result['processed_length']}")
    
    # 测试教案内容
    lesson_content = """
    教学目标：
    1. 理解二次函数的概念和性质
    2. 掌握二次函数的图像绘制方法
    3. 能够应用二次函数解决实际问题
    
    教学重难点：
    重点：二次函数的图像和性质
    难点：二次函数在实际问题中的应用
    
    教学过程：
    一、导入（5分钟）
    通过实际问题引入二次函数
    二、新课讲授（20分钟）
    讲解二次函数的概念、图像和性质
    三、巩固练习（15分钟）
    学生完成练习题
    四、小结（5分钟）
    总结本节课内容
    五、作业
    完成课后习题
    """
    
    print("\n=== 测试教案处理 ===")
    result = processor.process_content(lesson_content, "lesson_plan", 300)
    print(f"摘要: {result['summary']}")
    print(f"是否有更多内容: {result['has_more']}")
    
    # 测试理论内容
    theory_content = """
    二次函数是形如y=ax²+bx+c(a≠0)的函数，其中a、b、c为常数。
    二次函数的图像是一条抛物线，当a>0时，抛物线开口向上；当a<0时，抛物线开口向下。
    二次函数的顶点坐标为(-b/2a, f(-b/2a))，对称轴为x=-b/2a。
    二次函数在区间(-∞, -b/2a)和(-b/2a, +∞)上的单调性相反。
    """
    
    print("\n=== 测试理论处理 ===")
    result = processor.process_content(theory_content, "theory", 200)
    print(f"摘要: {result['summary']}")
    print(f"是否有更多内容: {result['has_more']}")
    
    # 测试分段功能
    print("\n=== 测试分段功能 ===")
    long_content = "这是一段很长的内容" * 50
    chunks = processor.split_content(long_content, 200)
    print(f"总段数: {len(chunks)}")
    print(f"第一段: {chunks[0]}")
    print(f"第二段: {chunks[1]}")
