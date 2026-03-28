"""
教案和习题内容特征提取器

职责：
- 解析教案内容，提取教学方法、教学环节等特征
- 解析习题内容，提取难度、题目类型等特征
- 为教案和习题建立内容标签，支持基于内容的检索
- 保持与现有主题检索的兼容性

V9.1新增：支持基于教学方法和教学环节的内容检索
V9.2新增：支持习题难度和题目类型的检索
V12.0新增：主观意图语义理解增强
V12.0改进2：年级元数据匹配
"""

import re
from typing import Dict, Any, List, Set, Optional
from collections import Counter

# V12.0改进2：导入年级元数据丰富器
from .grade_metadata_enricher import get_grade_enricher


class SubjectiveIntentInterpreter:
    """
    主观意图解释器 - 理解用户的真实需求
    
    V12.0新增：解决主观词汇（如"基础"、"提高"、"难题"）理解不准确的问题
    """
    
    # 主观词汇的多维映射 - 理解用户的真实意图
    SUBJECTIVE_MAPPINGS = {
        '基础': {
            'difficulty': ['1', '2'],  # 难度维度
            'difficulty_range': (1, 2),  # 难度范围
            'cognitive_level': ['识记', '理解'],  # 认知层次维度
            'question_features': ['概念题', '直接计算', '公式应用', '单一知识点'],  # 题目特征
            'prerequisites': ['前置知识少', '步骤少', '直观'],  # 前置要求
            'user_scenarios': {
                '新手入门': {
                    'weight': 0.4, 
                    'features': ['概念理解', '简单计算', '直观认识'],
                    'keywords': ['刚学', '第一次', '初学', '入门']
                },
                '课前预习': {
                    'weight': 0.25, 
                    'features': ['知识引入', '直观理解', '自主尝试'],
                    'keywords': ['预习', '课前', '自学']
                },
                '差生补弱': {
                    'weight': 0.25, 
                    'features': ['基础巩固', '逐步引导', '反复练习'],
                    'keywords': ['补弱', '帮扶', '跟不上', '困难']
                },
                '巩固练习': {
                    'weight': 0.1, 
                    'features': ['熟练度', '准确率', '速度'],
                    'keywords': ['熟练', '巩固', '复习']
                }
            }
        },
        '简单': {
            'difficulty': ['1', '2'],
            'difficulty_range': (1, 2),
            'cognitive_level': ['识记', '理解'],
            'question_features': ['步骤少', '直接应用', '单一知识点'],
            'prerequisites': ['前置知识少', '计算量小'],
            'user_scenarios': {
                '快速练习': {'weight': 0.5, 'features': ['速度快', '量大'], 'keywords': ['快', '多', '刷题']},
                '建立信心': {'weight': 0.3, 'features': ['成功体验', '正向反馈'], 'keywords': ['信心', '鼓励']},
                '热身准备': {'weight': 0.2, 'features': ['激活思维', '进入状态'], 'keywords': ['热身', '准备']}
            }
        },
        '提高': {
            'difficulty': ['4'],
            'difficulty_range': (4, 4),
            'cognitive_level': ['应用', '分析', '综合'],
            'question_features': ['综合题', '变式训练', '易错点', '方法迁移', '多知识点'],
            'prerequisites': ['需要理解', '多步骤', '方法选择'],
            'user_scenarios': {
                '能力提升': {
                    'weight': 0.45, 
                    'features': ['思维拓展', '方法总结', '举一反三'],
                    'keywords': ['提升', '能力', '思维', '方法']
                },
                '考前复习': {
                    'weight': 0.3, 
                    'features': ['重点突破', '典型例题', '查漏补缺'],
                    'keywords': ['考试', '复习', '备考', '重点']
                },
                '培优训练': {
                    'weight': 0.25, 
                    'features': ['竞赛入门', '创新思维', '深度理解'],
                    'keywords': ['培优', '尖子', '竞赛', '拔高']
                }
            }
        },
        '中等': {
            'difficulty': ['3'],
            'difficulty_range': (3, 3),
            'cognitive_level': ['应用', '分析'],
            'question_features': ['标准题型', '常规综合', '适度挑战'],
            'prerequisites': ['基本掌握', '常规方法'],
            'user_scenarios': {
                '常规练习': {'weight': 0.6, 'features': ['标准难度', '全面覆盖'], 'keywords': ['常规', '普通', '一般']},
                '阶段检测': {'weight': 0.4, 'features': ['能力评估', '水平测试'], 'keywords': ['检测', '测试', '评估']}
            }
        },
        '难题': {
            'difficulty': ['4', '5'],
            'difficulty_range': (4, 5),
            'cognitive_level': ['综合', '评价', '创新'],
            'question_features': ['压轴题', '探究题', '开放题', '多知识点综合', '非常规方法', '高思维量'],
            'prerequisites': ['深入理解', '多方法掌握', '强分析能力'],
            'user_scenarios': {
                '竞赛准备': {
                    'weight': 0.35, 
                    'features': ['高阶思维', '技巧训练', '非常规方法'],
                    'keywords': ['竞赛', '奥赛', '数学竞赛']
                },
                '高考冲刺': {
                    'weight': 0.4, 
                    'features': ['压轴突破', '综合应用', '应试技巧'],
                    'keywords': ['高考', '压轴', '冲刺', '高分']
                },
                '思维拓展': {
                    'weight': 0.25, 
                    'features': ['一题多解', '创新方法', '深度探究'],
                    'keywords': ['拓展', '探究', '创新', '深度']
                }
            }
        },
        '综合': {
            'difficulty': ['3', '4', '5'],
            'difficulty_range': (3, 5),
            'cognitive_level': ['综合', '评价'],
            'question_features': ['多知识点', '跨章节', '方法综合', '能力全面'],
            'prerequisites': ['多知识点掌握', '方法选择能力'],
            'user_scenarios': {
                '章节复习': {'weight': 0.4, 'features': ['知识整合', '体系构建'], 'keywords': ['复习', '章节', '总结']},
                '阶段测试': {'weight': 0.35, 'features': ['全面检测', '能力评估'], 'keywords': ['测试', '考试', '检测']},
                '能力提升': {'weight': 0.25, 'features': ['融会贯通', '灵活应用'], 'keywords': ['提升', '综合', '能力']}
            }
        }
    }
    
    def __init__(self):
        """初始化主观意图解释器"""
        pass
    
    def interpret(self, query: str) -> Optional[Dict[str, Any]]:
        """
        解释用户查询中的主观意图（简化版）
        
        Args:
            query: 用户查询
            
        Returns:
            解释后的意图特征，包含difficulty_range、cognitive_level、user_scenario等字段
        """
        if not query:
            return None
        
        # 检测主观词汇
        detected_words = []
        for word in self.SUBJECTIVE_MAPPINGS.keys():
            if word in query:
                detected_words.append(word)
        
        # 如果没有检测到主观词汇，返回None
        if not detected_words:
            return None
        
        # 使用第一个检测到的词汇（优先级最高的）
        primary_word = detected_words[0]
        mappings = self.SUBJECTIVE_MAPPINGS[primary_word]
        
        # 推断用户场景
        scenario = self._infer_user_scenario(query, None, primary_word)
        
        return {
            'subjective_words': detected_words,
            'primary_word': primary_word,
            'difficulty': mappings['difficulty'],
            'difficulty_range': mappings['difficulty_range'],
            'cognitive_level': mappings['cognitive_level'],
            'question_features': mappings['question_features'],
            'prerequisites': mappings['prerequisites'],
            'user_scenario': scenario['name'],
            'scenario_confidence': scenario['confidence']
        }
    
    def interpret_intent(self, query: str, context: dict = None) -> dict:
        """
        解释用户查询中的主观意图
        
        Args:
            query: 用户查询
            context: 上下文信息（如用户历史、年级等）
            
        Returns:
            解释后的意图特征
        """
        intent_features = {
            'original_words': [],
            'interpreted_dimensions': {},
            'confidence': 0.0,
            'suggested_refinements': [],
            'inferred_scenario': None
        }
        
        # 检测主观词汇
        detected_words = []
        for word in self.SUBJECTIVE_MAPPINGS.keys():
            if word in query:
                detected_words.append(word)
                intent_features['original_words'].append(word)
        
        # 如果没有检测到主观词汇，返回空结果
        if not detected_words:
            return intent_features
        
        # 根据上下文推断用户场景
        for word in detected_words:
            mappings = self.SUBJECTIVE_MAPPINGS[word]
            scenario = self._infer_user_scenario(query, context, word)
            
            intent_features['interpreted_dimensions'][word] = {
                'difficulty': mappings['difficulty'],
                'difficulty_range': mappings['difficulty_range'],
                'cognitive_level': mappings['cognitive_level'],
                'question_features': mappings['question_features'],
                'prerequisites': mappings['prerequisites'],
                'inferred_scenario': scenario,
                'scenario_confidence': scenario['confidence']
            }
            
            intent_features['inferred_scenario'] = scenario
            intent_features['confidence'] = scenario['confidence']
            
            # 当置信度低时，生成优化建议
            if scenario['confidence'] < 0.5:
                suggestions = self._generate_refinements(word, mappings, scenario)
                intent_features['suggested_refinements'].extend(suggestions)
        
        return intent_features
    
    def _infer_user_scenario(self, query: str, context: dict, word: str) -> dict:
        """
        推断用户使用场景
        
        Args:
            query: 用户查询
            context: 上下文信息
            word: 检测到的主观词汇
            
        Returns:
            场景推断结果
        """
        scenarios = self.SUBJECTIVE_MAPPINGS[word]['user_scenarios']
        
        # 基于关键词匹配计算各场景得分
        scenario_scores = {}
        for scenario_name, scenario_info in scenarios.items():
            score = scenario_info['weight']
            
            # 检查查询中是否包含场景特征词
            for feature in scenario_info['features']:
                if feature in query:
                    score += 0.15
            
            # 检查查询中是否包含场景关键词
            for keyword in scenario_info.get('keywords', []):
                if keyword in query:
                    score += 0.2
            
            scenario_scores[scenario_name] = min(score, 1.0)
        
        # 选择最高分的场景
        if scenario_scores:
            best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
            return {
                'name': best_scenario[0],
                'confidence': best_scenario[1],
                'features': scenarios[best_scenario[0]]['features'],
                'all_scores': scenario_scores
            }
        
        return {
            'name': '未知',
            'confidence': 0.3,
            'features': [],
            'all_scores': {}
        }
    
    def _generate_refinements(self, word: str, mappings: dict, scenario: dict) -> list:
        """
        生成查询优化建议
        
        Args:
            word: 主观词汇
            mappings: 词汇映射配置
            scenario: 推断的场景
            
        Returns:
            优化建议列表
        """
        suggestions = []
        difficulty_range = mappings.get('difficulty_range', (1, 5))
        
        if word == '基础':
            suggestions = [
                f"💡 如果您是指'入门难度'，可以说'难度{difficulty_range[0]}-{difficulty_range[1]}的习题'",
                f"💡 如果您是指'概念理解'，可以说'{mappings['question_features'][0]}'",
                f"💡 如果您需要'新手入门'练习，可以说'刚学的知识点，需要简单练习'"
            ]
        elif word == '提高':
            suggestions = [
                f"💡 如果您是指'能力提升'，可以说'难度{difficulty_range[0]}-{difficulty_range[1]}的综合题'",
                f"💡 如果您是指'考前复习'，可以说'重点题型'或'典型例题'",
                f"💡 如果您需要'培优训练'，可以说'竞赛入门题'或'拔高题'"
            ]
        elif word == '难题':
            suggestions = [
                f"💡 如果您是指'高考压轴'，可以说'高考难度'或'压轴题'",
                f"💡 如果您是指'竞赛难度'，可以说'竞赛题'或'奥赛题'",
                f"💡 如果您需要'思维拓展'，可以说'探究题'或'开放题'"
            ]
        elif word == '简单':
            suggestions = [
                f"💡 如果您是指'快速练习'，可以说'刷题'或'大量练习'",
                f"💡 如果您是指'建立信心'，可以说'成功体验题'",
                f"💡 如果您需要'步骤少'的题，可以说'直接计算'或'一步得出'"
            ]
        elif word == '中等':
            suggestions = [
                f"💡 如果您是指'标准难度'，可以说'常规题'或'普通难度'",
                f"💡 如果您需要'阶段检测'，可以说'单元测试'或'水平评估'"
            ]
        elif word == '综合':
            suggestions = [
                f"💡 如果您是指'多知识点'，可以说'跨章节'或'知识整合'",
                f"💡 如果您需要'章节复习'，可以说'复习题'或'总结题'"
            ]
        
        return suggestions
    
    def calculate_difficulty_match_score(self, query_difficulty: dict, resource_difficulty: str) -> float:
        """
        计算难度匹配得分（考虑主观意图）
        
        Args:
            query_difficulty: 查询中的难度要求（来自interpret_intent）
            resource_difficulty: 资源的实际难度（1-5）
            
        Returns:
            匹配得分 0-1
        """
        if not resource_difficulty or not query_difficulty:
            return 1.0
        
        try:
            resource_diff = int(resource_difficulty)
            difficulty_range = query_difficulty.get('difficulty_range', (1, 5))
            
            min_diff, max_diff = difficulty_range
            
            # 在范围内得满分
            if min_diff <= resource_diff <= max_diff:
                return 1.0
            
            # 在范围外但接近，给予部分分数
            if resource_diff < min_diff:
                # 资源难度低于要求
                distance = min_diff - resource_diff
                return max(0, 1.0 - distance * 0.3)  # 每差1级减0.3
            else:
                # 资源难度高于要求
                distance = resource_diff - max_diff
                return max(0, 1.0 - distance * 0.4)  # 每差1级减0.4（更严格）
                
        except (ValueError, TypeError):
            return 1.0


