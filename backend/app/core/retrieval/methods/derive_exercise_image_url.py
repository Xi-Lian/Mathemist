from .._shared import *
import re

from urllib.parse import quote


CHINESE_DIGITS = {
    0: "零",
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}


def _to_chinese_numeral(value: int) -> str:
    if value <= 10:
        return CHINESE_DIGITS[value]
    if value < 20:
        return f"十{CHINESE_DIGITS[value % 10]}"
    if value < 100:
        tens, ones = divmod(value, 10)
        tens_text = f"{CHINESE_DIGITS[tens]}十"
        return tens_text if ones == 0 else f"{tens_text}{CHINESE_DIGITS[ones]}"
    return str(value)


def _extract_chapter_number(image_filename: str) -> Optional[int]:
    match = re.match(r"^\s*(\d+)[-.]", image_filename or "")
    if not match:
        return None
    return int(match.group(1))


def _build_chapter_dir(chapter_number: Optional[int], image_kind: str) -> str:
    if chapter_number is None:
        return ""
    suffix = "题目" if image_kind == "question" else "答案"
    return f"第{_to_chinese_numeral(chapter_number)}章{suffix}"


def _extract_cloud_base_url(base_cloud_url: str) -> str:
    if not base_cloud_url:
        return ""
    normalized = base_cloud_url.strip()
    if not normalized.startswith(("http://", "https://")):
        return ""
    if "/" not in normalized:
        return normalized
    return normalized.rsplit("/", 1)[0].rstrip("/")


def derive_exercise_image_url(image_filename: str, base_cloud_url: str, image_kind: str) -> str:
    image_filename = (image_filename or "").strip()
    if not image_filename or not image_filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return ""

    chapter_number = _extract_chapter_number(image_filename)
    chapter_dir = _build_chapter_dir(chapter_number, image_kind)
    base_dir = _extract_cloud_base_url(base_cloud_url)
    if not chapter_dir or not base_dir:
        return ""

    encoded_filename = quote(image_filename, safe="/")
    encoded_chapter_dir = quote(chapter_dir, safe="/")
    return f"{base_dir}/{encoded_chapter_dir}/{encoded_filename}"
