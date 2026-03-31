from .._shared import *


class _LoadLessonPlanCommonCharacteristicsMixin:
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
