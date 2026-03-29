# 前端模块化结构说明

## 目录结构

```
frontend/
├── css/                    # 样式文件
│   ├── main.css           # 主样式（布局、导航等）
│   ├── components.css     # 组件样式（卡片、按钮等）
│   └── modules.css        # 模块样式（融合、重建、分割等）
├── js/                     # JavaScript文件
│   ├── app.js             # 主应用入口
│   └── modules/           # 功能模块
│       ├── core.js        # 核心模块（全局变量、工具函数）
│       ├── auth.js        # 认证模块
│       ├── navigation.js  # 导航模块
│       ├── dashboard.js   # 工作台模块
│       ├── scenes.js      # 场景资产模块
│       ├── fusion.js      # 图像融合模块
│       ├── reconstruction.js  # 三维重建模块
│       ├── segmentation.js    # 场景分割模块
│       ├── reports.js     # 报告中心模块
│       └── admin.js       # 系统管理模块
└── pages/                  # HTML页面
    └── index.html         # 主页面

```

## 模块说明

### 核心模块 (core.js)
- 全局变量管理（token, currentUser）
- 工具函数（updateTime, logout等）
- 提供给其他模块使用的基础功能

### 认证模块 (auth.js)
- 用户登录验证
- 获取用户信息
- 更新用户界面显示

### 导航模块 (navigation.js)
- 页面导航控制
- 路由管理
- 菜单激活状态管理

### 功能模块
每个功能模块负责一个独立的业务功能：
- **dashboard.js**: 工作台首页，显示KPI和快捷操作
- **scenes.js**: 场景资产管理，包括创建、查看、编辑场景
- **fusion.js**: 图像融合功能
- **reconstruction.js**: 三维重建功能
- **segmentation.js**: 场景分割功能
- **reports.js**: 报告中心
- **admin.js**: 系统管理（用户、角色、日志等）

## 使用方式

### 1. 在FastAPI中配置静态文件路由

在 `main.py` 中添加：

```python
from fastapi.staticfiles import StaticFiles

# 挂载前端静态文件
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
```

### 2. 访问应用

访问 `http://localhost:8000/frontend/pages/index.html`

### 3. 开发新模块

1. 在 `frontend/js/modules/` 创建新模块文件
2. 导出需要的函数
3. 在 `navigation.js` 中导入并注册路由
4. 在 `index.html` 中添加导航菜单项（如需要）

## 模块间通信

模块间通过导入导出进行通信：

```javascript
// 在模块A中导出
export function myFunction() {
    // ...
}

// 在模块B中导入
import { myFunction } from './moduleA.js';
```

## 全局函数

某些函数需要在HTML中直接调用，这些函数会挂载到 `window` 对象：

```javascript
// 在模块中
window.myGlobalFunction = function() {
    // ...
}

// 在HTML中
<button onclick="myGlobalFunction()">点击</button>
```

## 待完成工作

以下模块需要从原 `dashboard.html` 中提取完整代码：

- [ ] fusion.js - 图像融合完整功能
- [ ] reconstruction.js - 三维重建完整功能（包括Three.js集成）
- [ ] segmentation.js - 场景分割完整功能
- [ ] admin.js - 系统管理完整功能（用户、角色、日志管理）

## 优势

1. **模块化**: 每个功能独立，易于维护
2. **可复用**: 模块可以在不同页面中复用
3. **易测试**: 独立模块便于单元测试
4. **团队协作**: 不同开发者可以并行开发不同模块
5. **按需加载**: 可以实现代码分割和懒加载
6. **清晰结构**: 代码组织清晰，易于理解和扩展
