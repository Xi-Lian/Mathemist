from .._shared import *


class _DetectCsvEncodingMixin:
    def _detect_csv_encoding(self, csv_path: Path) -> str:
        """
        检测CSV编码，兼容UTF-8和GB系列编码
        """
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                with open(csv_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    if header:
                        return encoding
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        return "utf-8-sig"
