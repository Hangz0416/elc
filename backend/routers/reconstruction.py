"""
三维重建相关路由
"""
from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import os

from backend.logic.reconstruction_logic import run_reconstruction, check_and_get_existing_results
from backend.core.database import get_db, User
from backend.core.auth import require_permission, log_audit, get_client_ip

router = APIRouter(prefix="/api", tags=["三维重建"])


@router.post("/reconstruction")
async def reconstruction_endpoint(
    scene_name: str = Form(..., description="要重建的场景名称 (例如 'Truck')"),
    method: str = Form("MSMG", description="重建方法: MSMG, MFTG, 或 OMMG"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reconstruction", "write"))
):
    """
    接收场景名称，使用 thermal-gaussian 模型在后台执行三维重建，并返回结果。
    如果结果已存在，则直接返回缓存的结果。
    
    需要权限: reconstruction.write (管理员和算法调试员)
    """
    data_root = "static/reconstruction_data"
    output_root = "static/reconstruction"

    # 动态查找场景的完整路径
    source_path = None
    for scene_collection in os.listdir(data_root):
        collection_path = os.path.join(data_root, scene_collection)
        if os.path.isdir(collection_path):
            potential_path = os.path.join(collection_path, scene_name)
            if os.path.isdir(potential_path):
                source_path = potential_path
                break  # 找到后即退出循环

    if not source_path:
        log_audit(
            db=db,
            user_id=current_user.id,
            module="reconstruction",
            action="execute",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"场景: {scene_name}, 方法: {method}, 错误: 场景未找到"
        )
        raise HTTPException(status_code=404, detail=f"场景 '{scene_name}' 在 '{data_root}' 的任何子目录中都未找到")

    # --- 缓存逻辑 ---
    # 使用确定的、非随机的输出路径，以便查找缓存
    # 不同方法的输出应分开放置，以避免缓存混淆
    output_path = os.path.join(output_root, f"{scene_name}_{method}")
    
    # 1. 检查是否存在已完成的结果
    existing_results = check_and_get_existing_results(output_path, method)
    if existing_results:
        print(f"场景 '{scene_name}' (方法：{method}) 的结果已存在，直接从缓存返回。")
        color_model_path, thermal_model_path, color_rendered_images, thermal_rendered_images = existing_results
        
        # 记录缓存命中日志
        log_audit(
            db=db,
            user_id=current_user.id,
            module="reconstruction",
            action="execute",
            ip_address=get_client_ip(request),
            status="success",
            details=f"场景: {scene_name}, 方法: {method}, 来源: 缓存"
        )
    else:
        # 2. 如果不存在，则执行重建
        print(f"场景 '{scene_name}' (方法：{method}) 的结果不存在，开始新的重建任务。")
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        try:
            print(f"将重建任务添加到线程池：场景 '{scene_name}' (方法：{method})，源路径: '{source_path}'")
            # 调用线程池执行耗时任务
            color_model_path, thermal_model_path, color_rendered_images, thermal_rendered_images = await run_in_threadpool(
                run_reconstruction, 
                source_path=source_path, 
                output_path=output_path,
                method=method
            )
            
            # 记录成功日志
            log_audit(
                db=db,
                user_id=current_user.id,
                module="reconstruction",
                action="execute",
                ip_address=get_client_ip(request),
                status="success",
                details=f"场景: {scene_name}, 方法: {method}, 来源: 新建"
            )
            
        except Exception as e:
            # 记录失败日志
            log_audit(
                db=db,
                user_id=current_user.id,
                module="reconstruction",
                action="execute",
                ip_address=get_client_ip(request),
                status="failed",
                details=f"场景: {scene_name}, 方法: {method}, 错误: {str(e)}"
            )
            
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"重建过程中发生服务器内部错误: {str(e)}")

    # --- 统一处理并返回结果 ---
    def get_url_from_path(path):
        """辅助函数，根据路径生成URL"""
        if not path or not os.path.exists(path) or os.path.isdir(path):
            return None
        relative_path = os.path.relpath(path, os.getcwd())
        return f"/{relative_path.replace(os.path.sep, '/')}"

    color_model_url = get_url_from_path(color_model_path)
    thermal_model_url = get_url_from_path(thermal_model_path)

    # 只要至少有一个模型成功生成，我们就认为操作成功
    if color_model_url or thermal_model_url or color_rendered_images or thermal_rendered_images:
        response_data = {
            "status": "Reconstruction complete",
            "model_url_color": color_model_url,
            "model_url_thermal": thermal_model_url,
            "rendered_images_color": color_rendered_images,
            "rendered_images_thermal": thermal_rendered_images,
            "output_path": output_path
        }
        return JSONResponse(content=response_data)
    else:
        # 如果既没有缓存，重建后也没有任何文件，则报告错误
        detail_msg = "重建任务运行后未生成任何有效文件。请检查终端日志以获取详细错误。"
        raise HTTPException(status_code=500, detail=detail_msg)
