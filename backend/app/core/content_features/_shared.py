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
from ..grade_metadata_enricher import get_grade_enricher


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


