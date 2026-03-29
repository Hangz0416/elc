"""
用户管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import get_db, User, Role
from backend.core.auth import (
    get_current_user,
    require_permission,
    get_password_hash,
    log_audit,
    get_client_ip
)
from backend.core.schemas import (
    Response,
    UserCreate,
    UserUpdate,
    PasswordReset,
    UserListItem
)

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=Response)
async def get_users(
    page: int = 1,
    page_size: int = 20,
    username: str = None,
    role_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "read"))
):
    """
    获取用户列表
    
    需要权限: users.read
    """
    query = db.query(User)
    
    # 筛选条件
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    if role_id:
        query = query.filter(User.role_id == role_id)
    if status:
        query = query.filter(User.status == status)
    
    # 分页
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 构造响应
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "status": user.status,
            "created_at": user.created_at,
            "last_login": user.last_login
        })
    
    return Response(
        code=200,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "users": user_list
        }
    )


@router.get("/{user_id}", response_model=Response)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "read"))
):
    """
    获取用户详情
    
    需要权限: users.read
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return Response(
        code=200,
        message="success",
        data={
            "id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "status": user.status,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
    )


@router.post("", response_model=Response)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "write"))
):
    """
    创建用户
    
    需要权限: users.write
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查角色是否存在
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="角色不存在")
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role_id=user_data.role_id,
        status=user_data.status
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="users",
        action="create",
        ip_address=get_client_ip(request),
        status="success",
        details=f"创建用户: {new_user.username}"
    )
    
    return Response(
        code=200,
        message="用户创建成功",
        data={
            "id": new_user.id,
            "username": new_user.username
        }
    )


@router.put("/{user_id}", response_model=Response)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "write"))
):
    """
    更新用户信息
    
    需要权限: users.write
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许修改管理员账户
    if user.role.name == "admin" and current_user.id != user.id:
        raise HTTPException(status_code=403, detail="不允许修改管理员账户")
    
    # 更新字段
    if user_data.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = user_data.username
    
    if user_data.role_id is not None:
        # 检查角色是否存在
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="角色不存在")
        user.role_id = user_data.role_id
    
    if user_data.status is not None:
        user.status = user_data.status
    
    db.commit()
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="users",
        action="update",
        ip_address=get_client_ip(request),
        status="success",
        details=f"更新用户: {user.username}"
    )
    
    return Response(
        code=200,
        message="用户更新成功"
    )


@router.post("/{user_id}/reset-password", response_model=Response)
async def reset_password(
    user_id: int,
    password_data: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "write"))
):
    """
    重置用户密码
    
    需要权限: users.write
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新密码
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="users",
        action="reset_password",
        ip_address=get_client_ip(request),
        status="success",
        details=f"重置用户密码: {user.username}"
    )
    
    return Response(
        code=200,
        message="密码重置成功"
    )


@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "write"))
):
    """
    删除用户
    
    需要权限: users.write
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许删除管理员账户
    if user.role.name == "admin":
        raise HTTPException(status_code=403, detail="不允许删除管理员账户")
    
    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="不允许删除自己的账户")
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="users",
        action="delete",
        ip_address=get_client_ip(request),
        status="success",
        details=f"删除用户: {username}"
    )
    
    return Response(
        code=200,
        message="用户删除成功"
    )
