"""
页面路由（HTML页面）
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)


@router.get("/")
async def read_index():
    """
    根路由，返回新的模块化前端页面。
    当用户访问 "http://localhost:8000/" 时，返回 frontend/pages/index.html 文件。
    """
    return FileResponse('frontend/pages/index.html')


@router.get("/dashboard.html")
async def read_dashboard():
    """
    工作台Dashboard页面路由（兼容旧链接）。
    当用户访问 "http://localhost:8000/dashboard.html" 时，返回新的模块化前端页面。
    """
    return FileResponse('frontend/pages/index.html')


@router.get("/login.html")
async def read_login():
    """
    登录页面路由。
    当用户访问 "http://localhost:8000/login.html" 时，返回 login.html 文件。
    """
    return FileResponse('templates/login.html')


@router.get("/register.html")
async def read_register():
    """
    用户注册页面路由。
    当用户访问 "http://localhost:8000/register.html" 时，返回 register.html 文件。
    """
    return FileResponse('templates/register.html')


@router.get("/admin.html")
async def read_admin():
    """
    系统管理页面路由。
    当用户访问 "http://localhost:8000/admin.html" 时，返回 admin.html 文件。
    """
    return FileResponse('templates/admin.html')


@router.get("/forgot-password.html")
async def read_forgot_password():
    """
    忘记密码页面路由。
    当用户访问 "http://localhost:8000/forgot-password.html" 时，返回 forgot-password.html 文件。
    """
    return FileResponse('templates/forgot-password.html')
