from .._shared import *


class _GenerateApplicationCaseMixin:
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
