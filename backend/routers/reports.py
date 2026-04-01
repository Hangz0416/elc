from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os
import json
import io
import zipfile
from pathlib import Path

from backend.core.auth import get_current_user
from backend.core.database import get_db, AuditLog, User

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"]
)


# ========== 获取报告列表 ==========
@router.get("")
async def get_reports(
    type: Optional[str] = None,
    scene: Optional[str] = None,
    date: Optional[str] = None,
    page: int = 1,
    page_size: int = 15,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取报告列表
    - type: 报告类型 (fusion/reconstruction/segmentation)
    - scene: 场景名称
    - date: 日期筛选 (YYYY-MM-DD)
    - page: 页码
    - page_size: 每页数量
    """
    try:
        # 从审计日志中获取处理记录作为报告
        query = db.query(AuditLog)
        
        # 筛选处理类型的日志
        filters = [AuditLog.action.in_(["fusion", "reconstruction", "segmentation"])]
        
        # 应用筛选条件
        if type:
            filters.append(AuditLog.action == type)
        
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                next_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59)
                filters.append(and_(
                    AuditLog.created_at >= date_obj,
                    AuditLog.created_at <= next_day
                ))
            except ValueError:
                pass
        
        query = query.filter(and_(*filters))
        
        # 按时间倒序排序
        query = query.order_by(AuditLog.created_at.desc())
        
        # 获取所有符合条件的日志（用于场景筛选）
        all_logs = query.all()
        
        # 场景筛选（需要解析details字段）
        if scene:
            filtered_logs = []
            for log in all_logs:
                try:
                    details = json.loads(log.details) if log.details else {}
                    if details.get("scene") == scene:
                        filtered_logs.append(log)
                except:
                    pass
            all_logs = filtered_logs
        
        # 分页
        total = len(all_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = all_logs[start:end]
        
        # 转换为报告格式
        reports = []
        for log in paginated_logs:
            # 解析details字段
            try:
                details = json.loads(log.details) if log.details else {}
            except:
                details = {}
            
            # 获取用户名
            username = "Unknown"
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    username = user.username
            
            report = {
                "id": log.id,
                "type": log.action,
                "scene": details.get("scene", "Unknown"),
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "duration": details.get("duration", 0),
                "user": username,
                "details": details
            }
            
            # 添加类型特定信息
            if report["type"] == "fusion":
                report["images_count"] = details.get("images_count", 0)
                report["metrics"] = details.get("metrics", {})
            elif report["type"] == "reconstruction":
                report["method"] = details.get("method", "Unknown")
            
            reports.append(report)
        
        return {
            "success": True,
            "data": {
                "reports": reports,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")


# ========== 获取报告统计 ==========
@router.get("/statistics")
async def get_report_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告统计数据"""
    try:
        # 统计各类型报告数量
        fusion_count = db.query(AuditLog).filter(AuditLog.action == "fusion").count()
        reconstruction_count = db.query(AuditLog).filter(AuditLog.action == "reconstruction").count()
        segmentation_count = db.query(AuditLog).filter(AuditLog.action == "segmentation").count()
        total_count = fusion_count + reconstruction_count + segmentation_count
        
        return {
            "success": True,
            "data": {
                "total": total_count,
                "fusion": fusion_count,
                "reconstruction": reconstruction_count,
                "segmentation": segmentation_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


# ========== 获取单个报告详情 ==========
@router.get("/{report_id}")
async def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告详情"""
    try:
        # 查找对应的日志记录
        log = db.query(AuditLog).filter(AuditLog.id == report_id).first()
        
        if not log:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # 解析details字段
        try:
            details = json.loads(log.details) if log.details else {}
        except:
            details = {}
        
        # 获取用户名
        username = "Unknown"
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                username = user.username
        
        # 构建报告详情
        report = {
            "id": log.id,
            "type": log.action,
            "scene": details.get("scene", "Unknown"),
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "duration": details.get("duration", 0),
            "user": username,
            "details": details,
            "output_path": details.get("output_path", "")
        }
        
        # 添加类型特定信息
        if report["type"] == "fusion":
            report["images_count"] = details.get("images_count", 0)
            report["metrics"] = details.get("metrics", {})
        elif report["type"] == "reconstruction":
            report["method"] = details.get("method", "Unknown")
        
        return {
            "success": True,
            "data": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告详情失败: {str(e)}")


# ========== 下载报告（JSON格式）==========
@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载报告
    - format: 下载格式 (json/pdf/zip)
    """
    try:
        # 查找对应的日志记录
        log = db.query(AuditLog).filter(AuditLog.id == report_id).first()
        
        if not log:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # 解析details字段
        try:
            details = json.loads(log.details) if log.details else {}
        except:
            details = {}
        
        # 获取用户名
        username = "Unknown"
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                username = user.username
        
        # 构建报告数据
        report_data = {
            "report_id": log.id,
            "report_type": log.action,
            "scene_name": details.get("scene", "Unknown"),
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "processing_duration": details.get("duration", 0),
            "operator": username,
            "details": details,
            "output_path": details.get("output_path", ""),
            "generated_at": datetime.now().isoformat()
        }
        
        # 根据格式返回不同类型的文件
        if format == "json":
            # 返回JSON格式报告
            json_content = json.dumps(report_data, ensure_ascii=False, indent=2)
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        
        elif format == "zip":
            # 打包输出文件为ZIP
            output_path = details.get("output_path", "")
            
            # 创建内存中的ZIP文件
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 添加报告JSON
                zip_file.writestr(
                    f"report_{report_id}.json",
                    json.dumps(report_data, ensure_ascii=False, indent=2)
                )
                
                # 如果输出文件存在，则添加到ZIP
                if output_path and os.path.exists(output_path):
                    if os.path.isfile(output_path):
                        zip_file.write(output_path, os.path.basename(output_path))
                    elif os.path.isdir(output_path):
                        # 如果是目录，递归添加所有文件
                        for root, dirs, files in os.walk(output_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, output_path)
                                zip_file.write(file_path, arcname)
                else:
                    # 如果输出文件不存在，添加说明文件
                    readme_content = f"""报告 #{report_id} 说明

报告类型: {report_data['report_type']}
场景名称: {report_data['scene_name']}
处理状态: {report_data['status']}
创建时间: {report_data['created_at']}
操作员: {report_data['operator']}

注意: 输出文件路径不存在或已被删除
原始路径: {output_path if output_path else '未指定'}

详细信息请查看 report_{report_id}.json 文件
"""
                    zip_file.writestr("README.txt", readme_content)
            
            zip_buffer.seek(0)
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的下载格式")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")


# ========== 批量导出报告 ==========
@router.post("/export")
async def export_reports(
    report_ids: Optional[List[int]] = None,
    type: Optional[str] = None,
    scene: Optional[str] = None,
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量导出报告为CSV
    - report_ids: 指定报告ID列表（可选）
    - type/scene/date: 筛选条件（可选）
    """
    try:
        # 构建查询
        query = db.query(AuditLog)
        filters = [AuditLog.action.in_(["fusion", "reconstruction", "segmentation"])]
        
        # 应用筛选条件
        if report_ids:
            filters.append(AuditLog.id.in_(report_ids))
        
        if type:
            filters.append(AuditLog.action == type)
        
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                next_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59)
                filters.append(and_(
                    AuditLog.created_at >= date_obj,
                    AuditLog.created_at <= next_day
                ))
            except ValueError:
                pass
        
        query = query.filter(and_(*filters))
        report_logs = query.all()
        
        # 场景筛选
        if scene:
            filtered_logs = []
            for log in report_logs:
                try:
                    details = json.loads(log.details) if log.details else {}
                    if details.get("scene") == scene:
                        filtered_logs.append(log)
                except:
                    pass
            report_logs = filtered_logs
        
        # 生成CSV内容
        csv_lines = ["报告ID,类型,场景,状态,创建时间,处理时长(秒),操作员"]
        
        for log in report_logs:
            try:
                details = json.loads(log.details) if log.details else {}
            except:
                details = {}
            
            # 获取用户名
            username = "Unknown"
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    username = user.username
            
            csv_lines.append(
                f"{log.id},"
                f"{log.action},"
                f"{details.get('scene', 'Unknown')},"
                f"{log.status},"
                f"{log.created_at.isoformat() if log.created_at else ''},"
                f"{details.get('duration', 0)},"
                f"{username}"
            )
        
        csv_content = "\n".join(csv_lines)
        filename = f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content="\ufeff" + csv_content,  # 添加BOM以支持Excel中文显示
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出报告失败: {str(e)}")
