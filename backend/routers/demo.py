"""
演示数据路由 - 提供快速演示功能
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
import os
import glob
import random

from backend.core.database import get_db, User
from backend.core.auth import get_current_user

router = APIRouter(prefix="/api/demo", tags=["演示数据"])

# 本地数据集路径
LOCAL_DATASET_PATH = "data/RGBT-Scenes/RGBT-Scenes"

# 预置演示数据路径（如果本地数据集不存在）
FALLBACK_DEMO_PATH = "static/demo_data"


def get_available_demo_scenes() -> List[Dict]:
    """获取可用的演示场景列表"""
    scenes = []
    
    # 优先检查本地数据集
    if os.path.exists(LOCAL_DATASET_PATH):
        for scene_name in os.listdir(LOCAL_DATASET_PATH):
            scene_path = os.path.join(LOCAL_DATASET_PATH, scene_name)
            if os.path.isdir(scene_path):
                # 检查是否有rgb和thermal目录
                rgb_path = os.path.join(scene_path, "rgb", "train")
                thermal_path = os.path.join(scene_path, "thermal", "train")
                
                if os.path.exists(rgb_path) and os.path.exists(thermal_path):
                    # 统计图像数量
                    rgb_images = glob.glob(os.path.join(rgb_path, "*.jpg")) + \
                                glob.glob(os.path.join(rgb_path, "*.png"))
                    thermal_images = glob.glob(os.path.join(thermal_path, "*.jpg")) + \
                                    glob.glob(os.path.join(thermal_path, "*.png"))
                    
                    if rgb_images and thermal_images:
                        scenes.append({
                            "name": scene_name,
                            "source": "local",
                            "rgb_count": len(rgb_images),
                            "thermal_count": len(thermal_images),
                            "description": f"本地数据集 - {scene_name}"
                        })
    
    # 如果本地数据集不存在或为空，使用预置演示数据
    if not scenes and os.path.exists(FALLBACK_DEMO_PATH):
        for scene_name in os.listdir(FALLBACK_DEMO_PATH):
            scene_path = os.path.join(FALLBACK_DEMO_PATH, scene_name)
            if os.path.isdir(scene_path):
                rgb_path = os.path.join(scene_path, "rgb")
                thermal_path = os.path.join(scene_path, "thermal")
                
                if os.path.exists(rgb_path) and os.path.exists(thermal_path):
                    rgb_images = glob.glob(os.path.join(rgb_path, "*.jpg")) + \
                                glob.glob(os.path.join(rgb_path, "*.png"))
                    thermal_images = glob.glob(os.path.join(thermal_path, "*.jpg")) + \
                                    glob.glob(os.path.join(thermal_path, "*.png"))
                    
                    if rgb_images and thermal_images:
                        scenes.append({
                            "name": scene_name,
                            "source": "builtin",
                            "rgb_count": len(rgb_images),
                            "thermal_count": len(thermal_images),
                            "description": f"内置演示数据 - {scene_name}"
                        })
    
    return scenes


@router.get("/scenes")
async def get_demo_scenes(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的演示场景列表
    """
    try:
        scenes = get_available_demo_scenes()
        
        return {
            "success": True,
            "data": {
                "scenes": scenes,
                "total": len(scenes)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取演示场景失败: {str(e)}")


@router.get("/scenes/{scene_name}/images")
async def get_demo_images(
    scene_name: str,
    count: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    获取指定场景的演示图像列表
    
    参数:
    - scene_name: 场景名称
    - count: 返回的图像对数量（默认3对）
    """
    try:
        # 查找场景路径
        scene_path = None
        source = None
        
        # 优先查找本地数据集
        local_scene_path = os.path.join(LOCAL_DATASET_PATH, scene_name)
        if os.path.exists(local_scene_path):
            rgb_path = os.path.join(local_scene_path, "rgb", "train")
            thermal_path = os.path.join(local_scene_path, "thermal", "train")
            if os.path.exists(rgb_path) and os.path.exists(thermal_path):
                scene_path = local_scene_path
                source = "local"
        
        # 如果本地不存在，查找预置数据
        if not scene_path:
            fallback_scene_path = os.path.join(FALLBACK_DEMO_PATH, scene_name)
            if os.path.exists(fallback_scene_path):
                rgb_path = os.path.join(fallback_scene_path, "rgb")
                thermal_path = os.path.join(fallback_scene_path, "thermal")
                if os.path.exists(rgb_path) and os.path.exists(thermal_path):
                    scene_path = fallback_scene_path
                    source = "builtin"
        
        if not scene_path:
            raise HTTPException(status_code=404, detail=f"场景 '{scene_name}' 不存在")
        
        # 获取图像文件列表
        if source == "local":
            rgb_dir = os.path.join(scene_path, "rgb", "train")
            thermal_dir = os.path.join(scene_path, "thermal", "train")
        else:
            rgb_dir = os.path.join(scene_path, "rgb")
            thermal_dir = os.path.join(scene_path, "thermal")
        
        rgb_images = sorted(glob.glob(os.path.join(rgb_dir, "*.jpg")) + 
                          glob.glob(os.path.join(rgb_dir, "*.png")))
        thermal_images = sorted(glob.glob(os.path.join(thermal_dir, "*.jpg")) + 
                              glob.glob(os.path.join(thermal_dir, "*.png")))
        
        if not rgb_images or not thermal_images:
            raise HTTPException(status_code=404, detail=f"场景 '{scene_name}' 中没有找到图像")
        
        # 随机选择指定数量的图像对
        min_count = min(len(rgb_images), len(thermal_images), count)
        selected_indices = random.sample(range(min(len(rgb_images), len(thermal_images))), min_count)
        
        image_pairs = []
        for idx in selected_indices:
            # 构建相对于static目录的URL路径
            # 将绝对路径转换为相对于项目根目录的路径
            rgb_rel_path = os.path.relpath(rgb_images[idx], ".")
            thermal_rel_path = os.path.relpath(thermal_images[idx], ".")
            
            image_pairs.append({
                "rgb": f"/{rgb_rel_path}",
                "thermal": f"/{thermal_rel_path}",
                "filename": os.path.basename(rgb_images[idx])
            })
        
        return {
            "success": True,
            "data": {
                "scene": scene_name,
                "source": source,
                "image_pairs": image_pairs,
                "total_available": min(len(rgb_images), len(thermal_images))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取演示图像失败: {str(e)}")


@router.get("/images/{scene_name}/{image_type}/{subset}/{filename}")
async def serve_demo_image(
    scene_name: str,
    image_type: str,
    subset: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    提供演示图像文件
    
    参数:
    - scene_name: 场景名称
    - image_type: 图像类型 (rgb/thermal)
    - subset: 数据子集 (train/test)
    - filename: 文件名
    """
    try:
        # 构建文件路径
        file_path = os.path.join(LOCAL_DATASET_PATH, scene_name, image_type, subset, filename)
        
        # 如果本地不存在，尝试预置数据
        if not os.path.exists(file_path):
            file_path = os.path.join(FALLBACK_DEMO_PATH, scene_name, image_type, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="图像文件不存在")
        
        return FileResponse(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图像文件失败: {str(e)}")
