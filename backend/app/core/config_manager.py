"""配置管理模块"""
import os
import yaml
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_paths()
    
    def _load_config(self) -> dict:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            # 尝试从多个位置加载配置文件
            possible_config_paths = [
                Path(__file__).parent / self.config_file,
                Path(__file__).parent.parent / self.config_file,
                Path.cwd() / self.config_file
            ]
            
            for config_path in possible_config_paths:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        print(f"✅ 成功加载配置文件: {config_path}")
                        return config
            
            print(f"⚠️ 未找到配置文件，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "paths": {
                "learning_resource": {
                    "relative": "learning_resource",
                    "env_var": "LEARNING_RESOURCE_PATH"
                }
            },
            "session": {
                "timeout": 3600
            },
            "export": {
                "directory": {
                    "relative": "exports",
                    "env_var": "EXPORT_PATH"
                }
            },
            "logging": {
                "directory": {
                    "relative": "logs",
                    "env_var": "LOG_PATH"
                }
            }
        }
    
    def _validate_paths(self):
        """
        验证路径是否存在
        """
        learning_resource_path = self.get_learning_resource_path()
        if not os.path.exists(learning_resource_path):
            print(f"⚠️ 学习资源目录不存在: {learning_resource_path}")
            print("⚠️ 将使用内置默认内容")
        
        export_path = self.get_export_path()
        if not os.path.exists(export_path):
            os.makedirs(export_path, exist_ok=True)
            print(f"✅ 创建导出目录: {export_path}")
        
        log_path = self.get_log_path()
        if not os.path.exists(log_path):
            os.makedirs(log_path, exist_ok=True)
            print(f"✅ 创建日志目录: {log_path}")
    
    def get_learning_resource_path(self) -> str:
        """
        获取学习资源目录路径
        
        Returns:
            学习资源目录路径
        """
        # 优先使用环境变量
        env_path = os.environ.get(self.config["paths"]["learning_resource"]["env_var"])
        if env_path and os.path.exists(env_path):
            return env_path
        
        # 使用相对路径
        relative_path = self.config["paths"]["learning_resource"]["relative"]
        # 尝试从多个位置计算绝对路径
        possible_paths = [
            Path(__file__).parent.parent.parent / relative_path,
            Path(__file__).parent.parent / relative_path,
            Path.cwd() / relative_path
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 返回默认路径
        return str(Path.cwd() / relative_path)
    
    def get_export_path(self) -> str:
        """
        获取导出目录路径
        
        Returns:
            导出目录路径
        """
        # 优先使用环境变量
        env_path = os.environ.get(self.config["export"]["directory"]["env_var"])
        if env_path:
            return env_path
        
        # 使用相对路径
        relative_path = self.config["export"]["directory"]["relative"]
        return str(Path.cwd() / relative_path)
    
    def get_log_path(self) -> str:
        """
        获取日志目录路径
        
        Returns:
            日志目录路径
        """
        # 优先使用环境变量
        env_path = os.environ.get(self.config["logging"]["directory"]["env_var"])
        if env_path:
            return env_path
        
        # 使用相对路径
        relative_path = self.config["logging"]["directory"]["relative"]
        return str(Path.cwd() / relative_path)
    
    def get_session_timeout(self) -> int:
        """
        获取会话超时时间
        
        Returns:
            会话超时时间（秒）
        """
        return self.config.get("session", {}).get("timeout", 3600)

# 全局配置实例
config_manager = ConfigManager()