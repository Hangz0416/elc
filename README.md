# 多模态智能感知系统

## 项目简介

本系统是一个基于多模态图像融合的三维重建与智能感知平台，支持RGB与热红外图像的智能融合、高保真三维场景重建和语义分割功能。

## 技术栈

- **后端**: FastAPI (Python 3.8+), SQLAlchemy, PyTorch
- **前端**: 原生JavaScript (ES6 Modules), Three.js
- **数据库**: MySQL 8.0+
- **认证**: JWT Token, bcrypt
- **深度学习**: EAEFNet, 3D Gaussian Splatting

## 项目结构

```
.
├── backend/              # 后端代码（模块化架构）
│   ├── core/            # 核心模块
│   │   ├── auth.py      # 认证与授权
│   │   ├── database.py  # 数据库配置与模型
│   │   └── schemas.py   # Pydantic数据模型
│   ├── logic/           # 业务逻辑
│   │   ├── fusion_logic.py        # 图像融合逻辑
│   │   ├── reconstruction_logic.py # 三维重建逻辑
│   │   └── segmentation_logic.py   # 场景分割逻辑
│   ├── routers/         # API路由
│   │   ├── auth.py      # 认证路由
│   │   ├── fusion.py    # 融合路由
│   │   ├── reconstruction.py # 重建路由
│   │   ├── segmentation.py   # 分割路由
│   │   ├── scenes.py    # 场景管理路由
│   │   ├── users.py     # 用户管理路由
│   │   ├── roles.py     # 角色管理路由
│   │   ├── logs.py      # 日志审计路由
│   │   └── pages.py     # 页面路由
│   └── utils/           # 工具函数
│       └── init_db.py   # 数据库初始化脚本
├── frontend/            # 前端资源（模块化架构）
│   ├── css/            # 样式文件
│   ├── js/             # JavaScript模块
│   ├── pages/          # HTML页面
│   ├── README.md       # 前端说明文档
│   ├── QUICKSTART.md   # 快速开始指南
│   └── MIGRATION_GUIDE.md # 迁移指南
├── templates/          # HTML模板文件
│   ├── login.html      # 登录页面
│   ├── register.html   # 注册页面
│   ├── admin.html      # 管理页面（旧版）
│   └── dashboard.html  # 工作台页面（旧版，已迁移）
├── docs/               # 项目文档
├── data/               # 数据集（RGBT-Scenes）
├── src/                # 第三方源代码
├── static/             # 静态文件（上传、处理结果）
├── main.py            # FastAPI主程序
└── requirements.txt   # Python依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

系统使用MySQL数据库，默认配置：
- 主机: localhost:3306
- 用户: root
- 密码: root
- 数据库: multimodal_system

如需修改，请编辑 `database.py` 或设置环境变量。

### 3. 初始化数据库

```bash
python backend/utils/init_db.py
```

这将创建数据库表并初始化默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

### 4. 启动服务

```bash
python main.py
# 或
uvicorn main:app --reload
```

### 5. 访问应用

- 前端页面: `http://localhost:8000/`
- 登录页面: `http://localhost:8000/login.html`
- API文档: `http://localhost:8000/docs`

## 功能模块

### ✅ 已完成
- 用户认证与权限管理
- 工作台Dashboard
- 场景资产管理
- 图像融合（后端）
- 三维重建（后端）
- 场景分割（后端）

### ⏳ 开发中
- 图像融合（前端模块）
- 三维重建（前端模块）
- 场景分割（前端模块）
- 报告中心
- 系统管理（前端模块）

## 前端开发

前端采用模块化架构，详细说明请查看：
- `frontend/README.md` - 前端架构说明
- `frontend/QUICKSTART.md` - 快速开始指南
- `frontend/MIGRATION_GUIDE.md` - 模块迁移指南

## API端点

### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/profile` - 获取用户信息
- `POST /api/auth/logout` - 用户登出

### 业务功能
- `POST /api/fusion` - 图像融合
- `POST /api/reconstruction` - 三维重建
- `POST /api/segmentation` - 场景分割
- `GET /api/scenes` - 获取场景列表
- `GET /api/reconstructed-scenes` - 获取已重建场景

## 角色权限

系统预定义4个角色：

| 角色 | 权限 |
|------|------|
| 管理员 (admin) | 所有权限 |
| 算法调试员 (algorithm_engineer) | 融合/重建/分割读写，报告只读 |
| 现场巡检员 (inspector) | 场景读写，报告只读 |
| 数据审计员 (auditor) | 报告和日志只读 |

## 数据集

项目使用RGBT-Scenes数据集，包含多个场景的RGB和热红外图像对：
- RGBT-Scenes: 9个基础场景
- RGBT-Scenes-extend: 4个扩展场景

## 环境变量

可选的环境变量配置：

```bash
export MYSQL_USER=root
export MYSQL_PASSWORD=root
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=multimodal_system
export SECRET_KEY=your-secret-key-here
```

## 安全建议

⚠️ **生产环境部署前请务必**：
1. 修改默认管理员密码
2. 设置强密码的SECRET_KEY环境变量
3. 使用HTTPS
4. 限制CORS允许的域名
5. 配置防火墙规则
6. 定期备份数据库

## 文档

详细文档请参考：
- `docs/需求文档.md` - 功能需求文档
- `docs/技术文档.md` - 技术实现文档
- `docs/API文档.md` - API接口文档
- `使用说明.md` - 系统使用说明
- `软著文本.md` - 软件著作权文档

## 许可证

[待添加]

## 联系方式

[待添加]
