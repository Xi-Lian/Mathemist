from .._shared import *


class _PrintMatchInfoMixin:
    def _print_match_info(self, core_theme: str, title: str, result: Dict[str, Any]) -> None:
        """
        打印匹配信息（可视化）
        
        Args:
            core_theme: 核心主题
            title: 资源标题
            result: 匹配结果
        """
        if result["is_theme_match"]:
            evidence_type, evidence_text = result["match_evidence"][0] if result["match_evidence"] else ("未知", "")
            print(f"   🎯 主题匹配+分: +{result['relevance_boost']:.0%}, "
                  f"依据: {evidence_type}")
        if result["is_conflict_theme"]:
            conflict_theme, conflict_text = result["conflict_evidence"][0] if result["conflict_evidence"] else ("未知", "")
            print(f"   ⚠️  冲突主题-分: -{result['relevance_penalty']:.0%}, "
                  f"冲突: {conflict_theme}")
