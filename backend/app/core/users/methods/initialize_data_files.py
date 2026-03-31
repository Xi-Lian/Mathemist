from .._shared import *


class _InitializeDataFilesMixin:
    def _initialize_data_files(self):
        """初始化数据文件"""
        if not self.users_file.exists():
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
