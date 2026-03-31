"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.export_markdown import _ExportMarkdownMixin
from .methods.export_html import _ExportHtmlMixin
from .methods.export_docx import _ExportDocxMixin
from .methods.export_pdf import _ExportPdfMixin
from .methods.export_all import _ExportAllMixin
from .methods.add_metadata_header import _AddMetadataHeaderMixin
from .methods.build_html_document import _BuildHtmlDocumentMixin
from .methods.get_css import _GetCssMixin
from .methods.add_markdown_to_docx import _AddMarkdownToDocxMixin

class LessonPlanExporter(_InitMixin, _ExportMarkdownMixin, _ExportHtmlMixin, _ExportDocxMixin, _ExportPdfMixin, _ExportAllMixin, _AddMetadataHeaderMixin, _BuildHtmlDocumentMixin, _GetCssMixin, _AddMarkdownToDocxMixin):
    """教案导出器"""


lesson_plan_exporter = LessonPlanExporter()

def export_lesson_plan_markdown(
    lesson_plan_content: str,
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """导出为Markdown"""
    return lesson_plan_exporter.export_markdown(lesson_plan_content, filename, metadata)


def export_lesson_plan_html(
    lesson_plan_content: str,
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """导出为HTML"""
    return lesson_plan_exporter.export_html(lesson_plan_content, filename, metadata)


def export_lesson_plan_docx(
    lesson_plan_content: str,
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """导出为Word文档"""
    return lesson_plan_exporter.export_docx(lesson_plan_content, filename, metadata)


def export_lesson_plan_pdf(
    lesson_plan_content: str,
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """导出为PDF"""
    return lesson_plan_exporter.export_pdf(lesson_plan_content, filename, metadata)


def export_lesson_plan_all(
    lesson_plan_content: str,
    filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    formats: Optional[list] = None
) -> Dict[str, str]:
    """导出为多种格式"""
    return lesson_plan_exporter.export_all(lesson_plan_content, filename, metadata, formats)
