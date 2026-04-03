# 技术设计文档

## 简介

本文档定义了多模态图像融合系统四项改进功能的技术设计方案。这些改进旨在提升用户体验、统一工作流程并增强系统的专业性。主要包括：场景资产批量上传功能、融合模块简化、仪表板快捷操作调整以及专业UI改进。

## 概述

### 设计目标

1. 在场景详情页面添加批量上传功能，支持RGB和热红外图像的批量上传
2. 简化融合模块的用户界面，采用场景选择模式替代图像上传
3. 调整仪表板快捷操作，将"新建场景"改为"场景资产"
4. 使用SVG图标和商务化配色方案提升UI专业度

### 设计原则

- 保持与现有系统的一致性
- 最小化代码改动，复用现有组件
- 确保向后兼容性
- 提供清晰的用户反馈

### 技术栈

- 前端：原生JavaScript (ES6+)
- 后端：Python FastAPI
- 文件存储：本地文件系统
- API通信：RESTful API with JWT认证

## 架构

### 系统架构图

```mermaid
graph TB
    subgraph "前端层"
        A[场景资产页面] --> B[场景详情模态框]
        B --> C[批量上传组件]
        D[融合模块] --> E[场景选择器]
        E --> F[图像预览组件]
        G[仪表板] --> H[快捷操作按钮]
    end
    
    subgraph "API层"
        I[/api/scenes POST]
        J[/api/scenes/:name/upload]
        K[/api/scenes/:name/images]
        L[/api/fusion POST]
    end
    
    subgraph "后端层"
        M[场景管理服务]
        N[文件上传服务]
        O[图像融合服务]
    end
    
    subgraph "存储层"
        P[(文件系统)]
        Q[static/uploads/:scene/rgb]
        R[static/uploads/:scene/thermal]
    end
    
    C --> J
    E --> K
    D --> L
    I --> M
    J --> N
    K --> M
    L --> O
    M --> P
    N --> Q
    N --> R
    O --> P
```

### 数据流

1. **场景创建流程**
   - 用户输入场景名称 → 前端验证 → POST /api/scenes → 创建目录结构 → 返回场景信息

2. **批量上传流程**
   - 用户选择文件 → 前端预览 → POST /api/scenes/:name/upload → 保存文件 → 更新场景统计

3. **融合简化流程**
   - 加载场景列表 → 用户选择场景 → GET /api/scenes/:name/images → 显示预览 → 开始融合

## 组件和接口

### 前端组件

#### 1. 场景详情模态框增强 (SceneDetailModal)

**位置**: `frontend/js/modules/scenes.js`

**新增功能**:
- 批量上传RGB图像区域
- 批量上传热红外图像区域
- 上传进度显示
- 文件拖拽支持

**接口**:
```javascript
// 显示场景详情并支持上传
async function showSceneDetail(sceneName)

// 处理文件上传
async function uploadSceneImages(sceneName, imageType, files)

// 更新上传进度
function updateUploadProgress(percentage)
```

#### 2. 融合模块简化 (FusionModule)

**位置**: `frontend/js/modules/fusion.js`

**修改内容**:
- 移除RGB和热红外图像上传控件
- 添加场景选择下拉框
- 添加场景图像预览区域
- 保持融合处理逻辑不变

**接口**:
```javascript
// 加载融合页面（支持预选场景）
export async function loadFusionContent(params = {})

// 加载场景列表到下拉框
async function loadScenesForFusion()

// 加载选定场景的图像
async function loadSceneImages(sceneName)

// 显示场景图像预览
function displayScenePreview(rgbImages, thermalImages)
```

#### 3. 仪表板快捷操作 (Dashboard)

**位置**: `frontend/js/modules/dashboard.js`

**修改内容**:
- 将"新建场景"按钮文本改为"场景资产"
- 保持导航目标为scenes页面

### 后端API

#### 1. 创建场景 (已存在，需增强)

**端点**: `POST /api/scenes`

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "type": "indoor|outdoor|industrial|other"
}
```

**响应**:
```json
{
  "success": true,
  "message": "场景创建成功",
  "scene_name": "string",
  "scene_path": "string"
}
```

#### 2. 批量上传场景图像 (新增)

**端点**: `POST /api/scenes/{scene_name}/upload`

**请求**: multipart/form-data
- `image_type`: "rgb" | "thermal"
- `images`: File[] (多个图像文件)

**响应**:
```json
{
  "success": true,
  "uploaded_count": 10,
  "failed_count": 0,
  "scene_name": "string",
  "image_type": "rgb",
  "files": [
    {
      "filename": "string",
      "size": 1024,
      "status": "success"
    }
  ]
}
```

#### 3. 获取场景图像列表 (已存在)

**端点**: `GET /api/scenes/{scene_name}/images`

**响应**:
```json
{
  "scene_name": "string",
  "rgb_images": [
    {
      "filename": "string",
      "path": "/static/uploads/scene/rgb/image.jpg"
    }
  ],
  "thermal_images": [
    {
      "filename": "string",
      "path": "/static/uploads/scene/thermal/image.jpg"
    }
  ],
  "rgb_count": 10,
  "thermal_count": 10
}
```

## 数据模型

### 场景目录结构

```
static/uploads/
└── {scene_name}/
    ├── rgb/              # RGB图像目录
    │   ├── image001.jpg
    │   ├── image002.jpg
    │   └── ...
    ├── thermal/          # 热红外图像目录
    │   ├── image001.jpg
    │   ├── image002.jpg
    │   └── ...
    ├── fused/           # 融合结果目录
    ├── reconstruction/  # 重建结果目录
    ├── segmentation/    # 分割结果目录
    └── metadata.json    # 场景元数据
