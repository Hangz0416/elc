from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# 导入融合模型设置
from backend.logic.fusion_logic import setup_fusion_model

# 导入数据库初始化
from backend.core.database import init_db, init_roles_and_admin

# 导入路由模块
from backend.routers import auth, pages, fusion, reconstruction, segmentation, scenes, users, roles, logs

# 创建一个 FastAPI "实例"
app = FastAPI(
    title="多模态智能感知系统后端",
    description="基于多模态图像融合的三维重建与智能感知API",
    version="1.0.0",
)

# --- 事件处理器 ---
@app.on_event("startup")
async def startup_event():
    """ FastAPI应用启动时执行 """
    print("应用启动，开始初始化...")
    
    # 初始化数据库
    try:
        init_db()
        init_roles_and_admin()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
    
    # 加载融合模型
    print("开始加载融合模型...")
    setup_fusion_model()
    print("融合模型加载完成")


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

# 挂载 "frontend" 目录，提供前端静态资源（CSS、JS等）
# 例如: frontend/css/main.css -> http://localhost:8000/frontend/css/main.css
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


# --- 注册路由 ---
# 页面路由（HTML页面）
app.include_router(pages.router)

# 认证路由
app.include_router(auth.router)

# 系统管理路由
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(logs.router)

# 业务功能路由
app.include_router(fusion.router)
app.include_router(reconstruction.router)
app.include_router(segmentation.router)
app.include_router(scenes.router)


# --- 启动服务 ---
if __name__ == "__main__":
    print("要启动服务, 请在终端运行: uvicorn main:app --reload") 