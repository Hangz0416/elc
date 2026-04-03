"""
场景管理相关路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
import os
import shutil

router = APIRouter(prefix="/api", tags=["场景管理"])


@router.get("/scenes", summary="获取可用重建场景列表")
async def get_reconstruction_scenes():
    """
    扫描 `static/uploads` 目录，返回所有已导入的场景列表及其详细信息。
    """
    uploads_root = "static/uploads"
    
    if not os.path.isdir(uploads_root):
        os.makedirs(uploads_root, exist_ok=True)
        return JSONResponse(content={"scenes": [], "total": 0})
    
    try:
        scenes = []
        
        for scene_name in os.listdir(uploads_root):
            scene_path = os.path.join(uploads_root, scene_name)
            
            # 跳过文件，只处理目录
            if not os.path.isdir(scene_path):
                continue
            
            # 获取场景信息
            scene_info = {
                "name": scene_name,
                "path": scene_path,
                "rgb_count": 0,
                "thermal_count": 0,
                "fused_count": 0,
                "size_mb": 0,
                "has_colmap": False,
                "created_at": None,
                "updated_at": None
            }
            
            # 统计RGB图像
            rgb_path = os.path.join(scene_path, "rgb")
            if os.path.isdir(rgb_path):
                rgb_images = [f for f in os.listdir(rgb_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                scene_info["rgb_count"] = len(rgb_images)
            
            # 统计热红外图像
            thermal_path = os.path.join(scene_path, "thermal")
            if os.path.isdir(thermal_path):
                thermal_images = [f for f in os.listdir(thermal_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                scene_info["thermal_count"] = len(thermal_images)
            
            # 统计融合图像
            fused_path = os.path.join(scene_path, "fused")
            if os.path.isdir(fused_path):
                fused_images = [f for f in os.listdir(fused_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                scene_info["fused_count"] = len(fused_images)
            
            # 检查COLMAP数据
            colmap_path = os.path.join(scene_path, "colmap")
            scene_info["has_colmap"] = os.path.isdir(colmap_path)
            
            # 计算文件夹大小
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(scene_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            scene_info["size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # 获取创建和修改时间
            import time
            stat_info = os.stat(scene_path)
            scene_info["created_at"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_ctime))
            scene_info["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_mtime))
            
            scenes.append(scene_info)
        
        return JSONResponse(content={
            "scenes": sorted(scenes, key=lambda x: x["name"]),
            "total": len(scenes)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法读取场景目录: {e}")


@router.post("/scenes", summary="创建新场景")
async def create_scene(scene_data: dict):
    """
    创建一个新的场景项目。
    
    参数:
    - name: 场景名称（必填）
    - description: 场景描述（可选）
    - type: 场景类型（可选）
    
    返回:
    - success: 是否成功
    - message: 提示信息
    - scene_name: 场景名称
    - scene_path: 场景路径
    """
    name = scene_data.get("name", "").strip()
    description = scene_data.get("description", "")
    scene_type = scene_data.get("type", "other")
    
    # 验证场景名称
    if not name:
        raise HTTPException(status_code=400, detail="场景名称不能为空")
    
    # 验证场景名称格式（只允许字母、数字、下划线和连字符）
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise HTTPException(status_code=400, detail="场景名称只能包含字母、数字、下划线和连字符")
    
    # 创建场景目录
    uploads_root = "static/uploads"
    os.makedirs(uploads_root, exist_ok=True)
    
    scene_path = os.path.join(uploads_root, name)
    
    # 检查场景是否已存在
    if os.path.exists(scene_path):
        raise HTTPException(status_code=400, detail=f"场景 '{name}' 已存在")
    
    try:
        # 创建场景目录结构
        os.makedirs(os.path.join(scene_path, "rgb"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "thermal"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "fused"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "reconstruction"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "segmentation"), exist_ok=True)
        
        # 创建元数据文件
        import json
        import time
        metadata = {
            "name": name,
            "description": description,
            "type": scene_type,
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "rgb_count": 0,
            "thermal_count": 0,
            "fused_count": 0,
            "has_colmap": False
        }
        
        metadata_path = os.path.join(scene_path, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return JSONResponse(content={
            "success": True,
            "message": f"场景 '{name}' 创建成功",
            "scene_name": name,
            "scene_path": scene_path
        })
        
    except Exception as e:
        # 如果创建失败，清理已创建的目录
        if os.path.exists(scene_path):
            shutil.rmtree(scene_path)
        raise HTTPException(status_code=500, detail=f"创建场景失败: {e}")


@router.get("/reconstructed-scenes", summary="获取已完成重建的场景列表")
async def get_reconstructed_scenes():
    """
    扫描 `static/reconstruction` 目录，返回所有已完成重建的场景列表。
    这些场景可以作为分割任务的输入。
    """
    reconstruction_root = "static/reconstruction"
    if not os.path.isdir(reconstruction_root):
        return JSONResponse(content={"error": f"目录不存在: {reconstruction_root}"}, status_code=404)
    
    try:
        # 列出所有代表已完成重建的文件夹
        reconstructed_scenes = [
            name for name in os.listdir(reconstruction_root) 
            if os.path.isdir(os.path.join(reconstruction_root, name))
        ]
        return JSONResponse(content={"reconstructed_scenes": sorted(reconstructed_scenes)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenes/dataset-scenes", summary="获取数据集中的场景列表")
async def get_dataset_scenes():
    """
    扫描 data/RGBT-Scenes/RGBT-Scenes 目录，返回所有可用的数据集场景。
    这些场景包含预先准备好的RGB和热红外图像对。
    """
    dataset_root = "data/RGBT-Scenes/RGBT-Scenes"
    
    if not os.path.isdir(dataset_root):
        return JSONResponse(content={
            "scenes": [],
            "message": "数据集目录不存在"
        })
    
    try:
        scenes = []
        for scene_name in os.listdir(dataset_root):
            scene_path = os.path.join(dataset_root, scene_name)
            
            # 跳过文件，只处理目录
            if not os.path.isdir(scene_path):
                continue
            
            # 检查场景是否包含必要的文件夹
            rgb_path = os.path.join(scene_path, "rgb", "train")
            thermal_path = os.path.join(scene_path, "thermal", "train")
            
            if os.path.isdir(rgb_path) and os.path.isdir(thermal_path):
                # 统计图像数量
                rgb_images = [f for f in os.listdir(rgb_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                thermal_images = [f for f in os.listdir(thermal_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                
                scenes.append({
                    "name": scene_name,
                    "path": scene_path,
                    "rgb_count": len(rgb_images),
                    "thermal_count": len(thermal_images),
                    "has_colmap": os.path.isdir(os.path.join(scene_path, "colmap"))
                })
        
        return JSONResponse(content={
            "scenes": sorted(scenes, key=lambda x: x["name"]),
            "total": len(scenes)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法读取数据集场景: {e}")


@router.post("/scenes/import-dataset-scene", summary="导入数据集场景")
async def import_dataset_scene(scene_data: dict):
    """
    将数据集中的场景导入到系统中。
    这会在 static/uploads 目录下创建场景文件夹，并复制图像文件。
    
    参数:
    - scene_name: 场景名称
    """
    scene_name = scene_data.get("scene_name")
    
    if not scene_name:
        raise HTTPException(status_code=400, detail="场景名称不能为空")
    
    dataset_root = "data/RGBT-Scenes/RGBT-Scenes"
    source_scene_path = os.path.join(dataset_root, scene_name)
    
    if not os.path.isdir(source_scene_path):
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_name}")
    
    try:
        import shutil
        
        # 创建目标目录
        target_root = "static/uploads"
        os.makedirs(target_root, exist_ok=True)
        
        target_scene_path = os.path.join(target_root, scene_name)
        
        # 如果目标场景已存在，返回提示
        if os.path.exists(target_scene_path):
            return JSONResponse(content={
                "success": True,
                "message": f"场景 {scene_name} 已存在，无需重复导入",
                "scene_name": scene_name,
                "scene_path": target_scene_path
            })
        
        # 创建场景目录结构
        os.makedirs(os.path.join(target_scene_path, "rgb"), exist_ok=True)
        os.makedirs(os.path.join(target_scene_path, "thermal"), exist_ok=True)
        
        # 复制RGB图像
        source_rgb = os.path.join(source_scene_path, "rgb", "train")
        target_rgb = os.path.join(target_scene_path, "rgb")
        if os.path.isdir(source_rgb):
            for img_file in os.listdir(source_rgb):
                if img_file.endswith(('.jpg', '.png', '.jpeg')):
                    shutil.copy2(
                        os.path.join(source_rgb, img_file),
                        os.path.join(target_rgb, img_file)
                    )
        
        # 复制热红外图像
        source_thermal = os.path.join(source_scene_path, "thermal", "train")
        target_thermal = os.path.join(target_scene_path, "thermal")
        if os.path.isdir(source_thermal):
            for img_file in os.listdir(source_thermal):
                if img_file.endswith(('.jpg', '.png', '.jpeg')):
                    shutil.copy2(
                        os.path.join(source_thermal, img_file),
                        os.path.join(target_thermal, img_file)
                    )
        
        # 如果有COLMAP数据，也复制过去
        source_colmap = os.path.join(source_scene_path, "colmap")
        if os.path.isdir(source_colmap):
            target_colmap = os.path.join(target_scene_path, "colmap")
            shutil.copytree(source_colmap, target_colmap)
        
        # 统计导入的图像数量
        rgb_count = len([f for f in os.listdir(target_rgb) if f.endswith(('.jpg', '.png', '.jpeg'))])
        thermal_count = len([f for f in os.listdir(target_thermal) if f.endswith(('.jpg', '.png', '.jpeg'))])
        
        return JSONResponse(content={
            "success": True,
            "message": f"场景 {scene_name} 导入成功",
            "scene_name": scene_name,
            "scene_path": target_scene_path,
            "rgb_count": rgb_count,
            "thermal_count": thermal_count
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入场景失败: {e}")


@router.get("/scenes/{scene_name}/detail", summary="获取场景详细信息")
async def get_scene_detail(scene_name: str):
    """
    获取指定场景的详细信息，包括图像数量、存储大小、处理状态等。
    """
    uploads_root = "static/uploads"
    scene_path = os.path.join(uploads_root, scene_name)
    
    if not os.path.isdir(scene_path):
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_name}")
    
    try:
        # 获取场景信息
        scene_info = {
            "name": scene_name,
            "path": scene_path,
            "rgb_count": 0,
            "thermal_count": 0,
            "fused_count": 0,
            "size_mb": 0,
            "has_colmap": False,
            "created_at": None,
            "updated_at": None
        }
        
        # 统计RGB图像
        rgb_path = os.path.join(scene_path, "rgb")
        if os.path.isdir(rgb_path):
            rgb_images = [f for f in os.listdir(rgb_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            scene_info["rgb_count"] = len(rgb_images)
        
        # 统计热红外图像
        thermal_path = os.path.join(scene_path, "thermal")
        if os.path.isdir(thermal_path):
            thermal_images = [f for f in os.listdir(thermal_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            scene_info["thermal_count"] = len(thermal_images)
        
        # 统计融合图像
        fused_path = os.path.join(scene_path, "fused")
        if os.path.isdir(fused_path):
            fused_images = [f for f in os.listdir(fused_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            scene_info["fused_count"] = len(fused_images)
        
        # 检查COLMAP数据
        colmap_path = os.path.join(scene_path, "colmap")
        scene_info["has_colmap"] = os.path.isdir(colmap_path)
        
        # 计算文件夹大小
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(scene_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        scene_info["size_mb"] = round(total_size / (1024 * 1024), 2)
        
        # 获取创建和修改时间
        import time
        stat_info = os.stat(scene_path)
        scene_info["created_at"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_ctime))
        scene_info["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_mtime))
        
        return JSONResponse(content=scene_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景详情失败: {e}")


@router.get("/scenes/{scene_name}/images", summary="获取场景图像列表")
async def get_scene_images(scene_name: str):
    """
    获取指定场景的RGB和热红外图像列表。
    返回图像文件名和访问路径。
    """
    uploads_root = "static/uploads"
    scene_path = os.path.join(uploads_root, scene_name)
    
    if not os.path.isdir(scene_path):
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_name}")
    
    try:
        rgb_images = []
        thermal_images = []
        
        # 获取RGB图像列表
        rgb_path = os.path.join(scene_path, "rgb")
        if os.path.isdir(rgb_path):
            for filename in sorted(os.listdir(rgb_path)):
                if filename.endswith(('.jpg', '.png', '.jpeg')):
                    rgb_images.append({
                        "filename": filename,
                        "path": f"/static/uploads/{scene_name}/rgb/{filename}"
                    })
        
        # 获取热红外图像列表
        thermal_path = os.path.join(scene_path, "thermal")
        if os.path.isdir(thermal_path):
            for filename in sorted(os.listdir(thermal_path)):
                if filename.endswith(('.jpg', '.png', '.jpeg')):
                    thermal_images.append({
                        "filename": filename,
                        "path": f"/static/uploads/{scene_name}/thermal/{filename}"
                    })
        
        return JSONResponse(content={
            "scene_name": scene_name,
            "rgb_images": rgb_images,
            "thermal_images": thermal_images,
            "rgb_count": len(rgb_images),
            "thermal_count": len(thermal_images)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图像列表失败: {e}")


@router.post("/scenes/{scene_name}/upload", summary="批量上传场景图像")
async def upload_scene_images(
    scene_name: str,
    image_type: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """
    批量上传RGB或热红外图像到指定场景。
    
    参数:
    - scene_name: 场景名称
    - image_type: 图像类型 ("rgb" 或 "thermal")
    - images: 图像文件列表
    
    返回:
    - success: 是否成功
    - uploaded_count: 成功上传的文件数
    - failed_count: 失败的文件数
    - files: 每个文件的上传状态
    """
    # 验证图像类型
    if image_type not in ["rgb", "thermal"]:
        raise HTTPException(status_code=400, detail="图像类型必须是 'rgb' 或 'thermal'")
    
    # 验证场景是否存在
    uploads_root = "static/uploads"
    scene_path = os.path.join(uploads_root, scene_name)
    
    if not os.path.isdir(scene_path):
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_name}")
    
    # 创建图像类型目录
    target_dir = os.path.join(scene_path, image_type)
    os.makedirs(target_dir, exist_ok=True)
    
    # 支持的文件格式
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    
    uploaded_files = []
    uploaded_count = 0
    failed_count = 0
    
    try:
        for image in images:
            file_info = {
                "filename": image.filename,
                "size": 0,
                "status": "success",
                "message": ""
            }
            
            try:
                # 验证文件扩展名
                file_ext = os.path.splitext(image.filename)[1].lower()
                if file_ext not in allowed_extensions:
                    file_info["status"] = "failed"
                    file_info["message"] = f"不支持的文件格式: {file_ext}"
                    failed_count += 1
                    uploaded_files.append(file_info)
                    continue
                
                # 保存文件
                file_path = os.path.join(target_dir, image.filename)
                
                with open(file_path, "wb") as buffer:
                    content = await image.read()
                    buffer.write(content)
                    file_info["size"] = len(content)
                
                uploaded_count += 1
                uploaded_files.append(file_info)
                
            except Exception as e:
                file_info["status"] = "failed"
                file_info["message"] = str(e)
                failed_count += 1
                uploaded_files.append(file_info)
        
        return JSONResponse(content={
            "success": True,
            "uploaded_count": uploaded_count,
            "failed_count": failed_count,
            "scene_name": scene_name,
            "image_type": image_type,
            "files": uploaded_files
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")