```

### 场景元数据 (metadata.json)

```json
{
  "name": "string",
  "description": "string",
  "type": "indoor|outdoor|industrial|other",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "rgb_count": 0,
  "thermal_count": 0,
  "fused_count": 0,
  "has_colmap": false
}
```

### 上传进度状态

```javascript
{
  total: number,        // 总文件数
  uploaded: number,     // 已上传数
  failed: number,       // 失败数
  percentage: number,   // 完成百分比
  currentFile: string   // 当前文件名
}
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 场景名称验证

*对于任何*包含非法字符（非字母、数字、下划线、连字符）的场景名称，系统应拒绝创建并显示错误提示

**验证需求: 1.4**

### 属性 2: 场景创建后可见性

*对于任何*成功创建的场景，该场景应立即出现在场景列表中

**验证需求: 1.5**

### 属性 3: 批量上传功能可用性

*对于任何*场景，场景详情页应同时提供RGB和热红外图像的批量上传功能

**验证需求: 1.6, 1.7**

### 属性 4: 上传状态显示

*对于任何*批量上传操作中的每个文件，系统应显示该文件的上传状态（成功/失败/进行中）

**验证需求: 1.11**

### 属性 5: 文件格式验证

*对于任何*JPG、PNG或JPEG格式的图像文件，系统应接受上传；对于其他格式，应拒绝并显示错误提示

**验证需求: 1.14, 1.15**

### 属性 6: 上传后统计更新

*对于任何*场景，上传图像后，场景的图像数量统计应准确反映实际文件数量

**验证需求: 1.16**

### 属性 7: 场景选择触发预览

*对于任何*在融合模块中选择的场景，系统应显示该场景的图像预览

**验证需求: 2.6**

### 属性 8: 预览内容完整性

*对于任何*场景预览，应同时显示RGB图像缩略图、热红外图像缩略图和图像对数量

**验证需求: 2.7, 2.8, 2.9**

### 属性 9: 图像数量不匹配处理

*对于任何*RGB和热红外图像数量不匹配的场景，系统应显示警告信息并禁用开始融合按钮

**验证需求: 2.10, 2.11**

### 属性 10: 有效场景启用融合

*对于任何*RGB和热红外图像数量匹配的场景，选择后应启用开始融合按钮

**验证需求: 2.12**

### 属性 11: 融合使用正确数据源

*对于任何*开始融合操作，系统应使用当前选定场景的图像进行融合处理

**验证需求: 2.13**

### 属性 12: SVG图标使用

*对于任何*模块（场景资产、融合、重建、仪表板），应使用SVG图标而非emoji文本

**验证需求: 4.1, 4.2, 4.3, 4.4**

## 错误处理

### 场景创建错误

1. **场景名称为空**
   - 错误码: SCENE_NAME_EMPTY
   - 处理: 显示提示"请输入场景名称"
   - 用户操作: 输入有效名称后重试

2. **场景名称包含非法字符**
   - 错误码: SCENE_NAME_INVALID
   - 处理: 显示提示"场景名称只能包含字母、数字、下划线和连字符"
   - 用户操作: 修改名称后重试

3. **场景已存在**
   - 错误码: SCENE_ALREADY_EXISTS
   - 处理: 显示提示"场景名称已存在，请使用其他名称"
   - 用户操作: 更改名称后重试

4. **文件系统错误**
   - 错误码: FILESYSTEM_ERROR
   - 处理: 显示提示"创建场景失败，请检查磁盘空间"
   - 用户操作: 检查系统状态后重试

### 文件上传错误

1. **文件格式不支持**
   - 错误码: UNSUPPORTED_FORMAT
   - 处理: 显示提示"仅支持JPG、PNG、JPEG格式"
   - 用户操作: 选择正确格式的文件

2. **文件大小超限**
   - 错误码: FILE_TOO_LARGE
   - 处理: 显示提示"文件大小不能超过10MB"
   - 用户操作: 压缩图像或选择其他文件

3. **网络传输失败**
   - 错误码: UPLOAD_NETWORK_ERROR
   - 处理: 显示提示"上传失败，请检查网络连接"
   - 用户操作: 检查网络后重试

4. **服务器存储失败**
   - 错误码: UPLOAD_STORAGE_ERROR
   - 处理: 显示提示"保存文件失败，请联系管理员"
   - 用户操作: 联系技术支持

