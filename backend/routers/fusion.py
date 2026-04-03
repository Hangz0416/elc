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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fusion", "write"))
):
    """
    接收场景名称，使用场景中的RGB和热成像图像执行批量融合，并返回所有结果。
    
    支持两种模式:
    1. 场景模式: 传入 JSON {"scene_name": "场景名称"}
    2. 文件上传模式: 传入 multipart/form-data (向后兼容)
    
    需要权限: fusion.write (管理员和算法调试员)
    """
    content_type = request.headers.get("content-type", "")
    
    # 场景模式 - 使用JSON
    if "application/json" in content_type:
        try:
            body = await request.json()
            scene_name = body.get("scene_name")
            text_prompt = body.get("text_prompt", "default")
            custom_text = body.get("custom_text")
            
            if not scene_name:
                raise HTTPException(status_code=400, detail="必须提供 scene_name")
            
            # 检查场景目录是否存在
            scene_dir = f"static/uploads/{scene_name}"
            if not os.path.exists(scene_dir):
                raise HTTPException(status_code=404, detail=f"场景 '{scene_name}' 不存在")
            
            # 获取场景中的RGB和热红外图像
            rgb_dir = os.path.join(scene_dir, "rgb")
            thermal_dir = os.path.join(scene_dir, "thermal")
            
            if not os.path.exists(rgb_dir) or not os.path.exists(thermal_dir):
                raise HTTPException(status_code=400, detail=f"场景 '{scene_name}' 缺少图像目录")
            
            # 获取图像文件列表
            rgb_files = sorted([f for f in os.listdir(rgb_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            thermal_files = sorted([f for f in os.listdir(thermal_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            
            if len(rgb_files) == 0 or len(thermal_files) == 0:
                raise HTTPException(status_code=400, detail=f"场景 '{scene_name}' 缺少图像文件")
            
            if len(rgb_files) != len(thermal_files):
                raise HTTPException(status_code=400, detail=f"RGB图像({len(rgb_files)})和热红外图像({len(thermal_files)})数量不匹配")
            
            # 限制每次处理10张图像以避免CUDA内存不足
            max_images = 10
            if len(rgb_files) > max_images:
                print(f"场景包含 {len(rgb_files)} 对图像，限制处理前 {max_images} 对以避免内存不足")
                rgb_files = rgb_files[:max_images]
                thermal_files = thermal_files[:max_images]
            
            # 构建完整路径
            rgb_paths = [os.path.join(rgb_dir, f) for f in rgb_files]
            thermal_paths = [os.path.join(thermal_dir, f) for f in thermal_files]
            original_rgb_filenames = rgb_files
            
            # 根据前端选项生成实际的文本提示
            prompt = get_text_prompt(text_prompt, custom_text)
            print(f"开始场景融合任务: {scene_name}，共 {len(rgb_paths)} 对图像。")
            
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
                
                return JSONResponse(content=results)
                
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
                
        except HTTPException:
            raise
        except Exception as e:
            # 记录失败日志
            log_audit(
                db=db,
                user_id=current_user.id,
                module="fusion",
                action="execute",
                ip_address=get_client_ip(request),
                status="failed",
                details=f"错误: {str(e)}"
            )
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
    
    # 文件上传模式 - 向后兼容
    else:
        form = await request.form()
        rgb_images = form.getlist("rgb_images")
        thermal_images = form.getlist("thermal_images")
        scene_name = form.get("scene_name")
        text_prompt = form.get("text_prompt", "default")
        custom_text = form.get("custom_text")
        
        if not rgb_images or not thermal_images:
            raise HTTPException(status_code=400, detail="必须上传RGB和热红外图像")
        
        if len(rgb_images) != len(thermal_images):
            raise HTTPException(status_code=400, detail="RGB图像和热成像图像的数量必须相同。")
        
        if not scene_name:
            raise HTTPException(status_code=400, detail="必须提供场景名称")
        
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
                
                return JSONResponse(content=results)
                
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

        except HTTPException:
            raise
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
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
        
        finally:
            # 清理所有临时上传的文件
            for path in rgb_paths + thermal_paths:
                if os.path.exists(path):
                    os.remove(path)
