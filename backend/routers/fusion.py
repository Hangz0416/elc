"""
图像融合相关路由
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid

from backend.logic.fusion_logic import run_fusion, get_text_prompt
from backend.core.database import get_db, User
from backend.core.auth import require_permission, log_audit, get_client_ip

router = APIRouter(prefix="/api", tags=["图像融合"])


@router.post("/fusion")
async def fusion_endpoint(
    rgb_images: List[UploadFile] = File(..., description="一个或多个RGB图像文件"),
    thermal_images: List[UploadFile] = File(..., description="一个或多个热成像图像文件"),
    scene_name: str = Form(..., description="本次融合任务的场景名称 (例如 'Building')"),
    text_prompt: str = Form("default", description="选择的文本引导的Key (对所有图像生效)"),
    custom_text: Optional[str] = Form(None, description="自定义的文本引导"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fusion", "write"))
):
    """
    接收一批RGB和热成像图像，使用 EAEFNet 模型执行批量融合，并返回所有结果。
    
    需要权限: fusion.write (管理员和算法调试员)
    """
    if len(rgb_images) != len(thermal_images):
        raise HTTPException(status_code=400, detail="RGB图像和热成像图像的数量必须相同。")
    if not rgb_images:
        raise HTTPException(status_code=400, detail="必须至少上传一对图像。")

    rgb_paths = []
    thermal_paths = []
    original_rgb_filenames = []
    
    try:
        # 临时保存所有上传的图像
        for rgb_image, thermal_image in zip(rgb_images, thermal_images):
            # 为保证文件名唯一，使用UUID作为前缀
            rgb_path = f"static/uploads/{uuid.uuid4()}_{rgb_image.filename}"
            thermal_path = f"static/uploads/{uuid.uuid4()}_{thermal_image.filename}"
            
            with open(rgb_path, "wb") as buffer:
                shutil.copyfileobj(rgb_image.file, buffer)
            
            with open(thermal_path, "wb") as buffer:
                shutil.copyfileobj(thermal_image.file, buffer)
            
            rgb_paths.append(rgb_path)
            thermal_paths.append(thermal_path)
            original_rgb_filenames.append(rgb_image.filename)

        # 根据前端选项生成实际的文本提示
        prompt = get_text_prompt(text_prompt, custom_text)
        print(f"开始批量融合任务，共 {len(rgb_paths)} 对图像。")

        # 调用核心批量融合函数
        try:
            results = run_fusion(
                rgb_paths=rgb_paths,
                thermal_paths=thermal_paths,
                text_prompt=prompt,
                scene_name=scene_name,
                original_rgb_filenames=original_rgb_filenames
            )
            
            # 记录成功日志
            log_audit(
                db=db,
                user_id=current_user.id,
                module="fusion",
                action="execute",
                ip_address=get_client_ip(request),
                status="success",
                details=f"场景: {scene_name}, 图像数: {len(rgb_paths)}"
            )
            
        except FileNotFoundError as e:
            # 记录失败日志
            log_audit(
                db=db,
                user_id=current_user.id,
                module="fusion",
                action="execute",
                ip_address=get_client_ip(request),
                status="failed",
                details=f"场景: {scene_name}, 错误: {str(e)}"
            )
            raise HTTPException(status_code=404, detail=str(e))
        
        return JSONResponse(content=results)

    except HTTPException as e:
        # 如果是已知HTTP异常，直接重新抛出给FastAPI处理
        raise e

    except Exception as e:
        # 记录失败日志
        log_audit(
            db=db,
            user_id=current_user.id,
            module="fusion",
            action="execute",
            ip_address=get_client_ip(request),
            status="failed",
            details=f"场景: {scene_name}, 错误: {str(e)}"
        )
        
        # 打印详细的错误信息到后端控制台
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
    
    finally:
        # 清理所有临时上传的文件
        for path in rgb_paths + thermal_paths:
            if os.path.exists(path):
                os.remove(path)
