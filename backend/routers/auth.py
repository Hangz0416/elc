"""
认证相关路由
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.core.database import get_db, User
from backend.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    log_audit,
    get_client_ip,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_HOURS
)
from backend.core.schemas import UserLogin, UserRegister, UserInfo, RoleInfo, Response

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=Response)
async def login(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT token和用户信息
    """
    # 验证用户凭证
    user = authenticate_user(db, user_login.username, user_login.password)
    
    if not user:
        # 记录登录失败日志
        log_audit(
            db=db,
            user_id=None,
            module="auth",
            action="login",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"用户名或密码错误: {user_login.username}"
        )
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    
    # 更新最后登录时间
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 记录登录成功日志
    log_audit(
        db=db,
        user_id=user.id,
        module="auth",
        action="login",
        ip_address=get_client_ip(request),
        status="success"
    )
    
    # 构造用户信息
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        role=RoleInfo(
            id=user.role.id,
            name=user.role.name,
            permissions=user.role.permissions,
            description=user.role.description
        ),
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )
    
    return Response(
        code=200,
        message="登录成功",
        data={
            "token": access_token,
            "user": user_info.dict()
        }
    )


@router.post("/register", response_model=Response)
async def register(
    user_register: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    用户注册接口
    
    - **username**: 用户名（3-50字符）
    - **password**: 密码（至少8位，包含字母和数字）
    - **confirm_password**: 确认密码
    - **role_id**: 角色ID（默认为2-算法调试员）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_register.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # 创建新用户
    new_user = User(
        username=user_register.username,
        password_hash=get_password_hash(user_register.password),
        role_id=user_register.role_id,
        status="active"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 记录注册日志
    log_audit(
        db=db,
        user_id=new_user.id,
        module="auth",
        action="register",
        ip_address=get_client_ip(request),
        status="success"
    )
    
    return Response(
        code=200,
        message="注册成功",
        data={
            "id": new_user.id,
            "username": new_user.username
        }
    )


@router.get("/profile", response_model=Response)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    
    需要在请求头中携带有效的JWT token:
    Authorization: Bearer <token>
    """
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=RoleInfo(
            id=current_user.role.id,
            name=current_user.role.name,
            permissions=current_user.role.permissions,
            description=current_user.role.description
        ),
        status=current_user.status,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
    
    return Response(
        code=200,
        message="success",
        data=user_info.dict()
    )


@router.post("/logout", response_model=Response)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出接口
    
    记录登出日志（实际的token失效由前端处理）
    """
    # 记录登出日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="auth",
        action="logout",
        ip_address=get_client_ip(request),
        status="success"
    )
    
    return Response(
        code=200,
        message="登出成功"
    )


@router.post("/verify-username", response_model=Response)
async def verify_username(
    data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    验证用户名是否存在（用于忘记密码流程）
    
    - **username**: 用户名
    """
    username = data.get("username")
    
    if not username:
        raise HTTPException(
            status_code=400,
            detail="用户名不能为空"
        )
    
    # 查询用户是否存在
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        # 记录验证失败日志
        log_audit(
            db=db,
            user_id=None,
            module="auth",
            action="verify_username",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"用户名不存在: {username}"
        )
        raise HTTPException(
            status_code=404,
            detail="用户名不存在"
        )
    
    # 记录验证成功日志
    log_audit(
        db=db,
        user_id=user.id,
        module="auth",
        action="verify_username",
        ip_address=get_client_ip(request),
        status="success"
    )
    
    return Response(
        code=200,
        message="用户验证成功",
        data={"username": username}
    )


@router.post("/reset-password", response_model=Response)
async def reset_password(
    data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    重置密码（用于忘记密码流程）
    
    - **username**: 用户名
    - **new_password**: 新密码
    """
    username = data.get("username")
    new_password = data.get("new_password")
    
    if not username or not new_password:
        raise HTTPException(
            status_code=400,
            detail="用户名和新密码不能为空"
        )
    
    # 验证密码强度
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="密码长度至少为8位"
        )
    
    import re
    if not re.search(r'[a-zA-Z]', new_password) or not re.search(r'\d', new_password):
        raise HTTPException(
            status_code=400,
            detail="密码必须包含字母和数字"
        )
    
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        # 记录重置失败日志
        log_audit(
            db=db,
            user_id=None,
            module="auth",
            action="reset_password",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"用户名不存在: {username}"
        )
        raise HTTPException(
            status_code=404,
            detail="用户名不存在"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    # 记录重置成功日志
    log_audit(
        db=db,
        user_id=user.id,
        module="auth",
        action="reset_password",
        ip_address=get_client_ip(request),
        status="success",
        details="密码重置成功"
    )
    
    return Response(
        code=200,
        message="密码重置成功",
        data={"username": username}
    )
