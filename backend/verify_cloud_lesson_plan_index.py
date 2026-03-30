"""
验证云端教案CSV索引是否可用于教案资源迁移
"""

import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / "backend"))

    from app.core.resource_table_parser import ResourceTableParser

    parser = ResourceTableParser(str(project_root / "learning_resource"))
    rows = parser._load_cloud_lesson_plan_index()
    markdown_rows = [
        row for row in rows
        if row.get("扩展名", "").lower() in {".md", "md"} or row.get("文件类型", "") == "Markdown文件"
    ]
    rows_by_path = {parser._build_logical_lesson_plan_path(row).lower(): row for row in rows}
    rows_by_name = {}
    for row in rows:
        rows_by_name.setdefault(parser._normalize_filename_key(row.get("文件名", "")), []).append(row)

    print(f"索引总记录数: {len(rows)}")
    print(f"Markdown教案数: {len(markdown_rows)}")

    sample_count = min(5, len(markdown_rows))
    success_count = 0

    # 只抽样验证，避免每次都全量拉取云端正文
    for row in markdown_rows[:sample_count]:
        linked_row = parser._find_linked_lesson_plan_row(
            row,
            rows_by_path,
            rows_by_name,
        )
        markdown_url = row.get("云端链接", "").strip() or parser._derive_markdown_url(row.get("文件名", ""), linked_row)
        content = parser._download_cloud_markdown(markdown_url)
        content_source = "cloud_markdown"
        if not content:
            content = parser._build_lesson_plan_fallback_content(
                row,
                parser._build_logical_lesson_plan_path(row),
                linked_row,
                parser._extract_lesson_plan_topics(
                    f"{Path(row.get('文件名', '')).stem} {row.get('目录', '')} {parser._build_logical_lesson_plan_path(row)}"
                ),
            )
            content_source = "index_fallback"
        print("-" * 80)
        print(f"文件名: {row.get('文件名', '')}")
        print(f"逻辑路径: {parser._build_logical_lesson_plan_path(row)}")
        print(f"Markdown链接: {markdown_url}")
        print(f"内容来源: {content_source}")
        print(f"正文长度: {len(content)}")
        print(f"原文件: {linked_row.get('文件名', '') if linked_row else ''}")
        print(f"原文件链接: {linked_row.get('云端链接', '') if linked_row else ''}")
        if content:
            success_count += 1

    print("-" * 80)
    print(f"抽样成功数: {success_count}/{sample_count}")
    return 0 if success_count == sample_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
