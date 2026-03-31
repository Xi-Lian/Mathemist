from .._shared import *


class _IsVagueGradeQueryMixin:
    def _is_vague_grade_query(self, query: str, grade_info: Dict[str, Any]) -> bool:
        """
        V32.0：判断是否是宽泛的年级查询
        
        宽泛查询的特征：
        - 只有年级关键词（如"高三数学"、"高一"）
        - 没有具体的主题或知识点
        - 没有明确的难度要求
        
        Args:
            query: 用户查询
            grade_info: 年级信息
            
        Returns:
            是否是宽泛查询
        """
        if not query or not grade_info:
            return False
        
        query_lower = query.lower()
        
        # 1. 检查是否有具体的主题关键词
        theme_keywords = [
            '函数', '方程', '不等式', '集合', '向量', '复数', '数列', '导数', '积分',
            '三角', '指数', '对数', '二次', '一次', '幂函数', '圆锥曲线', '立体几何',
            '概率', '统计', '排列组合', '二项式'
        ]
        has_theme = any(keyword in query_lower for keyword in theme_keywords)
        
        # 2. 检查是否有明确的难度要求
        difficulty_keywords = ['基础', '简单', '中等', '提高', '难题', '拔高', '冲刺', '竞赛']
        has_difficulty = any(keyword in query_lower for keyword in difficulty_keywords)
        
        # 3. 检查是否有具体的知识点
        knowledge_keywords = ['概念', '性质', '图像', '单调性', '奇偶性', '周期性', '定义域', '值域']
        has_knowledge = any(keyword in query_lower for keyword in knowledge_keywords)
        
        # 4. 检查是否有资源类型要求
        type_keywords = ['教案', '习题', '课件', '课例', '真题', '模拟']
        has_type = any(keyword in query_lower for keyword in type_keywords)
        
        # 宽泛查询 = 只有年级，没有其他具体要求
        is_vague = not (has_theme or has_difficulty or has_knowledge or has_type)
        
        # V52.0改进：对于高三查询，放宽年级筛选条件
        # 高三学生需要复习所有年级的知识，所以即使包含主题，也应该被认为是宽泛查询
        if grade_info.get('grade') == '高三':
            print(f"   🔍 V52.0高三查询: 放宽年级筛选条件")
            is_vague = True
        
        if is_vague:
            print(f"   🔍 V32.0检测到宽泛查询: 年级={grade_info.get('grade')}, 无具体主题/难度/类型要求")
        else:
            print(f"   🔍 V32.0检测到具体查询: 主题={has_theme}, 难度={has_difficulty}, 知识点={has_knowledge}, 类型={has_type}")
        
        return is_vague
