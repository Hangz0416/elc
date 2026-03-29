"""
场景管理相关路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os

router = APIRouter(prefix="/api", tags=["场景管理"])


@router.get("/scenes", summary="获取可用重建场景列表")
async def get_reconstruction_scenes():
    """
    扫描 `static/reconstruction_data` 下的所有子目录，
    返回找到的所有场景文件夹名称作为可用场景列表。
    """
    data_root = "static/reconstruction_data"
    if not os.path.isdir(data_root):
        return JSONResponse(content={"error": f"数据目录不存在: {data_root}"}, status_code=404)
    
    try:
        all_scenes = []
        # 遍历根数据目录下的每个子目录 (例如 'RGBT-Scenes', 'RGBT-Scenes-extend')
        for scene_collection in os.listdir(data_root):
            collection_path = os.path.join(data_root, scene_collection)
            if os.path.isdir(collection_path):
                # 将该集合下的所有子目录（即实际场景）添加到列表中
                scenes_in_collection = [name for name in os.listdir(collection_path) if os.path.isdir(os.path.join(collection_path, name))]
                all_scenes.extend(scenes_in_collection)
        
        # 去重并排序，以防不同集合中有同名场景
        unique_scenes = sorted(list(set(all_scenes)))
        return JSONResponse(content=unique_scenes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法读取场景目录: {e}")


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