### 融合模块错误

1. **场景不存在**
   - 错误码: SCENE_NOT_FOUND
   - 处理: 显示提示"场景不存在或已被删除"
   - 用户操作: 刷新场景列表并重新选择

2. **图像数量不匹配**
   - 错误码: IMAGE_COUNT_MISMATCH
   - 处理: 显示警告"RGB和热红外图像数量不匹配，无法进行融合"
   - 用户操作: 上传缺失的图像使数量匹配

3. **场景无图像**
   - 错误码: SCENE_EMPTY
   - 处理: 显示提示"该场景没有可用的图像数据"
   - 用户操作: 先上传图像到场景

4. **加载图像失败**
   - 错误码: IMAGE_LOAD_ERROR
   - 处理: 显示提示"加载场景图像失败"
   - 用户操作: 刷新页面或重新选择场景

### 错误处理原则

1. **用户友好**: 所有错误信息使用中文，清晰说明问题和解决方案
2. **非阻塞**: 单个文件上传失败不应阻止其他文件继续上传
3. **可恢复**: 提供明确的恢复路径，允许用户重试操作
4. **日志记录**: 所有错误应记录到控制台，便于调试
5. **状态保持**: 错误发生后保持用户已输入的数据，避免重复输入

## 测试策略

### 测试方法

本项目采用双重测试策略：

1. **单元测试**: 验证具体示例、边界情况和错误条件
2. **属性测试**: 验证跨所有输入的通用属性

两者互补，共同确保全面覆盖。单元测试捕获具体错误，属性测试验证一般正确性。

### 单元测试重点

单元测试应专注于：
- 具体示例（如创建名为"Building"的场景）
- 组件间集成点（如API调用和响应处理）
- 边界情况（空输入、特殊字符、大文件）
- 错误条件（网络失败、权限错误）

避免编写过多单元测试——属性测试已处理大量输入覆盖。

### 属性测试配置

**测试库选择**: 
- JavaScript: fast-check
- Python: Hypothesis

**配置要求**:
- 每个属性测试最少100次迭代
- 每个测试必须引用设计文档中的属性
- 标签格式: `Feature: scene-upload-and-fusion-simplification, Property {number}: {property_text}`

### 测试用例

#### 功能1: 场景资产批量上传

**单元测试**:
1. 测试创建场景模态框显示
2. 测试空场景名称验证
3. 测试特殊字符场景名称验证（如"test@scene"）
4. 测试文件选择器multiple属性
5. 测试拖拽事件监听器
6. 测试上传进度条显示
7. 测试上传成功提示
8. 测试上传失败提示
9. 测试支持的文件格式（.jpg, .png, .jpeg）
10. 测试不支持的文件格式（.txt, .pdf）

**属性测试**:
- 属性1: 场景名称验证
- 属性2: 场景创建后可见性
- 属性3: 批量上传功能可用性
- 属性4: 上传状态显示
- 属性5: 文件格式验证
- 属性6: 上传后统计更新

#### 功能2: 融合模块简化

**单元测试**:
1. 测试RGB上传控件已移除
2. 测试热红外上传控件已移除
3. 测试场景选择下拉框存在
4. 测试模块加载时获取场景列表
5. 测试空场景列表提示
6. 测试预选场景参数处理

**属性测试**:
- 属性7: 场景选择触发预览
- 属性8: 预览内容完整性
- 属性9: 图像数量不匹配处理
- 属性10: 有效场景启用融合
- 属性11: 融合使用正确数据源

#### 功能3: 仪表板快捷操作

**单元测试**:
1. 测试按钮文本为"场景资产"
2. 测试按钮点击导航到scenes页面
3. 测试其他按钮未被修改

#### 功能4: 专业UI改进

**单元测试**:
1. 测试场景资产页面使用SVG图标
2. 测试融合模块使用SVG图标
3. 测试重建模块使用SVG图标
4. 测试仪表板使用SVG图标

**属性测试**:
- 属性12: SVG图标使用

### 测试环境

**前端测试**:
- 测试框架: Jest
- DOM模拟: jsdom
- 属性测试: fast-check
- 覆盖率目标: 80%以上

**后端测试**:
- 测试框架: pytest
- 属性测试: Hypothesis
- API测试: TestClient (FastAPI)
- 覆盖率目标: 85%以上

**集成测试**:
- E2E框架: Playwright
- 测试场景: 完整用户工作流
- 浏览器: Chrome, Firefox

### 测试数据

**场景名称测试数据**:
- 有效: "Building", "Factory_01", "warehouse-2024"
- 无效: "test scene", "场景@123", "scene#1", ""

**图像文件测试数据**:
- 有效格式: .jpg, .png, .jpeg
- 无效格式: .txt, .pdf, .doc, .gif
- 大小范围: 1KB - 15MB

**场景状态测试数据**:
- 空场景（无图像）
- 部分场景（仅RGB或仅热红外）
- 完整场景（RGB和热红外数量相等）
- 不匹配场景（RGB和热红外数量不等）

