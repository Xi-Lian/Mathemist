from .._shared import *


class _AddMetadataHeaderMixin:
    def _add_metadata_header(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """
        添加元数据头部
        
        Args:
            content: 原始内容
            metadata: 元数据字典
        
        Returns:
            添加元数据后的内容
        """
        if not metadata:
            return content
        
        header_lines = ["---"]
        for key, value in metadata.items():
            header_lines.append(f"{key}: {value}")
        header_lines.append(f"export_time: {datetime.now().isoformat()}")
        header_lines.append("---")
        header_lines.append("")
        
        return "\n".join(header_lines) + content
