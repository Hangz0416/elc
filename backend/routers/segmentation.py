"""
场景分割相关路由
"""
from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import os

from backend.logic.segmentation_logic import run_segmentation
from backend.core.database import get_db, User
from backend.core.auth import require_permission, log_audit, get_client_ip

router = APIRouter(prefix="/api", tags=["场景分割"])


@router.post("/segmentation")
async def segmentation_endpoint(
    scene_name: str = Form(..., description="要执行分割的原始场景名称 (例如 'Building')"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("segmentation", "write"))
):
    """
    对一个原始场景，执行完整的分割流程：准备mask -> 训练 -> 渲染。
    如果结果已存在，则直接返回缓存的结果。
    
    需要权限: segmentation.write (管理员和算法调试员)
    """
    # 验证场景是否存在
    source_root = "static/reconstruction_data/RGBT-Scenes"
    scene_path = os.path.join(source_root, scene_name)

    if not os.path.isdir(scene_path):
        log_audit(
            db=db,
            user_id=current_user.id,
            module="segmentation",
            action="execute",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"场景: {scene_name}, 错误: 场景未找到"
        )
        raise HTTPException(status_code=404, detail=f"找不到指定的原始场景: '{scene_name}'")

    try:
        print(f"将分割任务添加到线程池：场景 '{scene_name}'")
        
        result_pairs = await run_in_threadpool(
            run_segmentation,
            scene_name=scene_name
        )

        if not result_pairs:
            log_audit(
                db=db,
                user_id=current_user.id,
                module="segmentation",
                action="execute",
                ip_address=get_client_ip(request),
                status="failed",
                details=f"场景: {scene_name}, 错误: 未生成有效文件"
            )
            raise HTTPException(status_code=500, detail="分割任务运行后未生成任何有效文件。请检查终端日志。")

        # 记录成功日志
        log_audit(
            db=db,
            user_id=current_user.id,
            module="segmentation",
            action="execute",
            ip_address=get_client_ip(request),
            status="success",
            details=f"场景: {scene_name}, 结果数: {len(result_pairs)}"
        )

        return JSONResponse(content={
            "status": "Segmentation complete",
            "segmentation_pairs": result_pairs,
            "scene_name": scene_name
        })

    except Exception as e:
        log_audit(
            db=db,
            user_id=current_user.id,
            module="segmentation",
            action="execute",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"场景: {scene_name}, 错误: {str(e)}"
        )
        
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分割过程中发生服务器内部错误: {str(e)}")
