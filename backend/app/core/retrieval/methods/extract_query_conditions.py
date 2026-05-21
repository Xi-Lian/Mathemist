from .._shared import *


class _ExtractQueryConditionsMixin:
    def _extract_query_conditions(self, query: str) -> Dict[str, str]:
        """
        V49.0改进：从查询中提取多维度条件
        
        Args:
            query: 用户查询
        
        Returns:
            包含各维度条件的字典
        """
        conditions = {
            'knowledge_points': [],
            'question_type': '',
            'difficulty': '',
            'grade': '',
            'exam_form': '',
            'quantity': 0,
            'intent': '',  # 新增：查询意图
            'context': '',  # 新增：查询上下文
            'requirements': []  # 新增：用户的语义要求（如"互动性强"、"生动有趣"等）
        }
        
        # 1. 提取查询意图
        intent_patterns = [
            ('练习', ['练习课', '练习题', '习题', '题目', '测试题', '题']),
            ('学习', ['学习', '了解', '掌握', '理解', '认识']),
            ('教学', ['教学', '教案', '课件', '教学设计', '教学方案']),
            ('复习', ['复习课', '复习', '巩固', '回顾', '总结']),
            ('备考', ['备考', '冲刺', '模拟', '真题']),
            ('比较', ['比较', '对比', '区别', '联系', '异同']),
            ('应用', ['应用', '实际应用', '应用题', '实践'])
        ]
        
        for intent, patterns in intent_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['intent'] = intent
                    break
            if conditions['intent']:
                break
        
        # 2. 提取数量要求
        import re
        quantity_patterns = [
            (r'(\d+)道', True),
            (r'(\d+)题', True),
            (r'(\d+)个', True),
            (r'(\d+)道题', True),
            (r'几道', False),
            (r'一些', False),
            (r'几个', False),
            (r'少量', False),
            (r'多个', False),
            (r'几个', False)
        ]
        
        for pattern, has_group in quantity_patterns:
            match = re.search(pattern, query)
            if match:
                if has_group and match.group(1):
                    try:
                        conditions['quantity'] = int(match.group(1))
                    except:
                        conditions['quantity'] = 5
                else:
                    conditions['quantity'] = 5
                break
        
        # 3. 提取年级
        grade_patterns = [
            ('高一', ['高一', '高1', '高一上', '高一下', '高中一年级']),
            ('高二', ['高二', '高2', '高二上', '高二下', '高中二年级']),
            ('高三', ['高三', '高3', '高三上', '高三下', '高中三年级']),
            ('初中', ['初中', '初一', '初二', '初三', '初中一年级', '初中二年级', '初中三年级'])
        ]
        
        for grade, patterns in grade_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['grade'] = grade
                    break
            if conditions['grade']:
                break
        
        # 4. 提取难度
        difficulty_patterns = [
            ('基础', ['基础', '简单', '刚学', '入门', '初级', '容易', '基础题', '简单题', '简单练习', '基础练习']),
            ('中等', ['中等', '一般', '普通', '常见', '适中', '中等题', '中等难度', '一般难度']),
            ('拔高', ['拔高', '难', '困难', '挑战', '压轴', '难题', '提高', '进阶', '综合', '困难题', '高难度', '复杂'])  # 【V107.0新增】"复杂"映射到拔高难度
        ]
        
        for difficulty, patterns in difficulty_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['difficulty'] = difficulty
                    print(f"   📝 识别到难度: {difficulty} (匹配关键词: {pattern})")
                    break
            if conditions['difficulty']:
                break
        
        # 5. 提取考查形式
        exam_form_patterns = [
            ('性质', ['性质', '单调性', '奇偶性', '周期性', '对称性', '定义域', '值域', '图像', '零点']),
            ('应用', ['应用', '实际应用', '应用题', '综合应用', '生活应用', '经济应用', '物理应用']),
            ('证明', ['证明', '证明题', '求证', '推导', '证明方法', '数学归纳法']),
            ('计算', ['计算', '计算题', '求解', '求值', '计算方法', '运算']),
            ('最值', ['最值', '最大值', '最小值', '极值', '最值问题', '取值范围', '值域问题']),
            ('单调性', ['单调性', '单调递增', '单调递减', '单调区间', '单调性证明']),
            ('奇偶性', ['奇偶性', '奇函数', '偶函数', '奇偶性判断'])
        ]
        
        for exam_form, patterns in exam_form_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['exam_form'] = exam_form
                    print(f"   📝 V100.0识别到考查形式: {exam_form} (匹配关键词: {pattern})")
                    break
            if conditions['exam_form']:
                break
        
        # 6. 提取题目类型
        # V95.0改进：增强题目类型识别，特别是应用题
        question_type_patterns = [
            ('选择题', ['选择题', '单选题', '多选题', '选择', '单选', '多选']),
            ('证明题', ['证明题', '求证', '证明', '证明题', '推导题']),
            ('填空题', ['填空题', '填空', '填空题']),
            ('解答题', ['解答题', '计算题', '解答', '计算']),
            ('应用题', ['应用题', '实际背景', '实际问题', '应用场景', '应用问题', '实际应用']),
            ('判断题', ['判断题', '判断', '是非题']),
            ('简答题', ['简答题', '简答']),
            ('开放题', ['开放题', '开放性问题'])
        ]
        
        for qtype, patterns in question_type_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['question_type'] = qtype
                    print(f"   📝 V95.0识别到题目类型: {qtype} (匹配关键词: {pattern})")
                    break
            if conditions['question_type']:
                break
        
        # 6. 提取知识点（使用现有的主题提取逻辑）
        core_theme_result = self._extract_core_theme(query)
        print(f"   🔍 DEBUG: _extract_core_theme返回类型: {type(core_theme_result)}, 值: {core_theme_result}")
        # 处理新的返回值格式 (core_theme, board)
        if isinstance(core_theme_result, tuple) and len(core_theme_result) == 2:
            core_theme, board = core_theme_result
            if board and not conditions.get('board'):
                conditions['board'] = board
                print(f"   📝 V96.0提取板块: {board}")
        else:
            core_theme = core_theme_result
        print(f"   🔍 DEBUG: 处理后core_theme类型: {type(core_theme)}, 值: {core_theme}")
        if core_theme:
            conditions['knowledge_points'] = [t.strip() for t in core_theme.split(',') if t.strip()]
        
        # 7. 提取用户的语义要求
        requirement_patterns = [
            '互动性强', '互动性', '互动', '课堂互动', '小组讨论', '活动',
            '生动有趣', '有趣', '生动', '趣味', '游戏化',
            '深入浅出', '易懂', '简单明了', '容易理解',
            '探究式', '探究', '自主学习', '发现学习',
            '启发性', '启发', '引导', '思考',
            '系统性', '系统', '完整', '全面'
        ]
        
        requirements = []
        for pattern in requirement_patterns:
            if pattern in query:
                requirements.append(pattern)
                print(f"   📝 识别到语义要求: '{pattern}'")
        
        if requirements:
            conditions['requirements'] = requirements
            print(f"\n✅ [语义匹配] 成功提取 {len(requirements)} 个语义要求: {requirements}")
        else:
            print(f"\nℹ️ [语义匹配] 未提取到语义要求")
        
        print(f"   ✅ V49.0提取查询条件: {conditions}")
        return conditions
