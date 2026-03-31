"""
统一教案系统服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.load_latest_lesson_plan import _LoadLatestLessonPlanMixin
from .methods.save_latest_lesson_plan import _SaveLatestLessonPlanMixin
from .methods.process_lesson_plan_request import _ProcessLessonPlanRequestMixin
from .methods.extract_lesson_plan_info import _ExtractLessonPlanInfoMixin
from .methods.backup_extract_info import _BackupExtractInfoMixin
from .methods.assess_info_completion import _AssessInfoCompletionMixin
from .methods.guide_for_more_info import _GuideForMoreInfoMixin
from .methods.generate_summary import _GenerateSummaryMixin
from .methods.generate_complete_lesson_plan import _GenerateCompleteLessonPlanMixin
from .methods.build_enhanced_input import _BuildEnhancedInputMixin
from .methods.revise_lesson_plan import _ReviseLessonPlanMixin
from .methods.export_lesson_plan import _ExportLessonPlanMixin
from .methods.get_markdown_content import _GetMarkdownContentMixin
from .methods.get_html_content import _GetHtmlContentMixin
from .methods.get_html_css import _GetHtmlCssMixin
from .methods.clean_expired_sessions import _CleanExpiredSessionsMixin
from .methods.update_session_activity import _UpdateSessionActivityMixin
from .methods.get_session_state import _GetSessionStateMixin

class UnifiedLessonPlanSystem(_InitMixin, _LoadLatestLessonPlanMixin, _SaveLatestLessonPlanMixin, _ProcessLessonPlanRequestMixin, _ExtractLessonPlanInfoMixin, _BackupExtractInfoMixin, _AssessInfoCompletionMixin, _GuideForMoreInfoMixin, _GenerateSummaryMixin, _GenerateCompleteLessonPlanMixin, _BuildEnhancedInputMixin, _ReviseLessonPlanMixin, _ExportLessonPlanMixin, _GetMarkdownContentMixin, _GetHtmlContentMixin, _GetHtmlCssMixin, _CleanExpiredSessionsMixin, _UpdateSessionActivityMixin, _GetSessionStateMixin):
    """统一教案生成系统"""


unified_lesson_plan_system = UnifiedLessonPlanSystem()

def generate_lesson_plan(
    user_input: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成教案 - 统一入口
    
    智能判断用户输入的完整程度：
    - 信息完整 → 直接生成完整教案
    - 信息不完整 → 引导用户补充关键信息
    """
    return unified_lesson_plan_system.process_lesson_plan_request(user_input, session_id)


def revise_lesson_plan(session_id: str, revision_request: str) -> Dict[str, Any]:
    """修改教案"""
    return unified_lesson_plan_system.revise_lesson_plan(session_id, revision_request)


def export_lesson_plan(
    session_id: str,
    export_format: str = "markdown",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """导出教案"""
    return unified_lesson_plan_system.export_lesson_plan(session_id, export_format, filename)
