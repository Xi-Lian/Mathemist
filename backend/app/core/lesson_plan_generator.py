"""
教案生成模块

职责：
- 根据用户需求和检索到的资源生成教案
- 整合理论依据和优秀教案特征
- 提供结构化的教案输出
- 明确标注理论依据的使用场景和作用

依赖：
- model_config (模型配置)
- langchain (提示词和链)
"""

from typing import Dict, Any, List
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config
from .config_manager import config_manager


class LessonPlanGenerator:
    """教案生成器"""
    
    def __init__(self):
        """初始化教案生成器"""
        self.model_config = model_config
        
        # 加载优秀教案共性文件
        self.lesson_plan_common_characteristics = self._load_lesson_plan_common_characteristics()
        
        # 加载理论卡片文件
        self.theory_cards = self._load_theory_cards()
        
        # 解析理论卡片，建立索引
        self.theory_cards_index = self._parse_theory_cards()
        
        self.prompt_template = self._create_prompt_template()
    
    def _load_lesson_plan_common_characteristics(self) -> str:
        """加载优秀教案共性文件（多路径容错）"""
        try:
            # 尝试多个可能的路径
            learning_resource_path = config_manager.get_learning_resource_path()
            possible_paths = [
                # 从配置的学习资源目录加载
                Path(learning_resource_path) / "教案" / "优秀教案共性整合（最终版）.md",
                # 相对路径 1: 从当前文件向上4级
                Path(__file__).parent.parent.parent.parent / "learning_resource" / "教案" / "优秀教案共性整合（最终版）.md",
                # 相对路径 2: 从当前文件向上3级
                Path(__file__).parent.parent.parent / "learning_resource" / "教案" / "优秀教案共性整合（最终版）.md",
                # 相对路径 3: 当前目录
                Path(__file__).parent / "learning_resource" / "教案" / "优秀教案共性整合（最终版）.md",
                # 绝对路径: 当前工作目录
                Path.cwd() / "learning_resource" / "教案" / "优秀教案共性整合（最终版）.md"
            ]
            
            for i, file_path in enumerate(possible_paths, 1):
                print(f"📂 尝试路径 {i}: {file_path}")
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"✅ 成功加载优秀教案共性文件: {len(content)} 字符")
                        return content
                else:
                    print(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            print(f"⚠️ 加载优秀教案共性文件失败: {e}")
        
        # 内置默认内容
        default_content = """**优秀教案共性整合**

**一、教学目标设计**
- 目标明确，紧扣核心内容
- 核心素养导向突出
- 目标分层清晰，体现层次性

**二、教学结构设计**
- 流程完整：情境导入→新知探究→典例分析→跟踪训练→课堂小结→作业布置
- 符合认知发展规律
- 整体衔接性强

**三、教学内容与方法**
- 情境导入贴近生活
- 强调探究式学习
- 典例与训练配套精准
- 思想方法显化

**四、教学工具与资源**
- 多媒体与信息技术辅助教学
- 板书与练习系统清晰

**五、教学评价与反馈**
- 当堂检测与反馈及时
- 作业设计呼应课堂
- 教学反思常态化

**六、学生主体与互动**
- 以学生为中心
- 语言启发性强
- 关注认知难点与易错点
"""
        print("📝 使用内置默认优秀教案共性内容")
        return default_content
    
    def _load_theory_cards(self) -> str:
        """加载理论卡片文件（多路径容错）"""
        try:
            # 尝试多个可能的路径
            learning_resource_path = config_manager.get_learning_resource_path()
            possible_paths = [
                # 从配置的学习资源目录加载
                Path(learning_resource_path) / "理论卡片" / "理论卡片.md",
                # 相对路径 1: 从当前文件向上4级
                Path(__file__).parent.parent.parent.parent / "learning_resource" / "理论卡片" / "理论卡片.md",
                # 相对路径 2: 从当前文件向上3级
                Path(__file__).parent.parent.parent / "learning_resource" / "理论卡片" / "理论卡片.md",
                # 相对路径 3: 当前目录
                Path(__file__).parent / "learning_resource" / "理论卡片" / "理论卡片.md",
                # 绝对路径: 当前工作目录
                Path.cwd() / "learning_resource" / "理论卡片" / "理论卡片.md"
            ]
            
            for i, file_path in enumerate(possible_paths, 1):
                print(f"📂 尝试路径 {i}: {file_path}")
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"✅ 成功加载理论卡片文件: {len(content)} 字符")
                        return content
                else:
                    print(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            print(f"⚠️ 加载理论卡片文件失败: {e}")
        
        # 内置默认理论卡片
        default_content = """# 教育理论卡片集

## 理论卡片1：建构主义学习理论
**核心观点**：学习是学习者主动建构知识的过程，不是被动接受信息的过程。
**适用环节**：新知探究、小组合作、自主学习
**教学启发**：设置问题情境，引导学生自主探究，通过协作学习建构知识体系。

## 理论卡片2：最近发展区理论
**核心观点**：教学应着眼于学生的最近发展区，为学生提供带有难度的内容，调动学生的积极性。
**适用环节**：新知探究、典例分析、分层作业
**教学启发**：设计梯度问题，搭建学习脚手架，促进学生从现有水平向潜在发展水平过渡。

## 理论卡片3：多元智能理论
**核心观点**：每个人都有不同的智能优势，教育应尊重个体差异，因材施教。
**适用环节**：分层作业、小组合作、课堂评价
**教学启发**：设计多样化的学习活动，提供多元评价方式，满足不同学生的学习需求。

## 理论卡片4：认知负荷理论
**核心观点**：学习过程中的认知负荷应控制在合理范围内，避免认知超载。
**适用环节**：新知讲解、典例分析、练习设计
**教学启发**：简化教学材料，分步呈现复杂内容，提供认知支持。

## 理论卡片5：学习动机理论
**核心观点**：内部动机是学习的最佳动力，教师应激发学生的学习兴趣和内在动机。
**适用环节**：情境导入、课堂小结、作业设计
**教学启发**：创设真实情境，设置挑战性任务，提供及时反馈，增强学习成就感。

## 理论卡片6：合作学习理论
**核心观点**：通过小组合作，学生可以相互学习、相互促进，共同完成学习任务。
**适用环节**：新知探究、问题解决、项目学习
**教学启发**：设计结构化的小组活动，明确角色分工，建立有效的合作机制。

## 理论卡片7：探究式学习理论
**核心观点**：学生通过自主探究、发现问题、解决问题的过程获得知识和技能。
**适用环节**：新知探究、实验教学、项目学习
**教学启发**：设置探究任务，提供必要的资源和指导，鼓励学生提出假设和验证。

## 理论卡片8：反馈理论
**核心观点**：及时、具体、有针对性的反馈是促进学习的重要因素。
**适用环节**：课堂练习、作业批改、学习评价
**教学启发**：提供及时的学习反馈，指出优点和改进方向，鼓励学生自我反思。

## 理论卡片9：元认知理论
**核心观点**：元认知是对认知过程的认知，包括计划、监控和评估学习活动。
**适用环节**：学习策略指导、课堂小结、自主学习
**教学启发**：教给学生学习策略，引导学生监控学习过程，培养自我评估能力。

## 理论卡片10：情境学习理论
**核心观点**：学习应在真实的情境中进行，知识只有在应用中才有意义。
**适用环节**：情境导入、应用练习、项目学习
**教学启发**：创设真实的问题情境，让学生在解决实际问题中学习和应用知识。"""
        print("📝 使用内置默认理论卡片内容")
        return default_content
    
    def _parse_theory_cards(self) -> Dict[str, Dict[str, str]]:
        """
        解析理论卡片，建立结构化索引
        
        Returns:
            理论卡片索引字典，格式为：
            {
                "理论卡片1": {
                    "name": "建构主义学习理论",
                    "core_view": "学习是学习者主动建构知识的过程，不是被动接受信息的过程。",
                    "applicable_links": "新知探究、小组合作、自主学习",
                    "applicable_methods": "探究式、合作学习",
                    "applicable_content": "概念教学、问题解决",
                    "teaching_inspiration": "设置问题情境，引导学生自主探究，通过协作学习建构知识体系。"
                },
                ...
            }
        """
        import re
        index = {}
        
        # 匹配理论卡片的正则表达式（支持表格格式）
        # 格式: | **理论卡片一：建构主义学习理论** |
        #       +----------------------------------+
        #       | **核心观点** | 内容 |
        #       +----------------------------------+
        #       | **教学启发** | 内容 |
        #       +----------------------------------+
        #       | **适用环节** | 内容 |
        #       +----------------------------------+
        
        # 匹配理论卡片标题
        card_pattern = r"\| \*\*理论卡片([一二三四五六七八九十]+)：([^\|]+)\*\*\s*\|"
        
        # 查找所有理论卡片
        card_matches = list(re.finditer(card_pattern, self.theory_cards, re.DOTALL))
        
        for i, card_match in enumerate(card_matches):
            card_number_chinese = card_match.group(1)
            card_name = card_match.group(2).strip()
            
            # 转换中文数字为阿拉伯数字
            chinese_to_arabic = {
                "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
                "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"
            }
            card_number = chinese_to_arabic.get(card_number_chinese, str(i + 1))
            
            # 获取当前理论卡片的完整内容（直到下一个理论卡片或文件结束）
            start_pos = card_match.start()
            end_pos = card_matches[i + 1].start() if i + 1 < len(card_matches) else len(self.theory_cards)
            card_content = self.theory_cards[start_pos:end_pos]
            
            # 提取核心观点
            core_view = ""
            core_view_match = re.search(r"\|\s*\*\*核心观点\*\*\s*\|\s*([^\|]+)\s*\|", card_content, re.DOTALL)
            if core_view_match:
                core_view = core_view_match.group(1).strip()
                # 清理多余的内容
                core_view = re.sub(r'\^\[\d+\]', '', core_view)  # 移除引用标记
                core_view = re.sub(r'\s+', ' ', core_view)  # 规范化空格
            
            # 提取适用环节
            applicable_links = ""
            applicable_links_match = re.search(r"\|\s*\*\*适用环节\*\*\s*\|\s*([^\|]+)\s*\|", card_content, re.DOTALL)
            if applicable_links_match:
                applicable_links = applicable_links_match.group(1).strip()
            
            # 提取教学启发（提取所有相关内容）
            teaching_inspiration = ""
            teaching_inspiration_elements = []
            
            # 查找教学启发表格部分
            teaching_inspiration_section = re.search(r"\|\s*\*\*教学启发\*\*\s*\|.*?\+(?:-+\+)+.*?\|(?:\s*\|.*?)+", card_content, re.DOTALL)
            if teaching_inspiration_section:
                teaching_inspiration_text = teaching_inspiration_section.group(0)
                
                # 提取教学启发表格中的标题行（第一行）
                title_match = re.search(r"\|\s*\*\*教学启发\*\*\s*\|.*\|", teaching_inspiration_text, re.DOTALL)
                if title_match:
                    title_line = title_match.group(0)
                    # 提取所有标题（如"情境的真实性"、"脚手架式的引导"），排除"教学启发"本身
                    titles = re.findall(r"\*\*([^*]+)\*\*", title_line)
                    teaching_inspiration_elements = [title.strip() for title in titles if title.strip() and title.strip() != "教学启发"]
                
                # 提取教学启发表格中的内容行（第二行）
                content_match = re.search(r"\|\s+.*?\|.*?\|.*?\|", teaching_inspiration_text, re.DOTALL)
                if content_match:
                    content_line = content_match.group(0)
                    # 提取所有内容
                    contents = re.findall(r"\|\s+([^|]+?)\s*\|", content_line)
                    teaching_inspiration = " ".join([content.strip() for content in contents if content.strip()])
                    # 清理多余的内容
                    teaching_inspiration = re.sub(r'\^\[\d+\]', '', teaching_inspiration)
                    teaching_inspiration = re.sub(r'\s+', ' ', teaching_inspiration)
            
            # 如果没有提取到教学启发要素，尝试从教学启发文本中提取
            if not teaching_inspiration_elements and teaching_inspiration:
                teaching_inspiration_elements = self._parse_teaching_inspiration_elements(teaching_inspiration)
            
            # 提取适用教学方法（基于理论名称和核心观点）
            applicable_methods = self._extract_applicable_methods(card_name, core_view)
            
            # 提取适用内容类型（基于理论名称和核心观点）
            applicable_content = self._extract_applicable_content(card_name, core_view)
            
            card_key = f"理论卡片{card_number}"
            index[card_key] = {
                "name": card_name,
                "core_view": core_view,
                "applicable_links": applicable_links,
                "applicable_methods": applicable_methods,
                "applicable_content": applicable_content,
                "teaching_inspiration": teaching_inspiration,
                "teaching_inspiration_elements": teaching_inspiration_elements
            }
        
        print(f"✅ 成功解析 {len(index)} 个理论卡片")
        return index
    
    def _parse_teaching_inspiration_elements(self, teaching_inspiration: str) -> List[str]:
        """
        智能解析教学启发，提取多个独立维度
        
        Args:
            teaching_inspiration: 教学启发文本
        
        Returns:
            教学启发要素列表
        """
        if not teaching_inspiration:
            return []
        
        elements = []
        
        # 尝试多种分隔符
        separators = ['，', '。', '；', ';', '；', '、', '，', '\n']
        
        # 首先尝试按分隔符分割
        for sep in separators:
            if sep in teaching_inspiration:
                parts = teaching_inspiration.split(sep)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 2:  # 过滤掉太短的片段
                        elements.append(part)
                if len(elements) >= 2:
                    break
        
        # 如果没有找到合适的分隔符，尝试按动词短语分割
        if len(elements) < 2:
            import re
            verb_patterns = [
                r'(设置|设计|创设|提供|引导|鼓励|通过|帮助|优化|简化|分步|建立|明确|培养|激发|增强|促进|搭建|搭建|组织|实现|体现|利用|运用|采用|采用|结合|整合|融合|融合)',
                r'(问题情境|学习情境|教学情境|真实情境|探究任务|学习任务|教学任务|学习活动|教学活动|小组活动|合作活动|探究活动|实践活动|应用活动)',
                r'(脚手架|认知支持|学习支持|教学支持|反馈机制|评价机制|合作机制|学习机制|教学机制)',
                r'(学习兴趣|学习动机|内在动机|外部动机|学习成就感|学习体验|学习效果|学习效率|学习质量)',
                r'(知识体系|知识网络|知识结构|知识框架|知识体系|知识建构|意义建构|认知建构)',
                r'(学习策略|学习方法|学习过程|学习活动|学习行为|学习习惯|学习态度|学习价值观)'
            ]
            
            for pattern in verb_patterns:
                matches = re.findall(pattern, teaching_inspiration)
                if matches:
                    for match in matches:
                        if match not in elements:
                            elements.append(match)
                    if len(elements) >= 2:
                        break
        
        # 如果还是没有足够的要素，尝试按句子分割
        if len(elements) < 2:
            import re
            sentences = re.split(r'[。！？]', teaching_inspiration)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 4:
                    elements.append(sentence)
        
        # 去重并保持顺序
        seen = set()
        unique_elements = []
        for element in elements:
            if element not in seen:
                seen.add(element)
                unique_elements.append(element)
        
        return unique_elements
    
    def _extract_applicable_methods(self, theory_name: str, core_view: str) -> str:
        """
        动态提取理论适用的教学方法（基于理论名称和核心观点的关键词分析）
        
        Args:
            theory_name: 理论名称
            core_view: 理论核心观点
        
        Returns:
            适用的教学方法
        """
        import re
        
        # 从理论名称和核心观点中提取关键词
        combined_text = theory_name + " " + core_view
        
        # 定义教学方法关键词
        method_keywords = {
            "讲授式": ["讲授", "讲解", "传递", "灌输", "呈现", "示范", "演示"],
            "探究式": ["探究", "发现", "探索", "研究", "实验", "调查", "自主", "建构"],
            "合作学习": ["合作", "协作", "小组", "团队", "同伴", "互动", "交流"],
            "自主学习": ["自主", "独立", "自我", "元认知", "监控", "反思"],
            "翻转课堂": ["翻转", "课前", "课后", "预习", "复习"],
            "项目式学习": ["项目", "实践", "应用", "综合", "真实情境"],
            "混合式教学": ["混合", "多种", "多元", "综合", "多样化"]
        }
        
        # 匹配教学方法
        matched_methods = []
        for method, keywords in method_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched_methods.append(method)
                    break
        
        # 如果没有匹配到，返回"所有教学方法"
        if not matched_methods:
            return "所有教学方法"
        
        # 去重
        matched_methods = list(set(matched_methods))
        
        # 如果匹配到多个方法，返回前3个
        if len(matched_methods) > 3:
            matched_methods = matched_methods[:3]
        
        return "、".join(matched_methods)
    
    def _extract_applicable_content(self, theory_name: str, core_view: str) -> str:
        """
        动态提取理论适用的内容类型（基于理论名称和核心观点的关键词分析）
        
        Args:
            theory_name: 理论名称
            core_view: 理论核心观点
        
        Returns:
            适用的内容类型
        """
        import re
        
        # 从理论名称和核心观点中提取关键词
        combined_text = theory_name + " " + core_view
        
        # 定义内容类型关键词
        content_keywords = {
            "概念教学": ["概念", "定义", "原理", "性质", "规律", "公式", "定理"],
            "技能训练": ["技能", "技巧", "方法", "操作", "计算", "解题", "练习"],
            "问题解决": ["问题", "解决", "应用", "实际", "情境", "任务", "挑战"],
            "知识讲解": ["知识", "讲解", "传递", "信息", "内容", "材料"],
            "实验教学": ["实验", "实践", "操作", "观察", "验证", "探究"],
            "项目学习": ["项目", "综合", "实践", "应用", "研究", "创作"],
            "学习策略": ["策略", "方法", "技巧", "元认知", "监控", "反思"],
            "记忆策略": ["记忆", "保持", "提取", "存储", "编码"],
            "复习总结": ["复习", "总结", "梳理", "归纳", "整合", "网络"],
            "学习评价": ["评价", "反馈", "评估", "测试", "考核"],
            "习惯养成": ["习惯", "行为", "规范", "养成", "塑造"],
            "个性化学习": ["个体", "差异", "因材施教", "多元", "智能"]
        }
        
        # 匹配内容类型
        matched_content = []
        for content, keywords in content_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched_content.append(content)
                    break
        
        # 如果没有匹配到，返回"所有内容类型"
        if not matched_content:
            return "所有内容类型"
        
        # 去重
        matched_content = list(set(matched_content))
        
        # 如果匹配到多个内容类型，返回前4个
        if len(matched_content) > 4:
            matched_content = matched_content[:4]
        
        return "、".join(matched_content)
    
    def _extract_theory_elements(self, theory_name: str, core_view: str) -> str:
        """
        动态提取理论要素（基于理论名称和核心观点的关键词分析）
        
        Args:
            theory_name: 理论名称
            core_view: 理论核心观点
        
        Returns:
            理论要素，以逗号分隔
        """
        import re
        
        # 从理论名称和核心观点中提取关键词
        combined_text = theory_name + " " + core_view
        
        # 定义理论要素关键词
        element_keywords = {
            "主动建构": ["主动", "建构", "建构主义", "意义建构"],
            "情境学习": ["情境", "真实情境", "问题情境", "情境学习"],
            "协作学习": ["协作", "合作", "小组", "同伴", "互动"],
            "意义建构": ["意义", "建构", "理解", "认知"],
            "最近发展区": ["最近发展区", "潜在", "发展", "水平"],
            "脚手架": ["脚手架", "支架", "支持", "引导"],
            "教学支架": ["支架", "支持", "引导", "帮助"],
            "多元智能": ["多元智能", "智能", "个体差异", "因材施教"],
            "个体差异": ["个体", "差异", "个性", "不同"],
            "因材施教": ["因材施教", "个性化", "差异化"],
            "认知负荷": ["认知负荷", "负荷", "工作记忆", "超载"],
            "工作记忆": ["工作记忆", "短期记忆", "记忆容量"],
            "长期记忆": ["长期记忆", "记忆存储", "知识保持"],
            "认知超载": ["超载", "过载", "信息过载"],
            "内部动机": ["内部动机", "内在动机", "兴趣", "好奇心"],
            "外部动机": ["外部动机", "奖励", "强化"],
            "自我效能感": ["自我效能", "信心", "能力感"],
            "成就动机": ["成就", "目标", "挑战"],
            "小组合作": ["小组", "合作", "团队", "协作"],
            "同伴学习": ["同伴", "互助", "互学"],
            "协作建构": ["协作", "共建", "共同建构"],
            "责任分工": ["分工", "责任", "角色"],
            "自主探究": ["自主", "探究", "探索", "发现"],
            "问题导向": ["问题", "导向", "驱动"],
            "发现学习": ["发现", "探索", "研究"],
            "科学探究": ["科学", "探究", "实验"],
            "及时反馈": ["及时", "反馈", "即时"],
            "具体反馈": ["具体", "明确", "详细"],
            "针对性反馈": ["针对", "个性化", "定向"],
            "形成性评价": ["形成性", "过程", "发展"],
            "元认知": ["元认知", "认知认知", "反思认知"],
            "自我监控": ["自我监控", "监控", "调节"],
            "自我评估": ["自我评估", "自评", "反思"],
            "学习策略": ["策略", "方法", "技巧"],
            "真实情境": ["真实", "实际", "现实"],
            "知识应用": ["应用", "运用", "实践"],
            "社会实践": ["社会", "实践", "体验"],
            "刺激-反应": ["刺激", "反应", "联结"],
            "强化": ["强化", "奖励", "惩罚"],
            "行为塑造": ["塑造", "形成", "培养"],
            "习惯养成": ["习惯", "养成", "培养"],
            "信息加工": ["信息", "加工", "处理"],
            "认知结构": ["认知结构", "图式", "框架"],
            "知识表征": ["表征", "表示", "编码"],
            "记忆存储": ["存储", "保持", "提取"],
            "再创造": ["再创造", "创造", "发现"],
            "数学发现": ["发现", "探索", "研究"],
            "自主建构": ["自主", "建构", "构建"],
            "数学思维": ["思维", "推理", "逻辑"]
        }
        
        # 匹配理论要素
        matched_elements = []
        for element, keywords in element_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched_elements.append(element)
                    break
        
        # 如果没有匹配到，返回默认理论要素
        if not matched_elements:
            return "核心观点、教学应用、学习过程"
        
        # 去重
        matched_elements = list(set(matched_elements))
        
        # 如果匹配到多个要素，返回前4个
        if len(matched_elements) > 4:
            matched_elements = matched_elements[:4]
        
        return "、".join(matched_elements)
    
    def _enhance_theory_card_parsing(self, theory_index: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """
        增强理论卡片解析，提取教学启发要素
        
        Args:
            theory_index: 理论卡片索引
        
        Returns:
            增强后的理论卡片索引
        """
        import re
        
        for card_key, card_info in theory_index.items():
            # 提取教学启发要素
            teaching_inspiration = card_info.get('teaching_inspiration', '')
            teaching_inspiration_elements = []
            
            if teaching_inspiration:
                # 尝试从教学启发中提取具体要素
                elements = re.split(r'[，。；]', teaching_inspiration)
                for element in elements:
                    element = element.strip()
                    if element:
                        teaching_inspiration_elements.append(element)
            
            # 添加教学启发要素到理论卡片信息
            card_info['teaching_inspiration_elements'] = teaching_inspiration_elements
        
        return theory_index
    
    def _enhance_theory_card_parsing(self, theory_index: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """
        增强理论卡片解析，提取教学启发要素
        
        Args:
            theory_index: 理论卡片索引
        
        Returns:
            增强后的理论卡片索引
        """
        import re
        
        for card_key, card_info in theory_index.items():
            # 提取教学启发要素
            teaching_inspiration = card_info.get('teaching_inspiration', '')
            teaching_inspiration_elements = []
            
            if teaching_inspiration:
                # 尝试从教学启发中提取具体要素
                elements = re.split(r'[，。；]', teaching_inspiration)
                for element in elements:
                    element = element.strip()
                    if element:
                        teaching_inspiration_elements.append(element)
            
            # 添加教学启发要素到理论卡片信息
            card_info['teaching_inspiration_elements'] = teaching_inspiration_elements
        
        return theory_index
    
    def _generate_deep_theory_reference(self, card_key: str, section: str, teaching_method: str) -> str:
        """
        生成深度理论引用，体现教学启发
        
        Args:
            card_key: 理论卡片键
            section: 教学环节
            teaching_method: 教学方法
        
        Returns:
            深度理论引用
        """
        theory_info = self.theory_cards_index.get(card_key, {})
        theory_name = theory_info.get('name', '未知理论')
        core_view = theory_info.get('core_view', '未知核心观点')
        teaching_inspiration = theory_info.get('teaching_inspiration', '')
        teaching_inspiration_elements = theory_info.get('teaching_inspiration_elements', [])
        
        # 构建深度理论引用
        reference_parts = [
            f"{card_key}：{theory_name}",
            f"核心观点：{core_view}"
        ]
        
        # 添加教学启发信息
        if teaching_inspiration:
            reference_parts.append(f"教学启发：{teaching_inspiration}")
        
        # 添加教学启发要素应用
        if teaching_inspiration_elements:
            application_info = "设计体现了教学启发中的：" + "、".join(teaching_inspiration_elements)
            reference_parts.append(f"应用场景：{application_info}")
        else:
            reference_parts.append("应用场景：详细说明该理论如何指导本环节设计")
        
        return " - ".join(reference_parts)
    
    def _generate_application_case(self, theory_name: str, applicable_links: str) -> str:
        """
        生成理论应用案例
        
        Args:
            theory_name: 理论名称
            applicable_links: 适用环节
        
        Returns:
            应用案例描述
        """
        # 理论名称与应用案例模板的映射
        case_templates = {
            "建构主义": f"通过{applicable_links}等活动，让学生自主建构知识体系，体现了学生的主体地位。",
            "最近发展区": f"通过设计梯度问题、搭建学习脚手架等方式，帮助学生突破{applicable_links}中的学习难点。",
            "多元智能": f"通过{applicable_links}等多样化活动，满足不同学生的学习需求，发挥学生的智能优势。",
            "认知负荷": f"通过简化教学材料、分步呈现内容等方式，降低{applicable_links}中的认知负荷。",
            "学习动机": f"通过创设真实情境、设置挑战性任务等方式，激发学生在{applicable_links}中的学习动机。",
            "合作学习": f"通过小组讨论、协作探究等方式，在{applicable_links}中培养学生的合作能力。",
            "探究式": f"通过问题引导、自主探究等方式，让学生在{applicable_links}中体验科学探究的过程。",
            "反馈": f"通过及时、具体的反馈，帮助学生在{applicable_links}中改进学习方法。",
            "元认知": f"通过指导学习策略、引导自我监控等方式，培养学生在{applicable_links}中的元认知能力。",
            "情境学习": f"通过创设真实问题情境，让学生在{applicable_links}中应用知识解决实际问题。",
            "行为主义": f"通过反复练习、及时强化等方式，帮助学生在{applicable_links}中养成良好的学习习惯。",
            "认知主义": f"通过优化信息呈现、帮助建立知识网络等方式，提高学生在{applicable_links}中的学习效率。",
            "再创造": f"通过引导观察、归纳、猜想、验证等过程，让学生在{applicable_links}中体验知识创造的过程。"
        }
        
        # 匹配理论名称中的关键词
        for keyword, template in case_templates.items():
            if keyword in theory_name:
                return template
        
        # 默认应用案例
        return f"通过设计有效的教学活动，在{applicable_links}中体现了该理论的应用价值。"
    
    def _validate_theory_references(self, lesson_plan: str, teaching_method: str = "讲授式", content_type: str = "概念教学") -> str:
        """
        验证教案中的理论引用
        
        Args:
            lesson_plan: 生成的教案文本
            teaching_method: 教学方法类型
            content_type: 教学内容类型
        
        Returns:
            验证并修正后的教案文本
        """
        import re
        
        # 定义所有需要理论依据的教学环节
        required_sections = [
            "知识与技能目标",
            "过程与方法目标",
            "情感态度与价值观目标",
            "核心素养目标",
            "教学重点",
            "教学难点",
            "教学方法",
            "教学手段",
            "创设情境",
            "提出问题",
            "激发兴趣",
            "自主探究",
            "小组合作",
            "教师引导",
            "典型例题",
            "解题思路",
            "易错点辨析",
            "基础训练",
            "综合应用",
            "分层作业",
            "知识梳理",
            "方法提炼",
            "反思评价",
            "基础作业",
            "拓展作业",
            "板书设计",
            "预期效果",
            "可能的问题",
            "改进方向"
        ]
        
        # 提取所有理论引用
        pattern = r"📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
        references = re.findall(pattern, lesson_plan)
        
        print(f"🔍 检测到 {len(references)} 个理论引用")
        
        # 检查引用的有效性和多样性
        valid_references = []
        invalid_references = []
        used_theories = set()
        
        for card_key, theory_name in references:
            if card_key in self.theory_cards_index:
                valid_references.append((card_key, theory_name))
                used_theories.add(card_key)
            else:
                invalid_references.append((card_key, theory_name))
        
        # 检查理论多样性
        if len(used_theories) < 3:
            print(f"⚠️ 理论引用多样性不足，仅使用了 {len(used_theories)} 个不同理论")
        else:
            print(f"✅ 理论引用多样性良好，使用了 {len(used_theories)} 个不同理论")
        
        # 检查无效引用
        if invalid_references:
            print(f"⚠️ 发现 {len(invalid_references)} 个无效理论引用")
            # 修正无效引用
            for card_key, theory_name in invalid_references:
                # 尝试找到最接近的有效理论卡片
                valid_card = None
                for key in self.theory_cards_index:
                    if theory_name in self.theory_cards_index[key]["name"]:
                        valid_card = key
                        break
                
                if valid_card:
                    # 替换为有效引用
                    old_ref = f"[{card_key}：{theory_name}]"
                    card_name = self.theory_cards_index[valid_card]["name"]
                    new_ref = f"[{valid_card}：{card_name}]"
                    lesson_plan = lesson_plan.replace(old_ref, new_ref)
                    print(f"✅ 修正无效引用: {old_ref} → {new_ref}")
                else:
                    # 如果找不到匹配的理论，使用第一个理论卡片作为替代
                    first_card = list(self.theory_cards_index.keys())[0]
                    old_ref = f"[{card_key}：{theory_name}]"
                    first_card_name = self.theory_cards_index[first_card]["name"]
                    new_ref = f"[{first_card}：{first_card_name}]"
                    lesson_plan = lesson_plan.replace(old_ref, new_ref)
                    print(f"⚠️ 替换无效引用为默认理论: {old_ref} → {new_ref}")
        else:
            print("✅ 所有理论引用均有效")
        
        # 检查每个环节是否都有理论引用
        missing_sections = []
        for section in required_sections:
            if re.search(rf"###.*?{re.escape(section)}.*?📌 理论依据", lesson_plan, re.DOTALL) is None:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ 发现 {len(missing_sections)} 个环节缺少理论依据: {', '.join(missing_sections)}")
            # 为缺失的环节添加理论依据
            for section in missing_sections:
                # 根据教学方法和内容类型调整理论推荐
                recommended_theories = self._get_dynamic_recommended_theories(section, teaching_method, content_type)
                
                # 选择一个合适的理论
                selected_theory = None
                for theory_key in recommended_theories:
                    if theory_key in self.theory_cards_index:
                        selected_theory = theory_key
                        break
                
                if selected_theory:
                    theory_info = self.theory_cards_index[selected_theory]
                    theory_name = theory_info["name"]
                    core_view = theory_info["core_view"]
                    teaching_inspiration = theory_info.get("teaching_inspiration", "")
                    teaching_inspiration_elements = theory_info.get("teaching_inspiration_elements", [])
                    
                    # 生成理论依据（使用简洁的分点格式，无边框）
                    if teaching_inspiration_elements:
                        inspiration_elements_str = "、".join(teaching_inspiration_elements[:3])  # 限制最多3个要点
                        
                        # 处理应用场景
                        application_text = f"设计体现了教学启发中的：{inspiration_elements_str}"
                        
                        theory_reference = f"""**📌 理论依据**
- **理论卡片**：{selected_theory} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：{application_text}"""
                    else:
                        # 处理应用场景
                        application_text = f"指导{section}环节的教学设计，体现了{theory_name}的应用价值"
                        
                        theory_reference = f"""**📌 理论依据**
- **理论卡片**：{selected_theory} - {theory_name}
- **核心观点**：{core_view}
- **应用场景**：{application_text}"""
                    
                    # 清理多余的空行
                    theory_reference = theory_reference.replace('\n\n', '\n')
                    
                    # 找到环节位置并插入理论依据
                    section_pattern = rf"(###.*?{re.escape(section)}.*?)(###|$)"
                    match = re.search(section_pattern, lesson_plan, re.DOTALL)
                    if match:
                        insert_position = match.end(1)
                        # 检查该位置是否已经有理论依据，避免重复添加
                        if "📌 理论依据" not in lesson_plan[match.start(1):insert_position]:
                            lesson_plan = lesson_plan[:insert_position] + f"\n\n{theory_reference}" + lesson_plan[insert_position:]
                            print(f"✅ 为 {section} 环节添加理论依据: {selected_theory}：{theory_name}")
        else:
            print("✅ 所有环节都有理论依据")
        
        # 检查理论选择是否与教学方法匹配
        lesson_plan = self._validate_theory_method_match(lesson_plan, teaching_method)
        
        # 检查理论引用的一致性
        import re
        required_sections = [
            "知识与技能目标", "过程与方法目标", "情感态度与价值观目标",
            "核心素养目标", "教学重点", "教学难点", "教学方法", "教学手段",
            "创设情境", "提出问题", "激发兴趣", "自主探究", "小组合作",
            "教师引导", "典型例题", "解题思路", "易错点辨析", "基础训练",
            "综合应用", "分层作业", "知识梳理", "方法提炼", "反思评价",
            "基础作业", "拓展作业", "板书设计", "预期效果", "可能的问题", "改进方向"
        ]
        
        # 构建环节-理论映射
        section_theory_map = {}
        for section in required_sections:
            section_pattern = rf"###.*?{re.escape(section)}.*?📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
            match = re.search(section_pattern, lesson_plan, re.DOTALL)
            if match:
                section_theory_map[section] = match.group(1)
        
        # 检查一致性
        inconsistent_sections = []
        for section, theory_key in section_theory_map.items():
            recommended_theories = self._get_recommended_theories(section, teaching_method, content_type)
            if recommended_theories and theory_key not in recommended_theories:
                inconsistent_sections.append((section, theory_key, recommended_theories[0]))
        
        # 修正不一致的理论引用
        if inconsistent_sections:
            print(f"⚠️ 发现 {len(inconsistent_sections)} 个理论引用不一致的环节")
            for section, old_theory_key, new_theory_key in inconsistent_sections:
                old_theory_name = self.theory_cards_index.get(old_theory_key, {}).get("name", "未知理论")
                new_theory_name = self.theory_cards_index.get(new_theory_key, {}).get("name", "未知理论")
                
                old_ref_pattern = rf"(###.*?{re.escape(section)}.*?)📌 理论依据：\[{old_theory_key}：{re.escape(old_theory_name)}\]"
                new_ref = f"📌 理论依据：[{new_theory_key}：{new_theory_name}]"
                
                lesson_plan = re.sub(old_ref_pattern, rf"\1{new_ref}", lesson_plan, flags=re.DOTALL)
                print(f"✅ 修正 {section} 环节的理论引用: {old_theory_key}：{old_theory_name} → {new_theory_key}：{new_theory_name}")
        else:
            print("✅ 所有理论引用均一致")
        
        # 更新理论依据使用总结
        lesson_plan = self._update_theory_summary(lesson_plan, valid_references)
        
        return lesson_plan
    
    def _get_recommended_theories(self, section: str, teaching_method: str, content_type: str = "概念教学") -> List[str]:
        """
        根据教学方法、环节类型和内容类型推荐合适的理论
        
        Args:
            section: 教学环节
            teaching_method: 教学方法
            content_type: 教学内容类型
        
        Returns:
            推荐的理论卡片列表
        """
        # 基础理论推荐
        base_recommendations = {
            "知识与技能目标": ["理论卡片1", "理论卡片4", "理论卡片12"],
            "过程与方法目标": ["理论卡片7", "理论卡片19", "理论卡片2"],
            "情感态度与价值观目标": ["理论卡片5", "理论卡片3", "理论卡片11"],
            "核心素养目标": ["理论卡片1", "理论卡片7", "理论卡片12"],
            "教学重点": ["理论卡片4", "理论卡片12", "理论卡片1"],
            "教学难点": ["理论卡片2", "理论卡片4", "理论卡片7"],
            "教学方法": ["理论卡片6", "理论卡片7", "理论卡片1"],
            "教学手段": ["理论卡片4", "理论卡片12", "理论卡片1"],
            "创设情境": ["理论卡片10", "理论卡片5", "理论卡片1"],
            "提出问题": ["理论卡片7", "理论卡片2", "理论卡片1"],
            "激发兴趣": ["理论卡片5", "理论卡片10", "理论卡片3"],
            "自主探究": ["理论卡片1", "理论卡片7", "理论卡片19"],
            "小组合作": ["理论卡片6", "理论卡片1", "理论卡片3"],
            "教师引导": ["理论卡片2", "理论卡片1", "理论卡片7"],
            "典型例题": ["理论卡片4", "理论卡片12", "理论卡片1"],
            "解题思路": ["理论卡片12", "理论卡片4", "理论卡片7"],
            "易错点辨析": ["理论卡片4", "理论卡片12", "理论卡片1"],
            "基础训练": ["理论卡片11", "理论卡片8", "理论卡片4"],
            "综合应用": ["理论卡片10", "理论卡片1", "理论卡片7"],
            "分层作业": ["理论卡片3", "理论卡片2", "理论卡片11"],
            "知识梳理": ["理论卡片12", "理论卡片9", "理论卡片1"],
            "方法提炼": ["理论卡片12", "理论卡片9", "理论卡片19"],
            "反思评价": ["理论卡片9", "理论卡片8", "理论卡片1"],
            "基础作业": ["理论卡片11", "理论卡片8", "理论卡片4"],
            "拓展作业": ["理论卡片10", "理论卡片3", "理论卡片7"],
            "板书设计": ["理论卡片4", "理论卡片12", "理论卡片1"],
            "预期效果": ["理论卡片5", "理论卡片1", "理论卡片12"],
            "可能的问题": ["理论卡片2", "理论卡片4", "理论卡片8"],
            "改进方向": ["理论卡片9", "理论卡片8", "理论卡片1"]
        }
        
        # 根据教学方法调整推荐
        method_adjustments = {
            "讲授式": {
                "知识与技能目标": ["理论卡片11", "理论卡片4", "理论卡片12"],  # 行为主义更适合讲授式
                "过程与方法目标": ["理论卡片4", "理论卡片12", "理论卡片2"],  # 认知负荷理论适合知识讲解
                "教学方法": ["理论卡片11", "理论卡片4", "理论卡片1"],  # 行为主义适合讲授式
                "教师引导": ["理论卡片11", "理论卡片2", "理论卡片4"],  # 行为主义强调教师主导
                "典型例题": ["理论卡片4", "理论卡片11", "理论卡片12"],  # 认知负荷理论适合例题讲解
                "基础训练": ["理论卡片11", "理论卡片4", "理论卡片8"]  # 行为主义适合技能训练
            },
            "探究式": {
                "知识与技能目标": ["理论卡片1", "理论卡片7", "理论卡片19"],  # 建构主义适合探究式
                "过程与方法目标": ["理论卡片7", "理论卡片19", "理论卡片1"],  # 探究式学习理论
                "教学方法": ["理论卡片7", "理论卡片1", "理论卡片19"],  # 探究式学习理论
                "自主探究": ["理论卡片7", "理论卡片1", "理论卡片19"],  # 探究式学习理论
                "小组合作": ["理论卡片6", "理论卡片1", "理论卡片7"],  # 合作学习适合探究式
                "提出问题": ["理论卡片7", "理论卡片1", "理论卡片19"]  # 探究式强调问题导向
            },
            "合作学习": {
                "知识与技能目标": ["理论卡片6", "理论卡片1", "理论卡片3"],  # 合作学习理论
                "过程与方法目标": ["理论卡片6", "理论卡片1", "理论卡片7"],  # 合作学习理论
                "教学方法": ["理论卡片6", "理论卡片1", "理论卡片3"],  # 合作学习理论
                "小组合作": ["理论卡片6", "理论卡片1", "理论卡片3"],  # 合作学习理论
                "自主探究": ["理论卡片6", "理论卡片1", "理论卡片7"]  # 合作学习中的探究
            }
        }
        
        # 根据内容类型调整推荐
        content_adjustments = {
            "概念教学": {
                "知识与技能目标": ["理论卡片1", "理论卡片19", "理论卡片12"],  # 建构主义和再创造理论适合概念教学
                "过程与方法目标": ["理论卡片7", "理论卡片19", "理论卡片1"],  # 探究式适合概念形成
                "自主探究": ["理论卡片1", "理论卡片19", "理论卡片7"]  # 自主探究适合概念建构
            },
            "技能训练": {
                "知识与技能目标": ["理论卡片11", "理论卡片4", "理论卡片8"],  # 行为主义适合技能训练
                "基础训练": ["理论卡片11", "理论卡片8", "理论卡片4"],  # 行为主义适合基础训练
                "典型例题": ["理论卡片4", "理论卡片11", "理论卡片12"]  # 认知负荷理论适合例题讲解
            },
            "问题解决": {
                "知识与技能目标": ["理论卡片17", "理论卡片1", "理论卡片19"],  # 波利亚解题理论适合问题解决
                "过程与方法目标": ["理论卡片17", "理论卡片7", "理论卡片1"],  # 探究式适合问题解决
                "解题思路": ["理论卡片17", "理论卡片12", "理论卡片4"]  # 波利亚理论适合解题思路
            },
            "复习总结": {
                "知识与技能目标": ["理论卡片9", "理论卡片12", "理论卡片4"],  # 元认知理论适合复习
                "知识梳理": ["理论卡片9", "理论卡片12", "理论卡片1"],  # 元认知理论适合知识梳理
                "方法提炼": ["理论卡片9", "理论卡片12", "理论卡片19"]  # 元认知理论适合方法提炼
            },
            "项目学习": {
                "知识与技能目标": ["理论卡片6", "理论卡片1", "理论卡片10"],  # 合作学习适合项目学习
                "过程与方法目标": ["理论卡片6", "理论卡片7", "理论卡片10"],  # 探究式适合项目学习
                "小组合作": ["理论卡片6", "理论卡片1", "理论卡片10"]  # 合作学习适合项目学习
            }
        }
        
        # 获取调整后的推荐
        # 首先检查教学方法调整
        if teaching_method in method_adjustments and section in method_adjustments[teaching_method]:
            return method_adjustments[teaching_method][section]
        # 然后检查内容类型调整
        elif content_type in content_adjustments and section in content_adjustments[content_type]:
            return content_adjustments[content_type][section]
        # 最后使用基础推荐
        else:
            return base_recommendations.get(section, ["理论卡片1"])
    
    def _get_dynamic_recommended_theories(self, section: str, teaching_method: str, content_type: str = "概念教学", used_theories: List[str] = None) -> List[str]:
        """
        根据教学环节、教学方法和内容类型动态推荐理论
        
        Args:
            section: 教学环节
            teaching_method: 教学方法
            content_type: 内容类型
            used_theories: 已使用的理论列表，用于增加理论多样性
        
        Returns:
            推荐的理论卡片列表
        """
        recommended_theories = []
        
        # 遍历所有理论卡片，根据匹配度排序
        theory_scores = {}
        
        for card_key, card_info in self.theory_cards_index.items():
            # 如果该理论已经被使用，降低其优先级
            if used_theories and card_key in used_theories:
                continue
            
            score = 0
            
            # 检查教学环节匹配
            applicable_links = card_info.get('applicable_links', '')
            if section in applicable_links:
                score += 4
            elif '所有环节' in applicable_links:
                score += 2
            elif any(keyword in section for keyword in ['导入', '讲解', '练习', '总结', '作业', '探究', '合作', '自主']):
                score += 1
            
            # 检查教学方法匹配
            applicable_methods = card_info.get('applicable_methods', '')
            if self._is_theory_suitable_for_method(card_info, teaching_method):
                score += 5  # 提高教学方法匹配权重
            elif '所有教学方法' in applicable_methods:
                score += 2
            
            # 检查内容类型匹配
            applicable_content = card_info.get('applicable_content', '')
            if content_type in applicable_content:
                score += 3
            elif '所有内容类型' in applicable_content:
                score += 1
            
            # 检查教学启发要素丰富度
            teaching_inspiration_elements = card_info.get('teaching_inspiration_elements', [])
            if len(teaching_inspiration_elements) > 0:
                score += 1
            if len(teaching_inspiration_elements) > 2:
                score += 1
            
            # 根据环节类型动态调整理论偏好（基于教学启发和核心观点的关键词分析）
            section_preferences_keywords = {
                '知识与技能目标': ['技能', '目标', '行为', '掌握', '训练', '强化', '练习'],
                '过程与方法目标': ['过程', '方法', '探究', '建构', '发现', '自主', '合作'],
                '情感态度与价值观目标': ['情感', '态度', '价值观', '动机', '兴趣', '价值', '认同', '态度'],
                '教学重点': ['重点', '核心', '关键', '重要', '主要'],
                '教学难点': ['难点', '困难', '困难', '障碍', '挑战'],
                '教学方法': ['方法', '策略', '方式', '手段', '途径'],
                '创设情境': ['情境', '真实', '生活', '实际', '问题', '情境'],
                '提出问题': ['问题', '提问', '启发', '引导', '探究'],
                '激发兴趣': ['兴趣', '动机', '激发', '吸引', '好奇', '兴趣'],
                '自主探究': ['自主', '探究', '探索', '发现', '研究'],
                '小组合作': ['合作', '小组', '协作', '团队', '同伴'],
                '教师引导': ['引导', '支架', '支持', '帮助', '脚手架'],
                '典型例题': ['例题', '典型', '示范', '例子', '案例'],
                '解题思路': ['思路', '方法', '策略', '技巧', '解题'],
                '易错点辨析': ['易错', '错误', '辨析', '注意', '陷阱'],
                '基础训练': ['基础', '训练', '练习', '巩固', '强化'],
                '综合应用': ['综合', '应用', '实践', '运用', '解决'],
                '分层作业': ['分层', '差异', '个性化', '不同', '层次'],
                '知识梳理': ['梳理', '总结', '归纳', '整理', '系统'],
                '方法提炼': ['方法', '提炼', '总结', '思想', '策略'],
                '反思评价': ['反思', '评价', '评估', '反馈', '元认知']
            }
            
            # 根据环节偏好动态调整分数
            theory_name = card_info.get('name', '')
            core_view = card_info.get('core_view', '')
            teaching_inspiration = card_info.get('teaching_inspiration', '')
            
            # 组合理论的所有文本内容
            combined_theory_text = theory_name + " " + core_view + " " + teaching_inspiration
            
            if section in section_preferences_keywords:
                keywords = section_preferences_keywords[section]
                # 计算匹配的关键词数量
                matched_keywords = sum(1 for keyword in keywords if keyword in combined_theory_text)
                # 根据匹配的关键词数量加分
                if matched_keywords > 0:
                    score += matched_keywords * 0.5
            
            if score > 0:
                theory_scores[card_key] = score
        
        # 按分数排序，返回前5个理论（增加理论多样性）
        sorted_theories = sorted(theory_scores.items(), key=lambda x: x[1], reverse=True)
        recommended_theories = [theory[0] for theory in sorted_theories[:5]]
        
        # 确保至少有一个理论
        if not recommended_theories:
            # 如果没有匹配的理论，返回所有理论卡片中的前5个
            all_theories = list(self.theory_cards_index.keys())
            recommended_theories = all_theories[:5]
        
        return recommended_theories
    
    def _validate_theory_method_match(self, lesson_plan: str, teaching_method: str) -> str:
        """
        验证理论选择是否与教学方法匹配
        
        Args:
            lesson_plan: 教案文本
            teaching_method: 教学方法
        
        Returns:
            验证后的教案文本
        """
        import re
        
        # 扩展关键环节列表，确保更多环节的理论匹配
        key_sections = [
            "知识与技能目标", "过程与方法目标", "情感态度与价值观目标",
            "教学方法", "教师引导", "自主探究", "小组合作",
            "典型例题", "基础训练", "解题思路"
        ]
        
        for section in key_sections:
            # 提取该环节的理论引用
            section_pattern = rf"###.*?{re.escape(section)}.*?📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
            match = re.search(section_pattern, lesson_plan, re.DOTALL)
            
            if match:
                card_key = match.group(1)
                theory_name = match.group(2)
                
                # 检查理论是否适合当前教学方法
                if not self._is_theory_suitable_for_method(card_key, teaching_method):
                    print(f"⚠️ 发现 {section} 环节的理论选择与教学方法不匹配: {theory_name}")
                    # 推荐更适合的理论
                    recommended_theories = self._get_dynamic_recommended_theories(section, teaching_method)
                    for recommended_key in recommended_theories:
                        if recommended_key in self.theory_cards_index:
                            recommended_info = self.theory_cards_index[recommended_key]
                            recommended_name = recommended_info["name"]
                            core_view = recommended_info["core_view"]
                            
                            # 替换理论引用
                            old_ref = f"[{card_key}：{theory_name}]"
                            new_ref = f"[{recommended_key}：{recommended_name}]"
                            lesson_plan = lesson_plan.replace(old_ref, new_ref)
                            
                            # 更新理论依据内容
                            old_content_pattern = rf"\*\*📌 理论依据：\[{card_key}：{re.escape(theory_name)}\] - .*? - 应用场景：.*?\*\*"
                            new_content = f"**📌 理论依据：[{recommended_key}：{recommended_name}] - {core_view} - 应用场景：指导{section}环节的教学设计，体现了{recommended_name}的应用价值**"
                            lesson_plan = re.sub(old_content_pattern, new_content, lesson_plan, flags=re.DOTALL)
                            
                            print(f"✅ 替换为更适合的理论: {recommended_key}：{recommended_name}")
                            break
        
        return lesson_plan
    
    def _monitor_theory_frequency(self, lesson_plan: str) -> Dict[str, int]:
        """
        监控教案中理论的使用频率
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            理论使用频率字典，格式为：{"理论卡片1": 3, "理论卡片2": 2, ...}
        """
        import re
        frequency = {}
        
        # 匹配理论卡片引用的正则表达式
        pattern = r"理论卡片(\d+)"
        matches = re.findall(pattern, lesson_plan)
        
        for card_number in matches:
            card_key = f"理论卡片{card_number}"
            if card_key in frequency:
                frequency[card_key] += 1
            else:
                frequency[card_key] = 1
        
        return frequency
    
    def _check_theory_diversity(self, lesson_plan: str) -> str:
        """
        检查教案中的理论多样性
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            检查后的教案内容
        """
        # 监控理论使用频率
        frequency = self._monitor_theory_frequency(lesson_plan)
        
        # 计算总引用次数
        total_references = sum(frequency.values())
        if total_references == 0:
            return lesson_plan
        
        # 检查是否有理论使用过度（超过30%）
        overused_theories = []
        for theory, count in frequency.items():
            if count / total_references > 0.3:
                overused_theories.append(theory)
        
        # 如果有过度使用的理论，进行替换建议
        if overused_theories:
            print(f"⚠️  检测到过度使用的理论: {overused_theories}")
            # 这里可以添加替换逻辑，暂时只打印警告
        
        return lesson_plan
    
    def _check_theory_consistency(self, lesson_plan: str, teaching_method: str, content_type: str) -> str:
        """
        检查理论引用的一致性
        
        Args:
            lesson_plan: 教案内容
            teaching_method: 教学方法
            content_type: 教学内容类型
        
        Returns:
            检查后的教案内容
        """
        import re
        
        # 定义所有需要理论依据的教学环节
        required_sections = [
            "知识与技能目标", "过程与方法目标", "情感态度与价值观目标",
            "核心素养目标", "教学重点", "教学难点", "教学方法", "教学手段",
            "创设情境", "提出问题", "激发兴趣", "自主探究", "小组合作",
            "教师引导", "典型例题", "解题思路", "易错点辨析", "基础训练",
            "综合应用", "分层作业", "知识梳理", "方法提炼", "反思评价",
            "基础作业", "拓展作业", "板书设计", "预期效果", "可能的问题", "改进方向"
        ]
        
        # 构建环节-理论映射
        section_theory_map = {}
        for section in required_sections:
            section_pattern = rf"###.*?{re.escape(section)}.*?📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
            match = re.search(section_pattern, lesson_plan, re.DOTALL)
            if match:
                section_theory_map[section] = match.group(1)
        
        # 检查一致性
        inconsistent_sections = []
        for section, theory_key in section_theory_map.items():
            recommended_theories = self._get_recommended_theories(section, teaching_method, content_type)
            if recommended_theories and theory_key not in recommended_theories:
                inconsistent_sections.append((section, theory_key, recommended_theories[0]))
        
        # 修正不一致的理论引用
        if inconsistent_sections:
            print(f"⚠️ 发现 {len(inconsistent_sections)} 个理论引用不一致的环节")
            for section, old_theory_key, new_theory_key in inconsistent_sections:
                old_theory_name = self.theory_cards_index.get(old_theory_key, {}).get("name", "未知理论")
                new_theory_name = self.theory_cards_index.get(new_theory_key, {}).get("name", "未知理论")
                
                old_ref_pattern = rf"(###.*?{re.escape(section)}.*?)📌 理论依据：\[{old_theory_key}：{re.escape(old_theory_name)}\]"
                new_ref = f"📌 理论依据：[{new_theory_key}：{new_theory_name}]"
                
                lesson_plan = re.sub(old_ref_pattern, rf"\1{new_ref}", lesson_plan, flags=re.DOTALL)
                print(f"✅ 修正 {section} 环节的理论引用: {old_theory_key}：{old_theory_name} → {new_theory_key}：{new_theory_name}")
        else:
            print("✅ 所有理论引用均一致")
        
        return lesson_plan
    
    def _analyze_student_level(self, user_input: str) -> str:
        """
        分析用户输入中的学生水平
        
        Args:
            user_input: 用户需求
        
        Returns:
            学生水平
        """
        # 定义学生水平关键词
        student_levels = {
            "小学": ["小学", "低年级", "中年级", "高年级", "小学生"],
            "初中": ["初中", "初一", "初二", "初三", "初中生"],
            "高中": ["高中", "高一", "高二", "高三", "高中生"],
            "大学": ["大学", "本科生", "研究生", "大学生"]
        }
        
        # 匹配学生水平
        for level, keywords in student_levels.items():
            for keyword in keywords:
                if keyword in user_input:
                    return level
        
        return "初中"  # 默认值
    
    def _analyze_class_type(self, user_input: str) -> str:
        """
        分析用户输入中的课型
        
        Args:
            user_input: 用户需求
        
        Returns:
            课型
        """
        # 定义课型关键词
        class_types = {
            "新授课": ["新授", "新课", "新内容", "新知识点"],
            "复习课": ["复习", "回顾", "总结", "梳理"],
            "练习课": ["练习", "训练", "巩固", "应用"],
            "实验课": ["实验", "实践", "操作", "探究"],
            "讲评课": ["讲评", "点评", "分析", "讲解"]
        }
        
        # 匹配课型
        for class_type, keywords in class_types.items():
            for keyword in keywords:
                if keyword in user_input:
                    return class_type
        
        return "新授课"  # 默认值
    
    def _analyze_special_requirements(self, user_input: str) -> List[str]:
        """
        分析用户输入中的特殊需求
        
        Args:
            user_input: 用户需求
        
        Returns:
            特殊需求列表
        """
        special_requirements = []
        
        # 定义特殊需求关键词
        requirements = {
            "核心素养": ["核心素养", "素养目标", "素养培养"],
            "分层教学": ["分层", "因材施教", "个性化"],
            "多媒体教学": ["多媒体", "课件", "视频", "动画"],
            "实验教学": ["实验", "实践", "操作"],
            "小组合作": ["小组", "合作", "讨论", "协作"]
        }
        
        # 匹配特殊需求
        for requirement, keywords in requirements.items():
            for keyword in keywords:
                if keyword in user_input:
                    special_requirements.append(requirement)
                    break
        
        return special_requirements
    
    def _analyze_theory_preferences(self, user_input: str) -> List[str]:
        """
        分析用户输入中的理论偏好
        
        Args:
            user_input: 用户需求
        
        Returns:
            理论偏好列表
        """
        theory_preferences = []
        
        # 定义理论关键词
        theories = {
            "建构主义": ["建构主义", "建构"],
            "行为主义": ["行为主义", "行为"],
            "认知主义": ["认知主义", "认知"],
            "合作学习": ["合作学习", "合作"],
            "探究学习": ["探究学习", "探究"]
        }
        
        # 匹配理论偏好
        for theory, keywords in theories.items():
            for keyword in keywords:
                if keyword in user_input:
                    theory_preferences.append(theory)
                    break
        
        return theory_preferences
    
    def _format_all_theory_references(self, lesson_plan: str) -> str:
        """
        转换所有理论依据为新的简洁格式，并处理标题格式
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            格式化后的教案内容
        """
        import re
        
        # 1. 处理标题格式，添加正确的一级标题标记（避免重复添加）
        # 只对没有井号的标题添加井号
        lesson_plan = re.sub(r'^\s*(?!#)(《.+》教学设计)', r'# \1', lesson_plan, flags=re.MULTILINE)
        # 也处理可能在中间出现的标题格式（避免重复添加）
        lesson_plan = re.sub(r'\n\s*(?!#)(《.+》教学设计)', r'\n# \1', lesson_plan)
        
        # 2. 匹配旧格式的理论依据（使用更精确的正则表达式，避免误匹配）
        # 使用非贪婪匹配，确保只匹配完整的理论依据块
        pattern = r"\*\*📌 理论依据：\[(理论卡片[^\]]+)\] - (.*?) - 应用场景：(.*?)\*\*"
        matches = re.findall(pattern, lesson_plan, re.DOTALL)
        
        # 保存所有需要替换的内容，避免在遍历过程中修改字符串导致的问题
        replacements = []
        
        for match in matches:
            full_theory_key = match[0]
            core_view = match[1].strip()
            application = match[2].strip()
            
            # 提取理论卡片编号（去掉理论名称）
            theory_key_match = re.match(r"(理论卡片[一二三四五六七八九十百]+)[:：]*(.*)", full_theory_key)
            if theory_key_match:
                theory_key = theory_key_match.group(1)
                theory_name = theory_key_match.group(2)
            else:
                theory_key = full_theory_key
                theory_name = "未知理论"
            
            # 从理论卡片索引中获取完整信息
            if theory_key in self.theory_cards_index:
                theory_info = self.theory_cards_index[theory_key]
                theory_name = theory_info["name"]
                teaching_inspiration = theory_info.get("teaching_inspiration", "")
                teaching_inspiration_elements = theory_info.get("teaching_inspiration_elements", [])
                
                # 清理核心观点和应用场景中的重复内容
                core_view = core_view.replace('**核心观点**', '').strip()
                application = application.replace('**应用场景**', '').strip()
                
                # 生成新的理论依据格式（简洁版，无边框）
                if teaching_inspiration_elements:
                    # 确保教学启发内容不重复
                    teaching_inspiration = teaching_inspiration.replace('**教学启发**', '').strip()
                    new_theory_reference = f"""**📌 理论依据**
- **理论卡片**：{theory_key} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：{application}"""
                else:
                    new_theory_reference = f"""**📌 理论依据**
- **理论卡片**：{theory_key} - {theory_name}
- **核心观点**：{core_view}
- **应用场景**：{application}"""
                
                # 准备替换内容
                old_pattern = f"**📌 理论依据：[{full_theory_key}] - {core_view} - 应用场景：{application}**"
                replacements.append((old_pattern, new_theory_reference))
            else:
                pass
        
        # 执行替换，避免在遍历过程中修改字符串
        for old_pattern, new_theory_reference in replacements:
            # 使用re.escape确保特殊字符被正确处理
            safe_old_pattern = re.escape(old_pattern)
            lesson_plan = re.sub(safe_old_pattern, new_theory_reference, lesson_plan, flags=re.DOTALL)
        
        return lesson_plan
    
    def _enhance_theory_depth(self, card_key: str, section: str, teaching_method: str) -> str:
        """
        动态增强理论引用深度，确保体现理论核心要素（基于理论卡片内容的关键词分析）
        
        Args:
            card_key: 理论卡片键
            section: 教学环节
            teaching_method: 教学方法
        
        Returns:
            增强深度后的理论依据描述
        """
        theory_info = self.theory_cards_index.get(card_key, {})
        theory_name = theory_info.get('name', '未知理论')
        core_view = theory_info.get('core_view', '未知核心观点')
        teaching_inspiration = theory_info.get('teaching_inspiration', '')
        teaching_inspiration_elements = theory_info.get('teaching_inspiration_elements', [])
        
        # 如果有教学启发要素，直接返回核心观点和教学启发
        if teaching_inspiration_elements:
            elements_str = "、".join(teaching_inspiration_elements)
            return f"{core_view} - 教学启发：{teaching_inspiration} - 体现要素：{elements_str}"
        
        # 如果没有教学启发要素，返回核心观点
        return core_view
    
    def _is_theory_suitable_for_method(self, card_key_or_info: str or Dict[str, str], teaching_method: str) -> bool:
        """
        动态检查理论是否适合当前教学方法（基于理论卡片内容的关键词分析）
        
        Args:
            card_key_or_info: 理论卡片键或理论卡片信息
            teaching_method: 教学方法
        
        Returns:
            是否适合
        """
        # 获取理论卡片信息
        if isinstance(card_key_or_info, str):
            card_info = self.theory_cards_index.get(card_key_or_info, {})
        else:
            card_info = card_key_or_info
        
        applicable_methods = card_info.get('applicable_methods', '')
        theory_name = card_info.get('name', '')
        core_view = card_info.get('core_view', '')
        teaching_inspiration = card_info.get('teaching_inspiration', '')
        
        # 组合理论的所有文本内容
        combined_theory_text = theory_name + " " + core_view + " " + teaching_inspiration
        
        # 特殊处理：多元智能理论适合所有教学方法
        if '多元智能' in theory_name:
            return True
        
        if '所有教学方法' in applicable_methods:
            return True
        
        # 检查教学方法是否匹配
        if teaching_method in applicable_methods:
            return True
        
        # 定义教学方法关键词
        method_keywords = {
            '讲授式教学': ['讲授', '讲解', '传递', '灌输', '呈现', '示范', '演示', '教师主导', '知识传递'],
            '探究式教学': ['探究', '发现', '探索', '研究', '实验', '调查', '自主', '建构', '学生自主'],
            '合作学习': ['合作', '协作', '小组', '团队', '同伴', '互动', '交流', '协作'],
            '自主学习': ['自主', '独立', '自我', '元认知', '监控', '反思', '自我调节'],
            '翻转课堂': ['翻转', '课前', '课后', '预习', '复习', '自主学习'],
            '项目式学习': ['项目', '实践', '应用', '综合', '真实情境', '实际问题'],
            '混合式教学': ['混合', '多种', '多元', '综合', '多样化']
        }
        
        # 动态检查教学方法匹配（基于关键词分析）
        for method_key, keywords in method_keywords.items():
            if method_key in teaching_method:
                # 检查理论内容中是否包含该教学方法的关键词
                for keyword in keywords:
                    if keyword in combined_theory_text:
                        return True
        
        return False
    
    def _evaluate_theory_quality(self, lesson_plan: str, teaching_method: str, content_type: str) -> str:
        """
        理论引用质量三维评估
        
        Args:
            lesson_plan: 教案文本
            teaching_method: 教学方法
            content_type: 教学内容类型
        
        Returns:
            评估并优化后的教案文本
        """
        import re
        
        print("\n====================================")
        print("🎯 理论引用质量三维评估开始")
        print("====================================")
        
        # 定义所有需要理论依据的教学环节
        required_sections = [
            "知识与技能目标",
            "过程与方法目标",
            "情感态度与价值观目标",
            "核心素养目标",
            "教学重点",
            "教学难点",
            "教学方法",
            "教学手段",
            "创设情境",
            "提出问题",
            "激发兴趣",
            "自主探究",
            "小组合作",
            "教师引导",
            "典型例题",
            "解题思路",
            "易错点辨析",
            "基础训练",
            "综合应用",
            "分层作业",
            "知识梳理",
            "方法提炼",
            "反思评价",
            "基础作业",
            "拓展作业",
            "板书设计",
            "预期效果",
            "可能的问题",
            "改进方向"
        ]
        
        # 1. 完整性评估
        print("\n📊 完整性评估")
        # 检查每个环节是否都有理论依据
        missing_sections = []
        for section in required_sections:
            if re.search(rf"###.*?{re.escape(section)}.*?📌 理论依据", lesson_plan, re.DOTALL) is None:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ 发现 {len(missing_sections)} 个环节缺少理论依据: {', '.join(missing_sections)}")
            # 为缺失的环节添加理论依据
            for section in missing_sections:
                # 根据教学方法和内容类型调整理论推荐
                recommended_theories = self._get_recommended_theories(section, teaching_method, content_type)
                
                # 选择一个合适的理论
                selected_theory = None
                for theory_key in recommended_theories:
                    if theory_key in self.theory_cards_index:
                        selected_theory = theory_key
                        break
                
                if selected_theory:
                    theory_info = self.theory_cards_index[selected_theory]
                    theory_name = theory_info["name"]
                    core_view = theory_info["core_view"]
                    teaching_inspiration = theory_info.get("teaching_inspiration", "")
                    teaching_inspiration_elements = theory_info.get("teaching_inspiration_elements", [])
                    
                    # 生成理论依据（使用简洁的 Markdown 格式）
                    if teaching_inspiration_elements:
                        inspiration_elements_str = "、".join(teaching_inspiration_elements[:3])  # 限制最多3个要点
                        theory_reference = f"""

**📌 理论依据**

**【{selected_theory}：{theory_name}】**

- **核心观点**：{core_view[:100]}...
- **教学启发**：{teaching_inspiration[:80]}...
- **应用场景**：设计体现了教学启发中的：{inspiration_elements_str}"""
                    else:
                        theory_reference = f"""

**📌 理论依据**

**【{selected_theory}：{theory_name}】**

- **核心观点**：{core_view[:150]}...
- **应用场景**：指导{section}环节的教学设计，具体体现了{theory_name}的核心观点"""
                    
                    # 找到环节位置并插入理论依据
                    section_pattern = rf"(###.*?{re.escape(section)}.*?)(###|$)"
                    match = re.search(section_pattern, lesson_plan, re.DOTALL)
                    if match:
                        insert_position = match.end(1)
                        lesson_plan = lesson_plan[:insert_position] + f"\n\n{theory_reference}" + lesson_plan[insert_position:]
                        print(f"✅ 为 {section} 环节添加理论依据: {selected_theory}：{theory_name}")
        else:
            print("✅ 所有环节都有理论依据")
        
        # 2. 准确性评估
        print("\n📊 准确性评估")
        # 提取所有理论引用
        pattern = r"📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
        references = re.findall(pattern, lesson_plan)
        
        # 检查无效引用
        invalid_references = []
        for card_key, theory_name in references:
            if card_key not in self.theory_cards_index:
                invalid_references.append((card_key, theory_name))
        
        if invalid_references:
            print(f"⚠️ 发现 {len(invalid_references)} 个无效理论引用")
            # 修正无效引用
            for card_key, theory_name in invalid_references:
                # 尝试找到最接近的有效理论卡片
                valid_card = None
                for key in self.theory_cards_index:
                    if theory_name in self.theory_cards_index[key]["name"]:
                        valid_card = key
                        break
                
                if valid_card:
                    # 替换为有效引用
                    old_ref = f"[{card_key}：{theory_name}]"
                    card_name = self.theory_cards_index[valid_card]["name"]
                    new_ref = f"[{valid_card}：{card_name}]"
                    lesson_plan = lesson_plan.replace(old_ref, new_ref)
                    print(f"✅ 修正无效引用: {old_ref} → {new_ref}")
                else:
                    # 如果找不到匹配的理论，使用推荐的理论
                    recommended_theories = self._get_recommended_theories("教学方法", teaching_method, content_type)
                    if recommended_theories:
                        valid_card = recommended_theories[0]
                        old_ref = f"[{card_key}：{theory_name}]"
                        card_name = self.theory_cards_index[valid_card]["name"]
                        new_ref = f"[{valid_card}：{card_name}]"
                        lesson_plan = lesson_plan.replace(old_ref, new_ref)
                        print(f"⚠️ 替换无效引用为推荐理论: {old_ref} → {new_ref}")
        else:
            print("✅ 所有理论引用均有效")
        
        # 3. 深度评估
        print("\n📊 深度评估")
        # 检查理论引用深度
        shallow_references = []
        
        # 提取所有理论引用位置
        ref_pattern = r"###.*?(📌 理论依据：\[(理论卡片\d+)：([^\]]+)\].*?)(###|$)"
        ref_matches = re.findall(ref_pattern, lesson_plan, re.DOTALL)
        
        for match in ref_matches:
            ref_content = match[0]
            card_key = match[1]
            theory_name = match[2]
            
            # 检查是否为表层引用（仅提及理论名称，应用场景描述笼统）
            if len(ref_content) < 150 or "具体体现" not in ref_content:
                shallow_references.append((card_key, theory_name))
        
        if shallow_references:
            print(f"⚠️ 发现 {len(shallow_references)} 个表层引用，需要深度优化")
            # 优化深度不足的引用
            for card_key, theory_name in shallow_references:
                if card_key in self.theory_cards_index:
                    theory_info = self.theory_cards_index[card_key]
                    core_view = theory_info["core_view"]
                    teaching_inspiration = theory_info.get("teaching_inspiration", "")
                    
                    # 生成深度结合的理论依据（使用新的分点格式）
                    deep_content = f"""**📌 理论依据**
- **理论卡片**：{card_key} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：通过设计具体的教学活动，如...，充分体现了{theory_name}的核心观点，实现了理论与实践的深度融合"""
                    
                    # 替换表层引用
                    old_pattern = rf"📌 理论依据：\[{card_key}：{re.escape(theory_name)}\].*? - 应用场景：.*?\*\*"
                    lesson_plan = re.sub(old_pattern, deep_content, lesson_plan, flags=re.DOTALL)
                    print(f"✅ 优化理论引用深度: {card_key}：{theory_name}")
        else:
            print("✅ 所有理论引用均为深度结合")
        
        print("\n====================================")
        print("🎯 理论引用质量三维评估完成")
        print("====================================")
        
        return lesson_plan
    
    def _update_theory_summary(self, lesson_plan: str, references: List[tuple]) -> str:
        """
        更新教案中的理论依据使用总结
        
        Args:
            lesson_plan: 教案文本
            references: 有效理论引用列表
        
        Returns:
            更新后的教案文本
        """
        # 提取教案中的各个环节
        sections = [
            "教学目标设计", "教学重难点分析", "教学方法与策略",
            "情境导入", "新知探究", "典例分析", "跟踪训练", "课堂小结", "作业布置",
            "板书设计", "教学反思"
        ]
        
        # 构建理论使用统计
        theory_usage = {}
        for card_key, theory_name in references:
            if card_key not in theory_usage:
                theory_usage[card_key] = {
                    "name": theory_name,
                    "sections": [],
                    "core_view": self.theory_cards_index.get(card_key, {}).get("core_view", "")
                }
        
        # 简单地为每个理论分配一些环节（实际应用中可能需要更复杂的分析）
        for i, (card_key, _) in enumerate(references):
            if card_key in theory_usage:
                section = sections[i % len(sections)]
                if section not in theory_usage[card_key]["sections"]:
                    theory_usage[card_key]["sections"].append(section)
        
        # 生成新的理论依据使用总结
        summary_table = "| 理论依据 | 应用环节 | 理论核心观点 | 具体作用 |\n"
        summary_table += "|---------|---------|-------------|---------|\n"
        
        for card_key, info in theory_usage.items():
            sections_str = ", ".join(info["sections"])
            core_view = info["core_view"]
            # 简单生成具体作用描述
            role = f"指导{sections_str}环节的教学设计，体现了{info['name']}的应用价值"
            
            summary_table += f"| [{card_key}：{info['name']}] | {sections_str} | {core_view} | {role} |\n"
        
        # 替换原有的理论依据使用总结
        import re
        pattern = r"### 📚 本教案使用的理论依据汇总\n\n.*?### 🎯 理论依据使用亮点"
        replacement = f"### 📚 本教案使用的理论依据汇总\n\n{summary_table}\n### 🎯 理论依据使用亮点"
        
        updated_lesson_plan = re.sub(pattern, replacement, lesson_plan, flags=re.DOTALL)
        
        print("✅ 理论依据使用总结已更新")
        return updated_lesson_plan
    
    def generate(
        self, 
        user_input: str, 
        theory_resources: List[Dict[str, Any]],
        lesson_plan_patterns: List[Dict[str, Any]]
    ) -> str:
        """
        生成教案
        
        Args:
            user_input: 用户需求
            theory_resources: 理论资源列表
            lesson_plan_patterns: 优秀教案示例列表
        
        Returns:
            生成的教案文本
        """
        print(f"\n====================================")
        print(f"📝 教案生成开始")
        print(f"📝 用户需求: {user_input}")
        print(f"📚 向量数据库理论资源: {len(theory_resources)}条")
        print(f"📄 向量数据库教案示例: {len(lesson_plan_patterns)}条")
        print(f"📚 本地优秀教案共性文件: {'已加载' if self.lesson_plan_common_characteristics else '未找到'}")
        print(f"📚 本地理论卡片文件: {'已加载' if self.theory_cards else '未找到'}")
        
        try:
            # 分析用户输入中的教学方法
            teaching_method = self._analyze_teaching_method(user_input)
            print(f"🔍 分析教学方法: {teaching_method}")
            
            # 分析用户输入中的教学内容类型
            content_type = self._analyze_content_type(user_input)
            print(f"📝 分析教学内容类型: {content_type}")
            
            # 准备输入数据 - 优先使用本地文件，向量数据库资源作为补充
            theory_text = self._format_theory_resources(theory_resources)
            patterns_text = self._format_lesson_plan_patterns(lesson_plan_patterns)
            
            # 获取模型
            model = self.model_config.get_model("lesson_plan")
            
            # 构建链
            chain = self.prompt_template | model | StrOutputParser()
            
            # 调用模型生成教案
            lesson_plan = chain.invoke({
                "user_input": user_input,
                "theory_resources": theory_text,
                "lesson_plan_patterns": patterns_text,
                "lesson_plan_common_characteristics": self.lesson_plan_common_characteristics,
                "theory_cards": self.theory_cards
            })
            
            print(f"✅ 教案生成成功，长度: {len(lesson_plan)}字符")
            
            # 验证理论引用（考虑教学方法和内容类型）
            validated_lesson_plan = self._validate_theory_references(lesson_plan, teaching_method, content_type)
            
            # 理论引用质量三维评估
            quality_evaluated_plan = self._evaluate_theory_quality(validated_lesson_plan, teaching_method, content_type)
            
            # 检查理论多样性
            diverse_plan = self._check_theory_diversity(quality_evaluated_plan)
            
            # 检查理论引用的一致性
            consistent_plan = self._check_theory_consistency(diverse_plan, teaching_method, content_type)
            
            # 转换所有理论依据为新的边框格式
            formatted_plan = self._format_all_theory_references(consistent_plan)
            
            # 检查教案环节完整性
            complete_plan = self._check_lesson_plan_completeness(formatted_plan)
            
            return complete_plan
            
        except Exception as e:
            print(f"❌ 教案生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
    def _analyze_teaching_method(self, user_input: str) -> str:
        """
        分析用户输入中的教学方法
        
        Args:
            user_input: 用户需求
        
        Returns:
            教学方法类型
        """
        import re
        
        # 定义教学方法关键词
        teaching_methods = {
            "讲授式": ["讲授式", "讲解式", "传统教学", "教师主导", "课堂讲授"],
            "探究式": ["探究式", "自主探究", "发现学习", "问题导向", "项目学习"],
            "合作学习": ["合作学习", "小组合作", "同伴学习", "协作学习"],
            "翻转课堂": ["翻转课堂", "翻转教学"],
            "混合式": ["混合式", "线上线下", "混合教学"]
        }
        
        # 检测教学方法
        for method, keywords in teaching_methods.items():
            for keyword in keywords:
                if re.search(keyword, user_input, re.IGNORECASE):
                    return method
        
        # 默认教学方法
        return "讲授式"
    
    def _analyze_content_type(self, user_input: str) -> str:
        """
        分析用户输入中的教学内容类型
        
        Args:
            user_input: 用户需求
        
        Returns:
            教学内容类型
        """
        import re
        
        # 定义教学内容类型关键词
        content_types = {
            "概念教学": ["概念", "定义", "性质", "定理", "公式推导"],
            "技能训练": ["训练", "练习", "解题", "应用", "计算"],
            "问题解决": ["问题", "解决", "应用", "探究", "案例"],
            "复习总结": ["复习", "总结", "梳理", "回顾", "系统"],
            "项目学习": ["项目", "实践", "综合", "研究", "探究"]
        }
        
        # 检测教学内容类型
        for content_type, keywords in content_types.items():
            for keyword in keywords:
                if re.search(keyword, user_input, re.IGNORECASE):
                    return content_type
        
        # 根据课题名称推断内容类型
        # 常见概念教学课题
        concept_topics = ["函数", "指数函数", "对数函数", "三角函数", "立体几何", "解析几何", "概率", "统计"]
        for topic in concept_topics:
            if topic in user_input:
                return "概念教学"
        
        # 默认内容类型
        return "概念教学"
    
    def _format_theory_resources(self, resources: List[Dict[str, Any]]) -> str:
        """
        格式化理论资源，提供清晰的理论信息
        
        Args:
            resources: 理论资源列表
        
        Returns:
            格式化后的文本
        """
        if not resources:
            return "暂无相关理论资源"
        
        formatted = []
        for i, resource in enumerate(resources, 1):
            title = resource.get("title", f"理论{i}")
            content = resource.get("content", "")
            source = resource.get("source", "")
            
            # 提取核心观点和教学启发
            core_view = self._extract_section(content, "核心观点")
            teaching_inspiration = self._extract_section(content, "教学启发")
            applicable_links = self._extract_section(content, "适用环节")
            application_case = self._extract_section(content, "应用案例")
            
            formatted.append(f"""
【理论卡片{i}】{title}

📌 核心观点：
{core_view if core_view else content}

💡 教学启发：
{teaching_inspiration if teaching_inspiration else "请根据理论核心观点提炼教学启发"}

🎯 适用环节：
{applicable_links if applicable_links else "适用于教学全过程"}

📖 应用案例：
{application_case if application_case else "请结合具体教学内容设计应用场景"}

---
""")
        
        return "\n".join(formatted)
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        从内容中提取特定章节
        
        Args:
            content: 完整内容
            section_name: 章节名称
        
        Returns:
            提取的章节内容
        """
        import re
        pattern = rf"\*\*{re.escape(section_name)}\*\*\s*\n(.*?)(?=\n\*\*|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _format_lesson_plan_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """
        格式化教案示例，突出优秀教案的共性特征
        
        Args:
            patterns: 教案示例列表
        
        Returns:
            格式化后的文本
        """
        if not patterns:
            return "暂无优秀教案示例"
        
        formatted = []
        for i, pattern in enumerate(patterns, 1):
            title = pattern.get("title", f"教案{i}")
            content = pattern.get("content", "")
            
            # 提取关键信息
            formatted.append(f"""
【优秀教案示例{i}】{title}

{content}

---
""")
        
        return "\n".join(formatted)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"""
# ❌ 教案生成失败

抱歉，教案生成过程中出现错误：**{error_msg}**

## 可能的原因：
1. 网络连接问题，无法访问AI模型
2. API密钥配置错误
3. 理论资源或教案示例加载失败

## 建议解决方案：
1. 检查网络连接
2. 确认.env文件中的API密钥配置正确
3. 稍后重试或联系管理员

---
"""
    
    def _check_lesson_plan_completeness(self, lesson_plan: str) -> str:
        """
        检查教案环节完整性，自动补充缺失的必备模块
        
        Args:
            lesson_plan: 教案文本
        
        Returns:
            完整的教案文本
        """
        # 定义必备环节及其默认内容模板
        required_sections = {
            "教学目标设计": """## 一、教学目标设计

### 知识与技能目标
- 理解并掌握本课的核心概念和基本原理
- 能够运用所学知识解决简单的实际问题
- 培养数学思维能力和逻辑推理能力

### 过程与方法目标
- 通过自主探究和小组合作，体验知识的形成过程
- 学会运用数学思想方法分析和解决问题
- 提升数学表达和交流能力

### 情感态度与价值观目标
- 培养学习数学的兴趣和自信心
- 体会数学的实用价值和美学价值
- 培养严谨的科学态度和合作精神

**📌 理论依据**
- **理论卡片**：理论卡片一 - 布鲁姆教育目标分类学
- **核心观点**：教育目标应分为认知、情感和动作技能三个领域
- **教学启发**：在教案设计中，应明确区分知识目标、能力目标和情感目标，确保教学目标的全面性和层次性
- **应用场景**：用于指导教学目标的设定，确保目标覆盖知识、过程、情感三个维度

---

""",
            "教学重难点分析": """## 二、教学重难点分析

### 教学重点
- 本课的核心概念和基本原理
- 知识之间的内在联系和逻辑关系
- 数学思想方法的理解和应用

### 教学难点
- 抽象概念的理解和掌握
- 数学思想方法的灵活运用
- 解决实际问题的能力培养

### 突破策略
- 通过具体实例引入抽象概念
- 采用循序渐进的教学方法
- 加强练习和反馈，及时纠正错误

**📌 理论依据**
- **理论卡片**：理论卡片二 - 最近发展区理论
- **核心观点**：学生的发展存在两种水平：现有发展水平和潜在发展水平，两者之间的差距就是最近发展区
- **教学启发**：教学应着眼于学生的最近发展区，为学生提供适当难度的学习任务，通过教师的引导和同伴的帮助，使学生能够达到潜在发展水平
- **应用场景**：用于确定教学重难点，设计符合学生认知水平的教学内容和活动

---

""",
            "教学方法与策略": """## 三、教学方法与策略

### 教学方法
- **讲授法**：系统讲解核心概念和基本原理
- **探究法**：引导学生自主发现和总结规律
- **合作学习**：通过小组讨论促进思维碰撞

### 教学策略
- **情境创设**：创设贴近学生生活的教学情境
- **问题驱动**：以问题为导向，激发学生思考
- **分层教学**：根据学生差异提供不同层次的学习任务

### 教学手段
- 多媒体课件辅助教学
- 板书演示重点内容
- 实物教具或数学软件辅助

**📌 理论依据**
- **理论卡片**：理论卡片三 - 建构主义学习理论
- **核心观点**：学习是学习者主动建构意义的过程，不是被动接受信息
- **教学启发**：教学应以学生为中心，创设真实的学习情境，提供丰富的学习资源，引导学生主动建构知识
- **应用场景**：用于指导教学方法和策略的选择，强调学生的主动参与和知识建构

---

""",
            "板书设计": """## 五、板书设计

### 板书布局
```
--------------------------------------------------
|                  课题：[课题名称]                |
--------------------------------------------------
|  一、教学目标                                    |
|  1. 知识目标：...                                |
|  2. 能力目标：...                                |
|  3. 情感目标：...                                |
--------------------------------------------------
|  二、核心概念                                    |
|  [核心概念1]：定义、性质、应用                    |
|  [核心概念2]：定义、性质、应用                    |
--------------------------------------------------
|  三、典型例题                                    |
|  例1：[题目内容]                                 |
|      解：[解题过程]                              |
--------------------------------------------------
|  四、重要结论                                    |
|  1. [结论1]                                      |
|  2. [结论2]                                      |
--------------------------------------------------
```

### 设计意图
- 课题醒目，明确本课主题
- 教学目标清晰，指导学习方向
- 核心概念突出，便于记忆理解
- 典型例题详细，展示解题思路
- 重要结论归纳，便于复习巩固

**📌 理论依据**
- **理论卡片**：理论卡片四 - 双重编码理论
- **核心观点**：人类记忆系统包含言语系统和表象系统，两种系统同时加工信息可以提高记忆效果
- **教学启发**：板书设计应结合文字和图形，充分利用双重编码的优势，帮助学生更好地理解和记忆知识
- **应用场景**：用于指导板书设计，通过文字和图形的结合提高教学效果

---

""",
            "教学反思": """## 六、教学反思

### 预期效果
- 学生能够理解并掌握本课的核心概念和基本原理
- 学生能够运用所学知识解决简单的实际问题
- 学生的数学思维能力和逻辑推理能力得到提升
- 学生对数学学习的兴趣和自信心得到增强

### 可能的问题
- 部分学生对抽象概念的理解可能存在困难
- 学生的个体差异可能导致学习进度不一致
- 课堂时间分配可能需要根据实际情况调整

### 改进方向
- 加强对抽象概念的具体化讲解
- 采用分层教学，满足不同层次学生的需求
- 增加课堂互动，提高学生参与度
- 及时收集学生反馈，调整教学策略

**📌 理论依据**
- **理论卡片**：理论卡片五 - 反思性教学理论
- **核心观点**：教师通过反思自己的教学实践，不断改进教学方法，提高教学质量
- **教学启发**：教学反思是教师专业发展的重要途径，应关注教学效果、学生反应和改进方向
- **应用场景**：用于指导教学反思，帮助教师总结经验、发现问题、改进教学

---

"""
        }
        
        # 检查教学过程中的必备子环节
        required_subsections = {
            "作业布置": """### ⏱️ 环节六：作业布置（2分钟）
- **基础作业**（1分钟）：[详细布置基础巩固作业，包含2-3道基础题目，难度适中]
- **拓展作业**（1分钟）：[详细布置拓展延伸作业，包含1道拓展题目，可选做]

**📌 理论依据**
- **理论卡片**：理论卡片六 - 练习曲线理论
- **核心观点**：技能的掌握需要经过大量的练习，练习的次数和时间与技能的熟练度成正比
- **教学启发**：作业设计应遵循由易到难、循序渐进的原则，既要巩固基础知识，又要适当拓展提升
- **应用场景**：用于指导作业布置，确保作业的层次性和有效性

---

"""
        }
        
        # 检查主要环节
        for section_name, section_content in required_sections.items():
            if section_name not in lesson_plan:
                print(f"⚠️ 自动补充缺失环节: {section_name}")
                # 在教案末尾添加缺失环节
                lesson_plan += section_content
        
        # 检查教学过程中的子环节
        for subsection_name, subsection_content in required_subsections.items():
            if subsection_name not in lesson_plan:
                print(f"⚠️ 自动补充缺失子环节: {subsection_name}")
                # 在教案末尾添加缺失子环节
                lesson_plan += subsection_content
        
        return lesson_plan
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建教案生成的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一位资深的高中数学教学设计专家，拥有20年的一线教学经验和深厚的教育理论基础。

## 任务要求

请根据以下信息，生成一个**高质量、理论依据充分、结构清晰、内容详细、格式美观**的高中数学教案。**重要要求：每个教学环节都必须有明确的理论依据，不能有任何环节缺失！教案内容要详细具体，符合实际教学需要，篇幅要足够完整，不能过于简洁！**

**⚠️ 特别注意：请直接生成教案内容，不要添加任何自我介绍或开场白，直接以教案标题开始。**

**⚠️ 理论卡片编号格式要求：必须使用中文数字（如：理论卡片一、理论卡片二、理论卡片十一），不能使用阿拉伯数字（如：理论卡片1、理论卡片2、理论卡片11）！**

**📐 数学公式格式要求：使用上标表示指数和幂，如 y = x² 而不是 y = x^2，使用下标表示变量，如 x₁ 而不是 x_1！**

### 📋 用户需求
{user_input}

---

### 📚 核心参考资源

#### 1. 优秀教案共性特征
{lesson_plan_common_characteristics}

#### 2. 教育理论卡片（理论依据来源仅限于此）
{theory_cards}

#### 3. 向量数据库补充资源
（理论卡片为主，以下仅作补充参考）
{theory_resources}
{lesson_plan_patterns}

---

## 🎯 教案设计要求

### 一、整体结构要求
请严格按照以下结构组织教案，**每个部分、每个小环节都必须清晰标注理论依据（必须来自理论卡片），不能有任何环节缺失**。特别注意：**情感态度与价值观目标必须有完整的理论依据，不能被截断或省略！**

**学情适配要求：**
- 严格根据用户指定的学段（如高一、高二）、班型（如普通班、重点班）、课时（如1课时）来调整内容深度和难度
- 高一普通班1课时：内容要基础，难度适中，避免超纲内容（如含参函数、分段函数的深入讨论），重点放在概念理解和基础应用
- 高一重点班或高二普通班：可以适当增加拓展内容和深度，加入一些变式训练
- 高二重点班或高年级：可以增加综合性问题和拓展应用，提升思维训练
- 确保教学内容与学生认知水平匹配，避免过难或过易
- 根据课时安排合理分配时间，确保每个环节都有充足的时间完成

**内容详细度要求：**
- 每个教学环节都要有具体的教学内容和实施步骤
- 情境导入要有具体的生活情境或实际问题描述
- 探究活动要有详细的学生活动设计
- 典例分析要有具体的例题和解题过程
- 训练题目要有具体的题目内容
- 课堂小结要有完整的知识结构梳理
- 作业布置要有具体的作业内容
- 板书设计要有详细的布局规划
- 教学反思要有深入的分析和改进建议

**篇幅要求：**
- 完整教案长度应在3000-5000字之间
- 每个教学环节都要有足够的内容支撑
- 理论依据要详细展开，不能过于简略

**格式要求：**
- 标题使用《[课题名称]》教学设计格式，使用一级标题标记 (#)
- 减少emoji使用，仅使用必要的图标（如📋、📚、📌）增强可读性
- 理论依据使用简洁的分点格式，避免使用边框
- 教学目标、重难点使用层次化格式和图标突出显示
- 确保格式规范，符合学科教案正式排版要求

```markdown
# 《[课题名称]》教学设计

## 📋 教案信息
- **课题**：[课题名称]
- **对象**：[学生水平]
- **课时**：[课时安排]
- **方式**：[教学方式]

## 一、教学目标设计

### 📚 知识与技能目标
- **概念理解**：[具体描述]
- **方法掌握**：[具体描述]
- **拓展应用**：[具体描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### 🔬 过程与方法目标
- **探究过程**：[具体描述]
- **合作学习**：[具体描述]
- **建模体验**：[具体描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ❤️ 情感态度与价值观目标
- **兴趣激发**：[具体描述]
- **科学精神**：[具体描述]
- **应用意识**：[具体描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

**⚠️ 特别注意：情感态度与价值观目标是教学目标三维中不可或缺的一环，必须有完整的理论依据！请选择涉及情感、动机、态度、价值、兴趣、成就感等维度的理论卡片，确保理论依据与情感目标内容紧密呼应。**

### 🎯 核心素养目标
- **数学抽象**：[具体描述]
- **逻辑推理**：[具体描述]
- **数学运算**：[具体描述]
- **直观想象**：[具体描述]
- **数学建模**：[具体描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

---

## 二、教学重难点分析

### ⭐ 教学重点
- **核心1**：[描述]
- **核心2**：[描述]
- **核心3**：[描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⚠️ 教学难点
- **难点1**：[描述]
- **难点2**：[描述]
- **难点3**：[描述]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### 🎯 突破策略
- **策略1**：[描述]
- **策略2**：[描述]
- **策略3**：[描述]

---

## 三、教学方法与策略

### 🎓 教学方法
[详细列出本课采用的主要教学方法，如探究式教学、合作学习等，说明每种方法的具体应用方式]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### 🛠️ 教学手段
[详细列出教学工具，如GeoGebra、PPT、智慧黑板等，说明如何使用这些工具辅助教学。确保每个工具的描述完整，包括具体的使用方式和效果]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

---

## 四、教学过程设计（45分钟）

### ⏱️ 环节一：情境导入与问题提出（5分钟）
- **创设情境**（2分钟）：小组快速讨论图片中的变化特征（气温图、股票图、身高图）
- **提出问题**（3分钟）：观察 y = x² 图象，引导学生思考图象变化规律

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⏱️ 环节二：新知探究（15分钟）
- **自主探究**（5分钟）：[详细设计学生自主探究活动，包括具体的探究任务、学生操作步骤和预期结果]
- **小组合作**（5分钟）：[详细设计小组讨论和合作学习活动，包括分组方式、讨论问题和合作要求]
- **教师引导**（5分钟）：[详细说明教师的引导方式，包括提问设计、脚手架搭建和适时点拨]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⏱️ 环节三：典例分析（10分钟）
- **典型例题**（5分钟）：[详细设计典型例题，包含题目内容、完整解题过程和思路分析]
- **解题思路**（3分钟）：[详细分析解题思路和方法，说明关键步骤和注意事项]
- **易错点辨析**（2分钟）：[详细指出常见错误和注意事项，结合高一学生核心易错点设计]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⏱️ 环节四：跟踪训练（8分钟）
- **基础训练**（3分钟）：[详细设计基础练习题，包含2-3道基础题目，巩固核心概念]
- **综合应用**（3分钟）：[详细设计综合应用题，包含1-2道综合题目，提升应用能力]
- **反馈讲解**（2分钟）：[详细设计反馈讲解环节，针对学生错误进行纠正和巩固]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⏱️ 环节五：课堂小结（5分钟）
- **知识梳理**（2分钟）：[详细梳理本课的知识结构和要点，使用思维导图或知识框架]
- **方法提炼**（2分钟）：[详细提炼数学思想方法，强调本课的核心数学思想]
- **反思评价**（1分钟）：[详细引导学生进行自我反思和评价，检验学习效果]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### ⏱️ 环节六：作业布置（2分钟）
- **基础作业**（1分钟）：[详细布置基础巩固作业，包含2-3道基础题目，难度适中]
- **拓展作业**（1分钟）：[详细布置拓展延伸作业，包含1道拓展题目，可选做]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

---

## 五、板书设计

[详细设计结构化的板书，要有具体的布局规划、内容安排和设计意图。板书应包含：课题、教学目标、核心概念、典型例题、重要结论等]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

---

## 六、教学反思

### 预期效果
[详细预期本课的教学效果，要有具体的目标达成预期和效果评估方式]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### 可能的问题
[详细预测可能出现的问题和应对策略，要有具体的问题类型和解决措施]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

### 改进方向
[详细提出教学改进的方向，要有具体的改进措施和预期效果]

**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]

---

### 二、理论依据引用要求

#### 1. 强制要求
- **完整性**：每个教学环节（包括所有小环节）都必须有理论依据，不能有任何缺失
- **唯一性**：理论依据只能来自提供的理论卡片资源
- **准确性**：理论卡片编号和名称必须准确无误，必须使用中文数字
- **深度**：详细说明设计如何体现理论的具体要素，避免贴标签式引用
- **格式规范**：理论依据必须采用分点格式，避免使用边框

#### 2. 引用格式
在每个教学环节的设计说明后，必须使用以下格式标注理论依据：

```markdown
**📌 理论依据**
- **理论卡片**：[理论卡片编号] - [理论名称]
- **核心观点**：[理论核心观点]
- **教学启发**：[教学启发内容]
- **应用场景**：[具体应用场景说明]
```

**⚠️ 重要要求：理论卡片编号必须使用中文数字（如：理论卡片一、理论卡片二、理论卡片十一），不能使用阿拉伯数字（如：理论卡片1、理论卡片2、理论卡片11）！**

#### 3. 理论要素细化示例
- **建构主义**：可细分为"情境真实性"、"脚手架引导"、"协作互动"等要素
- **最近发展区**：可细分为"现有水平"、"潜在发展水平"、"脚手架搭建"等要素
- **多元智能**：可细分为"语言智能"、"逻辑-数学智能"、"空间智能"等要素
- **生活教育理论**：可细分为"生活即教育"、"社会即学校"、"教学做合一"等要素

#### 4. 环节-理论匹配建议
- **情境导入**：适合使用"情境学习理论"、"ARCS动机理论"、"生活教育理论"等
- **新知探究**：适合使用"建构主义"、"最近发展区"、"探究式学习理论"等
- **小组合作**：适合使用"合作学习理论"、"社会建构主义"等
- **典例分析**：适合使用"认知负荷理论"、"范例教学理论"等
- **跟踪训练**：适合使用"反馈理论"、"行为主义学习理论"等
- **课堂小结**：适合使用"元认知理论"、"反思性学习理论"等
- **情感态度**：适合使用"学习动机理论"、"情感教育理论"、"价值观教育理论"等

### 三、优秀教案共性特征要求

请在教案设计中充分体现优秀教案共性整合文件中的要求，包括但不限于：

#### 1. 教学目标设计
- 目标明确，紧扣核心内容
- 核心素养导向突出（数学抽象、逻辑推理、数学运算、直观想象、数学建模）
- 目标分层清晰，涵盖多个维度，体现层次性

#### 2. 教学重难点把握
- 突出"关系"与"应用"，重点围绕核心概念、性质及其在实际问题中的应用
- 难点聚焦抽象思维与思想方法

#### 3. 教学结构设计
- 流程完整，环节清晰："情境导入/预习导入→新知探究→典例分析→跟踪训练→课堂小结→作业布置"
- 符合认知发展规律：体现"感知→理解→应用→反思"的学习路径
- 整体衔接性强：注重与前后知识的衔接

#### 4. 教学内容与方法
- 情境导入贴近生活：采用实际情境引入课题
- 强调探究式学习：设置问题链、小组讨论、自主归纳
- 典例与训练配套精准：实现"讲---练---评"一体化
- 分层递进，覆盖全面：满足不同层次学生需求
- 思想方法显化：强调数学思想方法的渗透（数形结合、分类讨论、化归转化、从特殊到一般、函数与方程、数学建模）

#### 5. 教学工具与资源
- 多媒体与信息技术辅助教学：GeoGebra、几何画板、PPT、智慧黑板
- 板书与练习系统清晰：结构化板书，典例解析、跟踪训练、达标检测、分层作业

#### 6. 教学评价与反馈
- 当堂检测与反馈及时
- 作业设计呼应课堂：基础巩固+拓展延伸
- 教学反思常态化

#### 7. 学生主体与互动
- 以学生为中心："学生自主探究+小组合作+教师引导"
- 语言启发性强：注重启发性提问
- 关注认知难点与易错点：专项辨析与强化

### 四、用户需求融入要求

请确保教案设计充分响应用户的具体需求：
- 仔细分析用户需求中的关键词和要求
- 将用户需求融入到教案的各个环节设计中
- 在适当的地方说明如何满足用户需求

---

## 📌 重要提醒

1. **理论依据必须来自理论卡片**：请确保所有理论依据引用都来自提供的理论卡片资源
2. **理论依据是教案的灵魂**：请在每个环节都明确标注理论依据，说明理论如何指导教学设计
3. **理论与实践结合**：理论依据不是装饰，而是真正指导教学设计的依据
4. **突出"依据理论，有理论可依"的特色**：这是本教案的核心亮点
5. **结构清晰，排版美观**：使用Markdown格式，确保教案易读、美观
6. **内容详实，可操作性强**：教案要具体、详细，具有实际可操作性
7. **不要生成新文件**：所有内容都直接输出，不需要创建额外文件

现在，请根据以上要求，生成一个高质量、理论依据充分、结构清晰的高中数学教案。
""")


# 向后兼容的函数接口
def lesson_plan_generation_node(state) -> Dict[str, Any]:
    """
    教案生成节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含教案的更新状态
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 提取检索到的资源
    lesson_plan_patterns = []
    
    if isinstance(state, dict):
        retrieved_resources = state.get('retrieved_resources', {})
        lesson_plan_patterns = retrieved_resources.get('lesson_plan_patterns', [])
    
    # 从向量数据库获取理论资源
    theory_resources = []
    try:
        from .resource_retriever import ResourceRetriever
        retriever = ResourceRetriever()
        theory_resources = retriever.get_theory_resources()
        print(f"📚 从向量数据库获取理论资源: {len(theory_resources)}条")
    except Exception as e:
        print(f"⚠️  获取理论资源失败: {str(e)}")
    
    # 生成教案
    generator = LessonPlanGenerator()
    lesson_plan = generator.generate(user_input, theory_resources, lesson_plan_patterns)
    
    return {
        "lesson_plan": lesson_plan,
        "current_step": "lesson_plan_generation",
        "error": None
    }
