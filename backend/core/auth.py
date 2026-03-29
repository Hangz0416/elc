"""
认证和授权相关功能
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os

from backend.core.database import get_db, User, Role, AuditLog

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户凭证"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.status != "active":
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return user


def has_permission(user: User, module: str, action: str) -> bool:
    """检查用户是否有权限"""
    if not user.role:
        return False
    
    permissions = user.role.permissions
    
    # 管理员拥有所有权限
    if permissions.get("all") is True:
        return True
    
    # 检查模块权限
    module_perm = permissions.get(module)
    if not module_perm:
        return False
    
    # 如果是字符串权限（如 "rw", "r"）
    if isinstance(module_perm, str):
        if action == "read" and "r" in module_perm:
            return True
        if action == "write" and "w" in module_perm:
            return True
    
    # 如果是布尔值权限
    if isinstance(module_perm, bool) and module_perm:
        return True
    
    return False


def require_permission(module: str, action: str):
    """权限验证装饰器"""
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ):
        if not has_permission(current_user, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {module}.{action} 权限"
            )
        return current_user
    
    return permission_checker


def log_audit(
    db: Session,
    user_id: Optional[int],
    module: str,
    action: str,
    ip_address: Optional[str],
    status: str,
    details: Optional[str] = None
):
    """记录审计日志"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            module=module,
            action=action,
            ip_address=ip_address,
            status=status,
            details=details
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"记录审计日志失败: {e}")
        db.rollback()


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"
