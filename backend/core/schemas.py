"""
Pydantic模型定义（用于请求和响应验证）
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime


# 用户相关模型
class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str
    
    @validator('username')
    def username_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()
    
    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        return v


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    confirm_password: str
    role_id: int = 2  # 默认为算法调试员
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50之间')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度必须至少8位')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次密码输入不一致')
        return v


class RoleInfo(BaseModel):
    """角色信息"""
    id: int
    name: str
    permissions: Dict[str, Any]
    description: Optional[str]
    
    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    role: RoleInfo
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserInfo


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None


# 统一响应模型
class Response(BaseModel):
    """统一API响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 用户管理相关模型
class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    role_id: int
    status: str = "active"
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50之间')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度必须至少8位')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('用户名不能为空')
            if len(v) < 3 or len(v) > 50:
                raise ValueError('用户名长度必须在3-50之间')
            return v.strip()
        return v


class PasswordReset(BaseModel):
    """重置密码请求"""
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度必须至少8位')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class UserListItem(BaseModel):
    """用户列表项"""
    id: int
    username: str
    role_id: int
    role_name: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# 角色管理相关模型
class RoleCreate(BaseModel):
    """创建角色请求"""
    name: str
    permissions: Dict[str, Any]
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('角色名称不能为空')
        if len(v) > 50:
            raise ValueError('角色名称长度不能超过50')
        return v.strip()


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('角色名称不能为空')
            if len(v) > 50:
                raise ValueError('角色名称长度不能超过50')
            return v.strip()
        return v


# 日志审计相关模型
class AuditLogQuery(BaseModel):
    """审计日志查询参数"""
    user_id: Optional[int] = None
    module: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


class AuditLogItem(BaseModel):
    """审计日志项"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    module: str
    action: str
    ip_address: Optional[str]
    status: str
    details: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
