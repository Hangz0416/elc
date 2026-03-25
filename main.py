from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import shutil
import uuid
from typing import Optional, List

# 导入我们重构的融合逻辑
from fusion_logic import setup_fusion_model, run_fusion, get_text_prompt

# 导入新的三维重建逻辑
from reconstruction_logic import run_reconstruction, check_and_get_existing_results

# 导入新的分割逻辑
from segmentation_logic import run_segmentation

from fastapi.concurrency import run_in_threadpool

# 创建一个 FastAPI "实例"
app = FastAPI(
    title="多模态融合驱动的三维重建与智能感知一体化系统后端",
    description="使用FastAPI驱动的多模态融合、三维重建和智能感知API",
    version="1.0.0",
)

# --- 事件处理器 ---
@app.on_event("startup")
async def startup_event():
    """ FastAPI应用启动时执行 """
    print("应用启动，开始加载模型...")
    # 在这里预加载模型，避免每次API调用都重新加载
    setup_fusion_model()


# --- 中间件配置 ---
# 配置CORS（跨源资源共享）
# 这允许你的前端页面（即使从不同源加载）与FastAPI后端通信
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，在开发中很方便。生产环境应设置为你的前端域名。
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# --- 静态文件目录配置 ---
# 确保存放上传和处理结果的目录存在
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/fused", exist_ok=True)
os.makedirs("static/reconstruction", exist_ok=True)
os.makedirs("static/segmentation", exist_ok=True)

# 挂载 "static" 目录，这样任何在 "static" 文件夹下的文件都可以通过 /static/... URL访问
# 例如: static/fused/image.png -> http://localhost:8000/static/fused/image.png
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- API 端点定义 ---

@app.get("/", include_in_schema=False)
async def read_index():
    """
    根路由，提供前端主页面。
    当用户访问 "http://localhost:8000/" 时，返回 src/index.html 文件。
    """
    return FileResponse('src/index.html')


@app.post("/api/fusion")
async def fusion_endpoint(
    rgb_images: List[UploadFile] = File(..., description="一个或多个RGB图像文件"),
    thermal_images: List[UploadFile] = File(..., description="一个或多个热成像图像文件"),
    scene_name: str = Form(..., description="本次融合任务的场景名称 (例如 'Building')"),
    text_prompt: str = Form("default", description="选择的文本引导的Key (对所有图像生效)"),
    custom_text: Optional[str] = Form(None, description="自定义的文本引导")
):
    """
    接收一批RGB和热成像图像，使用 EAEFNet 模型执行批量融合，并返回所有结果。
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
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        return JSONResponse(content=results)

    except HTTPException as e:
        # 如果是已知HTTP异常，直接重新抛出给FastAPI处理
        raise e

    except Exception as e:
        # 打印详细的错误信息到后端控制台
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
    
    finally:
        # 清理所有临时上传的文件
        for path in rgb_paths + thermal_paths:
            if os.path.exists(path):
                os.remove(path)


@app.post("/api/reconstruction")
async def reconstruction_endpoint(
    scene_name: str = Form(..., description="要重建的场景名称 (例如 'Truck')"),
    method: str = Form("MSMG", description="重建方法: MSMG, MFTG, 或 OMMG")
):
    """
    接收场景名称，使用 thermal-gaussian 模型在后台执行三维重建，并返回结果。
    如果结果已存在，则直接返回缓存的结果。
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
        except Exception as e:
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


@app.post("/api/segmentation")
async def segmentation_endpoint(
    scene_name: str = Form(..., description="要执行分割的原始场景名称 (例如 'Building')")
):
    """
    对一个原始场景，执行完整的分割流程：准备mask -> 训练 -> 渲染。
    如果结果已存在，则直接返回缓存的结果。
    """
    # 验证场景是否存在
    source_root = "static/reconstruction_data/RGBT-Scenes"
    scene_path = os.path.join(source_root, scene_name)

    if not os.path.isdir(scene_path):
        raise HTTPException(status_code=404, detail=f"找不到指定的原始场景: '{scene_name}'")

    try:
        print(f"将分割任务添加到线程池：场景 '{scene_name}'")
        
        result_pairs = await run_in_threadpool(
            run_segmentation,
            scene_name=scene_name
        )

        if not result_pairs:
             raise HTTPException(status_code=500, detail="分割任务运行后未生成任何有效文件。请检查终端日志。")

        return JSONResponse(content={
            "status": "Segmentation complete",
            "segmentation_pairs": result_pairs,
            "scene_name": scene_name
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分割过程中发生服务器内部错误: {str(e)}")


@app.get("/api/reconstructed-scenes", summary="获取已完成重建的场景列表")
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


@app.get("/api/scenes", summary="获取可用重建场景列表")
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


# --- 启动服务 ---
if __name__ == "__main__":
    # 这使得你可以通过 `python main.py` 来启动服务
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print("要启动服务, 请在终端运行: uvicorn main:app --reload") 