"""
角色管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import get_db, User, Role
from backend.core.auth import (
    get_current_user,
    require_permission,
    log_audit,
    get_client_ip
)
from backend.core.schemas import Response, RoleInfo, RoleCreate, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["角色管理"])


@router.get("", response_model=Response)
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色列表
    
    所有登录用户都可以查看角色列表
    """
    roles = db.query(Role).all()
    
    role_list = []
    for role in roles:
        role_list.append({
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions,
            "description": role.description,
            "created_at": role.created_at
        })
    
    return Response(
        code=200,
        message="success",
        data=role_list
    )


@router.get("/{role_id}", response_model=Response)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色详情
    
    所有登录用户都可以查看角色详情
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return Response(
        code=200,
        message="success",
        data={
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions,
            "description": role.description,
            "created_at": role.created_at
        }
    )


@router.post("", response_model=Response)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles", "write"))
):
    """
    创建角色
    
    需要权限: roles.write (仅管理员)
    """
    # 检查角色名是否已存在
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="角色名已存在")
    
    # 创建角色
    new_role = Role(
        name=role_data.name,
        permissions=role_data.permissions,
        description=role_data.description
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="roles",
        action="create",
        ip_address=get_client_ip(request),
        status="success",
        details=f"创建角色: {new_role.name}"
    )
    
    return Response(
        code=200,
        message="角色创建成功",
        data={
            "id": new_role.id,
            "name": new_role.name
        }
    )


@router.put("/{role_id}", response_model=Response)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles", "write"))
):
    """
    更新角色
    
    需要权限: roles.write (仅管理员)
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 不允许修改管理员角色
    if role.name == "admin":
        raise HTTPException(status_code=403, detail="不允许修改管理员角色")
    
    # 更新字段
    if role_data.name is not None:
        # 检查角色名是否已被其他角色使用
        existing_role = db.query(Role).filter(
            Role.name == role_data.name,
            Role.id != role_id
        ).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="角色名已存在")
        role.name = role_data.name
    
    if role_data.permissions is not None:
        role.permissions = role_data.permissions
    
    if role_data.description is not None:
        role.description = role_data.description
    
    db.commit()
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="roles",
        action="update",
        ip_address=get_client_ip(request),
        status="success",
        details=f"更新角色: {role.name}"
    )
    
    return Response(
        code=200,
        message="角色更新成功"
    )


@router.delete("/{role_id}", response_model=Response)
async def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles", "write"))
):
    """
    删除角色
    
    需要权限: roles.write (仅管理员)
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 不允许删除管理员角色
    if role.name == "admin":
        raise HTTPException(status_code=403, detail="不允许删除管理员角色")
    
    # 检查是否有用户使用该角色
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该角色下还有 {user_count} 个用户，无法删除"
        )
    
    role_name = role.name
    db.delete(role)
    db.commit()
    
    # 记录日志
    log_audit(
        db=db,
        user_id=current_user.id,
        module="roles",
        action="delete",
        ip_address=get_client_ip(request),
        status="success",
        details=f"删除角色: {role_name}"
    )
    
    return Response(
        code=200,
        message="角色删除成功"
    )
