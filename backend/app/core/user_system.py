"""
用户系统和备课历史记录模块

职责：
- 用户身份管理和认证
- 备课历史记录的存储和检索
- 个人备课数据的管理
- 支持用户个性化配置

依赖：
- json (数据持久化)
- pathlib (路径管理)
- datetime (时间戳)
- uuid (生成唯一ID)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class LessonPlanStatus(Enum):
    """教案状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class User:
    """用户数据模型"""
    user_id: str
    username: str
    email: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


@dataclass
class LessonPlanHistory:
    """备课历史记录"""
    history_id: str
    user_id: str
    topic: str
    chapter: Optional[str] = None
    textbook: Optional[str] = None
    teaching_goals: Optional[str] = None
    teaching_framework: Optional[str] = None
    lesson_plan_content: Optional[str] = None
    status: str = LessonPlanStatus.DRAFT.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LessonPlanHistory':
        return cls(**data)


class UserSystem:
    """用户系统管理器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化用户系统
        
        Args:
            data_dir: 数据存储目录，默认为 backend/data
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "backend" / "data"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.history_file = self.data_dir / "lesson_plan_history.json"
        
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """初始化数据文件"""
        if not self.users_file.exists():
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """加载用户数据"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载备课历史"""
        with open(self.history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_history(self, history: List[Dict[str, Any]]):
        """保存备课历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def create_user(self, username: str, email: str) -> User:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
        
        Returns:
            创建的用户对象
        """
        users = self._load_users()
        
        # 检查邮箱是否已存在
        for user_data in users.values():
            if user_data['email'] == email:
                raise ValueError(f"邮箱 {email} 已被使用")
        
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email
        )
        
        users[user_id] = user.to_dict()
        self._save_users(users)
        
        print(f"✅ 用户创建成功: {username} ({email})")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户对象，如果不存在则返回None
        """
        users = self._load_users()
        if user_id in users:
            return User.from_dict(users[user_id])
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 邮箱
        
        Returns:
            用户对象，如果不存在则返回None
        """
        users = self._load_users()
        for user_data in users.values():
            if user_data['email'] == email:
                return User.from_dict(user_data)
        return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Optional[User]:
        """
        更新用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
        
        Returns:
            更新后的用户对象
        """
        users = self._load_users()
        if user_id not in users:
            return None
        
        users[user_id]['preferences'].update(preferences)
        self._save_users(users)
        
        return User.from_dict(users[user_id])
    
    def create_lesson_plan_history(
        self,
        user_id: str,
        topic: str,
        chapter: Optional[str] = None,
        textbook: Optional[str] = None,
        teaching_goals: Optional[str] = None,
        teaching_framework: Optional[str] = None,
        lesson_plan_content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> LessonPlanHistory:
        """
        创建备课历史记录
        
        Args:
            user_id: 用户ID
            topic: 课题
            chapter: 章节
            textbook: 教材
            teaching_goals: 教学目标
            teaching_framework: 教学框架
            lesson_plan_content: 教案内容
            tags: 标签列表
            notes: 备注
        
        Returns:
            创建的历史记录对象
        """
        history_id = str(uuid.uuid4())
        history = LessonPlanHistory(
            history_id=history_id,
            user_id=user_id,
            topic=topic,
            chapter=chapter,
            textbook=textbook,
            teaching_goals=teaching_goals,
            teaching_framework=teaching_framework,
            lesson_plan_content=lesson_plan_content,
            status=LessonPlanStatus.DRAFT.value,
            tags=tags or [],
            notes=notes
        )
        
        history_list = self._load_history()
        history_list.append(history.to_dict())
        self._save_history(history_list)
        
        print(f"✅ 备课历史创建成功: {topic}")
        return history
    
    def update_lesson_plan_history(
        self,
        history_id: str,
        **kwargs
    ) -> Optional[LessonPlanHistory]:
        """
        更新备课历史记录
        
        Args:
            history_id: 历史记录ID
            **kwargs: 要更新的字段
        
        Returns:
            更新后的历史记录对象
        """
        history_list = self._load_history()
        
        for i, history_data in enumerate(history_list):
            if history_data['history_id'] == history_id:
                # 更新字段
                for key, value in kwargs.items():
                    if key in history_data:
                        history_data[key] = value
                
                history_data['updated_at'] = datetime.now().isoformat()
                
                self._save_history(history_list)
                return LessonPlanHistory.from_dict(history_data)
        
        return None
    
    def get_lesson_plan_history(self, history_id: str) -> Optional[LessonPlanHistory]:
        """
        获取单个备课历史记录
        
        Args:
            history_id: 历史记录ID
        
        Returns:
            历史记录对象
        """
        history_list = self._load_history()
        for history_data in history_list:
            if history_data['history_id'] == history_id:
                return LessonPlanHistory.from_dict(history_data)
        return None
    
    def get_user_lesson_plan_history(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LessonPlanHistory]:
        """
        获取用户的备课历史列表
        
        Args:
            user_id: 用户ID
            status: 状态过滤（可选）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            历史记录列表
        """
        history_list = self._load_history()
        
        # 过滤用户历史
        user_history = [
            h for h in history_list
            if h['user_id'] == user_id
        ]
        
        # 状态过滤
        if status:
            user_history = [
                h for h in user_history
                if h['status'] == status
            ]
        
        # 按更新时间倒序排列
        user_history.sort(
            key=lambda x: x['updated_at'],
            reverse=True
        )
        
        # 分页
        user_history = user_history[offset:offset + limit]
        
        return [LessonPlanHistory.from_dict(h) for h in user_history]
    
    def delete_lesson_plan_history(self, history_id: str) -> bool:
        """
        删除备课历史记录
        
        Args:
            history_id: 历史记录ID
        
        Returns:
            是否删除成功
        """
        history_list = self._load_history()
        original_length = len(history_list)
        
        history_list = [
            h for h in history_list
            if h['history_id'] != history_id
        ]
        
        if len(history_list) < original_length:
            self._save_history(history_list)
            print(f"✅ 备课历史删除成功")
            return True
        
        return False
    
    def search_lesson_plan_history(
        self,
        user_id: str,
        keyword: str,
        limit: int = 50
    ) -> List[LessonPlanHistory]:
        """
        搜索备课历史
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            匹配的历史记录列表
        """
        history_list = self._load_history()
        
        keyword = keyword.lower()
        results = []
        
        for history_data in history_list:
            if history_data['user_id'] != user_id:
                continue
            
            # 在多个字段中搜索
            search_text = ' '.join([
                str(history_data.get('topic', '')),
                str(history_data.get('chapter', '')),
                str(history_data.get('textbook', '')),
                str(history_data.get('notes', '')),
                ' '.join(history_data.get('tags', []))
            ]).lower()
            
            if keyword in search_text:
                results.append(history_data)
        
        # 按更新时间倒序排列
        results.sort(
            key=lambda x: x['updated_at'],
            reverse=True
        )
        
        results = results[:limit]
        
        return [LessonPlanHistory.from_dict(h) for h in results]


# 全局实例
user_system = UserSystem()


# 便捷函数接口
def create_user(username: str, email: str) -> User:
    """创建新用户"""
    return user_system.create_user(username, email)


def get_user(user_id: str) -> Optional[User]:
    """获取用户信息"""
    return user_system.get_user(user_id)


def get_user_by_email(email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return user_system.get_user_by_email(email)


def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> Optional[User]:
    """更新用户偏好"""
    return user_system.update_user_preferences(user_id, preferences)


def create_lesson_plan_history(
    user_id: str,
    topic: str,
    **kwargs
) -> LessonPlanHistory:
    """创建备课历史"""
    return user_system.create_lesson_plan_history(user_id, topic, **kwargs)


def update_lesson_plan_history(history_id: str, **kwargs) -> Optional[LessonPlanHistory]:
    """更新备课历史"""
    return user_system.update_lesson_plan_history(history_id, **kwargs)


def get_lesson_plan_history(history_id: str) -> Optional[LessonPlanHistory]:
    """获取备课历史"""
    return user_system.get_lesson_plan_history(history_id)


def get_user_lesson_plan_history(
    user_id: str,
    **kwargs
) -> List[LessonPlanHistory]:
    """获取用户备课历史列表"""
    return user_system.get_user_lesson_plan_history(user_id, **kwargs)


def delete_lesson_plan_history(history_id: str) -> bool:
    """删除备课历史"""
    return user_system.delete_lesson_plan_history(history_id)


def search_lesson_plan_history(
    user_id: str,
    keyword: str,
    **kwargs
) -> List[LessonPlanHistory]:
    """搜索备课历史"""
    return user_system.search_lesson_plan_history(user_id, keyword, **kwargs)
