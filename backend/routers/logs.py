"""
日志审计路由
"""
from fastapi import APIRouter, Depends, HTTPException, Response as FastAPIResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import Optional
import csv
import io

from backend.core.database import get_db, User, AuditLog
from backend.core.auth import get_current_user, require_permission
from backend.core.schemas import Response, AuditLogQuery

router = APIRouter(prefix="/api/logs", tags=["日志审计"])


@router.get("", response_model=Response)
async def get_logs(
    user_id: Optional[int] = None,
    module: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("logs", "read"))
):
    """
    获取审计日志列表
    
    需要权限: logs.read (管理员和审计员)
    
    查询参数:
    - user_id: 用户ID
    - module: 模块名称
    - action: 操作动作
    - status: 状态(success/failed)
    - start_time: 开始时间(ISO格式)
    - end_time: 结束时间(ISO格式)
    - page: 页码
    - page_size: 每页数量
    """
    query = db.query(AuditLog)
    
    # 构建筛选条件
    filters = []
    
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    if module:
        filters.append(AuditLog.module == module)
    
    if action:
        filters.append(AuditLog.action == action)
    
    if status:
        filters.append(AuditLog.status == status)
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误")
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误")
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 按时间倒序排列
    query = query.order_by(AuditLog.created_at.desc())
    
    # 分页
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 构造响应
    log_list = []
    for log in logs:
        # 获取用户名
        username = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                username = user.username
        
        log_list.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": username,
            "module": log.module,
            "action": log.action,
            "ip_address": log.ip_address,
            "status": log.status,
            "details": log.details,
            "created_at": log.created_at
        })
    
    return Response(
        code=200,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "logs": log_list
        }
    )


@router.get("/export")
async def export_logs(
    user_id: Optional[int] = None,
    module: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("logs", "read"))
):
    """
    导出审计日志
    
    需要权限: logs.read (管理员和审计员)
    
    查询参数:
    - user_id: 用户ID
    - module: 模块名称
    - action: 操作动作
    - status: 状态(success/failed)
    - start_time: 开始时间(ISO格式)
    - end_time: 结束时间(ISO格式)
    - format: 导出格式(csv/excel)
    """
    query = db.query(AuditLog)
    
    # 构建筛选条件（与get_logs相同）
    filters = []
    
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    if module:
        filters.append(AuditLog.module == module)
    
    if action:
        filters.append(AuditLog.action == action)
    
    if status:
        filters.append(AuditLog.status == status)
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误")
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误")
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 按时间倒序排列
    query = query.order_by(AuditLog.created_at.desc())
    
    # 获取所有日志（限制最多10000条）
    logs = query.limit(10000).all()
    
    if format == "csv":
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "用户ID", "用户名", "模块", "操作", 
            "IP地址", "状态", "详细信息", "创建时间"
        ])
        
        # 写入数据
        for log in logs:
            username = ""
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    username = user.username
            
            writer.writerow([
                log.id,
                log.user_id or "",
                username,
                log.module,
                log.action,
                log.ip_address or "",
                log.status,
                log.details or "",
                log.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        # 返回CSV文件
        output.seek(0)
        return FastAPIResponse(
            content=output.getvalue().encode('utf-8-sig'),  # 使用utf-8-sig以支持Excel打开
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式")


@router.get("/statistics", response_model=Response)
async def get_log_statistics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("logs", "read"))
):
    """
    获取日志统计信息
    
    需要权限: logs.read (管理员和审计员)
    """
    query = db.query(AuditLog)
    
    # 时间筛选
    filters = []
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误")
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            filters.append(AuditLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误")
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 统计总数
    total_logs = query.count()
    
    # 按状态统计
    success_count = query.filter(AuditLog.status == "success").count()
    failed_count = query.filter(AuditLog.status == "failed").count()
    
    # 按模块统计
    module_stats = {}
    modules = db.query(AuditLog.module).distinct().all()
    for (module,) in modules:
        count = query.filter(AuditLog.module == module).count()
        module_stats[module] = count
    
    # 按操作统计
    action_stats = {}
    actions = db.query(AuditLog.action).distinct().all()
    for (action,) in actions:
        count = query.filter(AuditLog.action == action).count()
        action_stats[action] = count
    
    return Response(
        code=200,
        message="success",
        data={
            "total_logs": total_logs,
            "success_count": success_count,
            "failed_count": failed_count,
            "module_stats": module_stats,
            "action_stats": action_stats
        }
    )
