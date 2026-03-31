from .._shared import *


class _InitMixin:
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化教案导出器
        
        Args:
            output_dir: 输出目录，默认为配置文件中指定的目录
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # 从配置获取导出路径
            export_path = config_manager.get_export_path()
            self.output_dir = Path(export_path)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