class ContentFeatureExtractor:
    """教案内容特征提取器"""
    
    # 教学方法关键词库
    TEACHING_METHODS = {
        '小组讨论': ['小组讨论', '分组讨论', '合作学习', '小组合作', '协作学习'],
        '实验探究': ['实验', '探究', '探究式', '探究性', '发现式', '探索'],
        '案例分析': ['案例', '实例', '实际问题', '应用问题'],
        '翻转课堂': ['翻转课堂', '翻转', '课前预习', '课前学习'],
        '多媒体教学': ['多媒体', 'PPT', '课件', '视频', '动画', '信息化'],
        '情境教学': ['情境', '情景', '实际情境', '问题情境'],
        '启发式教学': ['启发', '引导', '提问', '问题驱动'],
        '讲授法': ['讲授', '讲解', '讲述', '精讲'],
        '练习巩固': ['练习', '课堂练习', '巩固', '训练'],
        '自主探究': ['自主', '自主探究', '自主学习', '独立探究'],
        '项目式学习': ['项目', '项目式', '任务驱动', '任务'],
        '游戏化教学': ['游戏', '游戏化', '趣味', '竞赛']
    }
    
    # 教学环节关键词库
    TEACHING_STAGES = {
        '导入': ['导入', '引入', '新课导入', '情境导入'],
        '新课讲授': ['讲授', '讲解', '新知', '新知识'],
        '例题讲解': ['例题', '示范', '示例'],
        '课堂练习': ['练习', '课堂练习', '随堂练习', '巩固练习'],
        '小组活动': ['小组', '活动', '讨论', '合作'],
        '总结归纳': ['总结', '归纳', '小结', '回顾'],
        '作业布置': ['作业', '课后', '布置'],
        '课堂检测': ['检测', '测试', '评价', '反馈']
    }
    
    # 教学手段关键词库
    TEACHING_TOOLS = {
        '多媒体': ['多媒体', 'PPT', '课件', '投影', '电子白板'],
        '实物教具': ['教具', '实物', '模型', '学具'],
        '几何画板': ['几何画板', 'GGB', 'GeoGebra', '图形软件'],
        '在线资源': ['网络', '在线', '互联网', '微课', '慕课']
    }
    
    # 习题难度关键词库
    EXERCISE_DIFFICULTY = {
        '简单': ['简单', '基础', '入门', '初级', '容易'],
        '中等': ['中等', '一般', '普通', '标准'],
        '困难': ['困难', '难', '高级', '拔高', '培优', '挑战', '综合']
    }
    
    # 习题类型关键词库
    EXERCISE_TYPES = {
        '选择题': ['选择题', '单选', '多选', '单选题', '多选题'],
        '填空题': ['填空题', '填空', '填充题', '填充', '空白题', '空白'],
        '解答题': ['解答题', '解答', '大题', '综合题', '简答题', '问答题', '论述题'],
        '计算题': ['计算题', '计算', '运算题', '算术题'],
        '证明题': ['证明题', '证明', '求证题', '推导题'],
        '应用题': ['应用题', '实际应用', '应用', '实际问题', '生活应用', '工程应用', '经济应用', '对数应用', '指数应用', '函数应用', '实际场景', '生活场景', '经济问题', '工程问题', '物理问题', '化学问题', '生物问题'],
        '作图题': ['作图题', '画图', '作图', '绘图题', '绘制题']
    }
    
    # 应用题场景关键词库
    APPLICATION_SCENES = {
        '生活场景': ['生活', '日常', '家庭', '购物', '消费', '工资', '收入', '支出', '水电费', '电话费', '出租车', '公交车', '地铁', '旅行', '旅游', '住宿', '餐饮', '购物'],
        '经济场景': ['经济', '金融', '投资', '理财', '股票', '债券', '利率', '利息', '利润', '成本', '收益', '价格', '销售', '市场', '需求', '供给'],
        '工程场景': ['工程', '建筑', '施工', '设计', '测量', '机械', '电力', '水利', '交通', '桥梁', '道路', '隧道', '建筑材料', '工程预算'],
        '物理场景': ['物理', '力学', '运动', '速度', '加速度', '力', '功', '能', '功率', '热学', '电学', '光学', '声学'],
        '化学场景': ['化学', '化学反应', '化学方程式', '化学平衡', '溶液', '浓度', 'pH值', '化学计算'],
        '生物场景': ['生物', '生态', '遗传', '进化', '细胞', '代谢', '生态系统', '生物多样性'],
        '天文场景': ['天文', '天体', '星系', '宇宙', '行星', '恒星', '卫星', '黑洞', '宇宙大爆炸'],
        '地理场景': ['地理', '地形', '地貌', '气候', '天气', '温度', '降水', '土壤', '植被', '人口', '城市', '国家', '地区']
    }
    
    def __init__(self):
        """初始化内容特征提取器"""
        # V12.0新增：初始化主观意图解释器
        self.subjective_interpreter = SubjectiveIntentInterpreter()
    
    def is_application_problem(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        检测题目是否是应用题
        
        Args:
            content: 题目内容
            metadata: 题目元数据
            
        Returns:
            是否是应用题
        """
        # 首先检查元数据中的题目类型
        if metadata:
            exercise_type = metadata.get('题目类型', '')
            if exercise_type:
                for keyword in self.EXERCISE_TYPES['应用题']:
                    if keyword in exercise_type:
                        return True
        
        # 检查内容中的应用题场景关键词
        if content:
            for scene, keywords in self.APPLICATION_SCENES.items():
                for keyword in keywords:
                    if keyword in content:
                        return True
        
        # 检查内容中的应用相关关键词
        for keyword in self.EXERCISE_TYPES['应用题']:
            if keyword in content:
                return True
        
        return False
    
    def extract_features(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        从教案内容中提取特征标签
        
        Args:
            content: 教案内容
            title: 教案标题
            
        Returns:
            特征标签字典
        """
        features = {
            'teaching_methods': [],  # 教学方法
            'teaching_stages': [],   # 教学环节
            'teaching_tools': [],    # 教学手段
            'has_group_work': False, # 是否有小组合作
            'has_experiment': False, # 是否有实验
            'has_multimedia': False, # 是否使用多媒体
            'has_practice': False,   # 是否有练习环节
            'content_summary': ''    # 内容摘要
        }
        
        if not content:
            return features
        
        # 提取教学方法
        for method, keywords in self.TEACHING_METHODS.items():
            if self._check_keywords(content, keywords):
                features['teaching_methods'].append(method)
        
        # 提取教学环节
        for stage, keywords in self.TEACHING_STAGES.items():
            if self._check_keywords(content, keywords):
                features['teaching_stages'].append(stage)
        
        # 提取教学手段
        for tool, keywords in self.TEACHING_TOOLS.items():
            if self._check_keywords(content, keywords):
                features['teaching_tools'].append(tool)
        
        # 设置布尔特征
        features['has_group_work'] = '小组讨论' in features['teaching_methods']
        features['has_experiment'] = '实验探究' in features['teaching_methods']
        features['has_multimedia'] = '多媒体教学' in features['teaching_methods'] or '多媒体' in features['teaching_tools']
        features['has_practice'] = '练习巩固' in features['teaching_methods'] or '课堂练习' in features['teaching_stages']
        
        # 生成内容摘要
        features['content_summary'] = self._generate_summary(content)
        
        return features
    
    def _check_keywords(self, content: str, keywords: List[str]) -> bool:
        """检查内容中是否包含关键词"""
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True
        return False
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        # 移除markdown标记和多余空白
        content = re.sub(r'[#*|`\[\]]', '', content)
        content = re.sub(r'\s+', '', content)
        
        # 返回前max_length个字符
        return content[:max_length] if len(content) > max_length else content
    
    def extract_query_content_features(self, query: str) -> Dict[str, Any]:
        """
        从用户查询中提取内容特征要求
        
        Args:
            query: 用户查询
            
        Returns:
            查询特征字典
        """
        features = {
            'has_content_requirement': False,  # 是否有内容要求
            'required_methods': [],            # 要求的教学方法
            'required_stages': [],             # 要求的教学环节
            'required_tools': [],              # 要求的教学手段
            'required_difficulty': None,        # 要求的习题难度
            'required_exercise_type': None,     # 要求的习题类型
            'query_type': 'theme',              # 查询类型：theme(主题) 或 content(内容)
            # V12.0新增：主观意图理解
            'subjective_intent': None,          # 主观意图解释结果
            'has_subjective_word': False,       # 是否包含主观词汇
            # V12.0改进2：年级识别
            'required_grade': None,             # 要求的年级
            'has_grade_requirement': False,     # 是否有年级要求
        }
        
        # V12.0新增：首先进行主观意图解释
        subjective_features = self.subjective_interpreter.interpret_intent(query)
        if subjective_features['original_words']:
            features['subjective_intent'] = subjective_features
            features['has_subjective_word'] = True
            features['has_content_requirement'] = True
            features['query_type'] = 'content'
            
            # 从主观意图推断难度要求
            if subjective_features['interpreted_dimensions']:
                # 获取第一个检测到的主观词汇的难度范围
                first_word = subjective_features['original_words'][0]
                dim = subjective_features['interpreted_dimensions'][first_word]
                diff_range = dim['difficulty_range']
                
                # 映射到原有的难度分类
                if diff_range[1] <= 2:
                    features['required_difficulty'] = '简单'
                elif diff_range[0] >= 4:
                    features['required_difficulty'] = '困难'
                else:
                    features['required_difficulty'] = '中等'
        
        # 检查是否包含内容要求关键词
        all_content_keywords = []
        for keywords in self.TEACHING_METHODS.values():
            all_content_keywords.extend(keywords)
        for keywords in self.TEACHING_STAGES.values():
            all_content_keywords.extend(keywords)
        for keywords in self.TEACHING_TOOLS.values():
            all_content_keywords.extend(keywords)
        for keywords in self.EXERCISE_DIFFICULTY.values():
            all_content_keywords.extend(keywords)
        for keywords in self.EXERCISE_TYPES.values():
            all_content_keywords.extend(keywords)
        
        # 检查查询中是否包含内容特征词
        for keyword in all_content_keywords:
            if keyword in query:
                features['has_content_requirement'] = True
                break
        
        # 如果包含内容要求，提取具体的教学方法、环节、手段
        if features['has_content_requirement']:
            features['query_type'] = 'content'
            
            # 提取教学方法要求
            for method, keywords in self.TEACHING_METHODS.items():
                if self._check_keywords(query, keywords):
                    features['required_methods'].append(method)
            
            # 提取教学环节要求
            for stage, keywords in self.TEACHING_STAGES.items():
                if self._check_keywords(query, keywords):
                    features['required_stages'].append(stage)
            
            # 提取教学手段要求
            for tool, keywords in self.TEACHING_TOOLS.items():
                if self._check_keywords(query, keywords):
                    features['required_tools'].append(tool)
            
            # 提取习题难度要求（如果主观意图没有设置）
            if not features['required_difficulty']:
                for difficulty, keywords in self.EXERCISE_DIFFICULTY.items():
                    if self._check_keywords(query, keywords):
                        features['required_difficulty'] = difficulty
                        break
            
            # 提取习题类型要求
            for ex_type, keywords in self.EXERCISE_TYPES.items():
                if self._check_keywords(query, keywords):
                    features['required_exercise_type'] = ex_type
                    break
        
        # V12.0改进2：年级识别
        grade_enricher = get_grade_enricher()
        grade_info = grade_enricher.infer_grade_from_title(query)
        
        if grade_info:
            features['required_grade'] = grade_info['grade']
            features['has_grade_requirement'] = True
            features['has_content_requirement'] = True
            features['query_type'] = 'content'
        
        return features
    
    def calculate_content_match_score(self, resource_features: Dict[str, Any], query_features: Dict[str, Any], resource_metadata: Dict[str, Any] = None, resource_content: str = None) -> float:
        """
        计算内容匹配得分
        
        Args:
            resource_features: 资源特征（教案）
            query_features: 查询特征
            resource_metadata: 资源元数据（习题）
            resource_content: 资源内容（习题）
            
        Returns:
            匹配得分 (0-1)
        """
        if not query_features['has_content_requirement']:
            return 1.0  # 没有内容要求，默认满分
        
        scores = []
        
        # V12.0改进：使用主观意图解释器的难度匹配逻辑
        if query_features.get('subjective_intent') and resource_metadata:
            # 使用新的主观意图匹配逻辑
            subjective_intent = query_features['subjective_intent']
            difficulty_str = resource_metadata.get('难度（1-5）', '')
            
            if difficulty_str and subjective_intent['interpreted_dimensions']:
                # 获取第一个主观词汇的维度
                first_word = subjective_intent['original_words'][0]
                query_difficulty = subjective_intent['interpreted_dimensions'][first_word]
                
                difficulty_score = self.subjective_interpreter.calculate_difficulty_match_score(
                    query_difficulty, difficulty_str
                )
                scores.append(difficulty_score)
        
        # 原有的难度匹配逻辑（作为后备）
        elif query_features['required_difficulty'] and resource_metadata:
            difficulty_str = resource_metadata.get('难度（1-5）', '')
            if difficulty_str:
                try:
                    difficulty = int(difficulty_str)
                    # 简单: 1-2, 中等: 3, 困难: 4-5
                    if query_features['required_difficulty'] == '简单':
                        difficulty_score = 1.0 if difficulty <= 2 else 0.0
                    elif query_features['required_difficulty'] == '中等':
                        difficulty_score = 1.0 if difficulty == 3 else 0.0
                    elif query_features['required_difficulty'] == '困难':
                        difficulty_score = 1.0 if difficulty >= 4 else 0.0
                    else:
                        difficulty_score = 1.0
                    scores.append(difficulty_score)
                except:
                    pass
        
        # 习题类型匹配
        # V9.5改进：对于"计算题"，放宽限制，只要不是"选择题"都算匹配
        # V10.0改进：增强题型识别，支持"应用题"、"综合题"、"方程组"等题型
        # V11.0改进：增强应用题识别，基于场景关键词库
        if query_features['required_exercise_type'] and resource_metadata:
            exercise_type = resource_metadata.get('题目类型', '')
            required_type = query_features['required_exercise_type']
            
            # 特殊处理应用题
            if required_type == '应用题':
                # 检查资源内容和元数据，判断是否是应用题
                resource_content = resource_content or resource_metadata.get('题干', '') + resource_metadata.get('题目描述', '')
                is_app = self.is_application_problem(resource_content, resource_metadata)
                scores.append(1.0 if is_app else 0.0)
            # V9.5改进：对于"计算题"，只要不是"选择题"都算匹配
            elif required_type == '计算题':
                # 如果是选择题，得0分；否则得1分
                if exercise_type and '选择题' in exercise_type:
                    scores.append(0.0)
                else:
                    scores.append(1.0)
            # 其他题型匹配
            else:
                # 精确匹配题目类型
                if required_type in exercise_type:
                    scores.append(1.0)
                else:
                    scores.append(0.0)
        
        # 教学方法匹配（教案）
        if query_features['required_methods'] and resource_features.get('teaching_methods'):
            method_matches = set(resource_features['teaching_methods']) & set(query_features['required_methods'])
            method_score = len(method_matches) / len(query_features['required_methods'])
            scores.append(method_score)
        
        # 教学环节匹配（教案）
        if query_features['required_stages'] and resource_features.get('teaching_stages'):
            stage_matches = set(resource_features['teaching_stages']) & set(query_features['required_stages'])
            stage_score = len(stage_matches) / len(query_features['required_stages'])
            scores.append(stage_score)
        
        # 教学手段匹配（教案）
        if query_features['required_tools'] and resource_features.get('teaching_tools'):
            tool_matches = set(resource_features['teaching_tools']) & set(query_features['required_tools'])
            tool_score = len(tool_matches) / len(query_features['required_tools'])
            scores.append(tool_score)
        
        # V12.0改进2：年级匹配
        if query_features.get('required_grade') and resource_metadata:
            grade_enricher = get_grade_enricher()
            resource_grade_level = resource_metadata.get('grade_level', 0)
            query_grade = query_features['required_grade']
            
            grade_score = grade_enricher.calculate_grade_match_score(
                resource_grade_level, query_grade
            )
            
            # 只有当年级匹配得分较低时才影响总分
            if grade_score < 0.5:
                scores.append(grade_score)
            elif grade_score < 0.8:
                # 部分匹配，轻微影响
                scores.append(grade_score)
        
        if not scores:
            return 1.0
        
        # 返回平均得分
        return sum(scores) / len(scores)


# 全局实例
_content_extractor = None

def get_content_feature_extractor() -> ContentFeatureExtractor:
    """获取内容特征提取器实例（单例模式）"""
    global _content_extractor
    if _content_extractor is None:
        _content_extractor = ContentFeatureExtractor()
    return _content_extractor
