from .._shared import *


class _CleanJsonResponseMixin:
    def _clean_json_response(self, response: str) -> str:
        """
        清洗模型输出，兼容 Markdown 代码块与前后说明文本。

        Args:
            response: 模型原始响应

        Returns:
            可用于 json.loads 的字符串
        """
        content = (response or "").strip()
        if not content:
            return content

        # 先处理 ```json ... ``` 或 ``` ... ``` 包裹
        fence_match = re.match(
            r"^\s*```(?:json|JSON)?\s*([\s\S]*?)\s*```\s*$",
            content,
        )
        if fence_match:
            content = fence_match.group(1).strip()

        # 若还有前后说明文本，尝试提取最外层 JSON 对象
        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            content = content[first_brace:last_brace + 1]

        return content
