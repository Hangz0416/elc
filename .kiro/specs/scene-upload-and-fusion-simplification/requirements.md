# 需求文档

## 简介

本文档定义了多模态图像融合系统的四项改进需求，旨在提升用户体验和工作流程一致性。主要改进包括：场景资产批量上传功能、融合模块简化、仪表板调整以及专业UI改进。

## 术语表

- **Scene_Asset_Manager**: 场景资产管理器，负责场景创建和图像上传
- **Fusion_Module**: 融合模块，负责RGB和热红外图像融合处理
- **Reconstruction_Module**: 重建模块，负责三维重建处理
- **Dashboard**: 仪表板，系统主页面显示统计信息和快捷操作
- **RGB_Image**: 可见光彩色图像
- **Thermal_Image**: 热红外图像
- **Image_Pair**: 一对配准的RGB图像和热红外图像
- **Scene**: 场景，包含一组相关图像的项目容器
- **Upload_Progress**: 上传进度，显示文件上传的完成百分比
- **Scene_Preview**: 场景预览，显示场景中的图像缩略图

## 需求

### 需求 1: 场景资产批量上传功能

**用户故事:** 作为系统用户，我希望能够创建空场景并批量上传图像到场景中，以便管理和组织我的图像数据。

#### 验收标准

1. THE Scene_Asset_Manager SHALL 提供创建空场景的功能
2. WHEN 用户创建场景时，THE Scene_Asset_Manager SHALL 要求输入场景名称
3. WHEN 场景名称为空时，THE Scene_Asset_Manager SHALL 显示错误提示
4. WHEN 场景名称包含非法字符时，THE Scene_Asset_Manager SHALL 显示错误提示并说明允许的字符规则
5. WHEN 场景创建成功后，THE Scene_Asset_Manager SHALL 在场景列表中显示新创建的场景
6. THE Scene_Asset_Manager SHALL 为每个场景提供批量上传RGB图像的功能
7. THE Scene_Asset_Manager SHALL 为每个场景提供批量上传热红外图像的功能
8. THE Scene_Asset_Manager SHALL 支持通过文件选择器选择多个图像文件
9. THE Scene_Asset_Manager SHALL 支持通过拖拽方式上传多个图像文件
10. WHEN 用户上传图像时，THE Scene_Asset_Manager SHALL 显示上传进度条
11. WHEN 用户上传图像时，THE Scene_Asset_Manager SHALL 显示每个文件的上传状态
12. WHEN 图像上传完成时，THE Scene_Asset_Manager SHALL 显示成功提示信息
13. WHEN 图像上传失败时，THE Scene_Asset_Manager SHALL 显示失败原因
14. THE Scene_Asset_Manager SHALL 支持JPG、PNG和JPEG格式的图像文件
15. WHEN 用户选择不支持的文件格式时，THE Scene_Asset_Manager SHALL 显示格式错误提示
16. THE Scene_Asset_Manager SHALL 在上传完成后更新场景的图像数量统计

### 需求 2: 融合模块简化

**用户故事:** 作为系统用户，我希望融合模块的工作流程与重建模块保持一致，只需选择场景而不是上传图像，以便简化操作流程。

#### 验收标准

1. THE Fusion_Module SHALL 移除RGB图像上传控件
2. THE Fusion_Module SHALL 移除热红外图像上传控件
3. THE Fusion_Module SHALL 提供场景选择下拉框
4. WHEN 融合模块加载时，THE Fusion_Module SHALL 从服务器获取可用场景列表
5. WHEN 场景列表为空时，THE Fusion_Module SHALL 在下拉框中显示提示信息
6. WHEN 用户选择场景时，THE Fusion_Module SHALL 显示该场景的图像预览
7. THE Fusion_Module SHALL 在场景预览中显示RGB图像缩略图
8. THE Fusion_Module SHALL 在场景预览中显示热红外图像缩略图
9. THE Fusion_Module SHALL 在场景预览中显示图像对数量
10. WHEN 场景包含的RGB图像数量与热红外图像数量不匹配时，THE Fusion_Module SHALL 显示警告信息
11. WHEN 场景包含的RGB图像数量与热红外图像数量不匹配时，THE Fusion_Module SHALL 禁用开始融合按钮
12. WHEN 用户选择有效场景后，THE Fusion_Module SHALL 启用开始融合按钮
13. WHEN 用户点击开始融合按钮时，THE Fusion_Module SHALL 使用选定场景的图像进行融合处理
14. THE Fusion_Module SHALL 保持与重建模块相同的用户界面布局风格
15. WHEN 从仪表板或场景详情页跳转到融合模块时，THE Fusion_Module SHALL 支持预选场景参数

### 需求 3: 仪表板快捷操作调整

**用户故事:** 作为系统用户，我希望仪表板的快捷操作能够直接访问场景资产管理页面，以便快速管理场景和上传图像。

#### 验收标准

1. THE Dashboard SHALL 将快捷操作中的"新建场景"按钮文本更改为"场景资产"
2. THE Dashboard SHALL 保持快捷操作按钮的图标和样式不变
3. WHEN 用户点击"场景资产"按钮时，THE Dashboard SHALL 导航到场景资产管理页面
4. THE Dashboard SHALL 保持其他快捷操作按钮不变
5. THE Dashboard SHALL 保持快捷操作区域的布局不变

### 需求 4: 专业UI改进

**用户故事:** 作为系统用户，我希望系统界面更加专业和商务化，以便提升系统的视觉专业度和用户体验。

#### 验收标准

1. THE Scene_Asset_Manager SHALL 使用SVG图标替代emoji图标
2. THE Fusion_Module SHALL 使用SVG图标替代emoji图标
3. THE Reconstruction_Module SHALL 使用SVG图标替代emoji图标
4. THE Dashboard SHALL 使用SVG图标替代emoji图标
5. THE Scene_Asset_Manager SHALL 应用商务化的配色方案
6. THE Fusion_Module SHALL 应用商务化的配色方案
7. THE Reconstruction_Module SHALL 应用商务化的配色方案
8. THE Dashboard SHALL 应用商务化的配色方案
9. THE Scene_Asset_Manager SHALL 使用专业的字体和间距
10. THE Fusion_Module SHALL 使用专业的字体和间距
11. THE Reconstruction_Module SHALL 使用专业的字体和间距
12. THE Dashboard SHALL 使用专业的字体和间距
13. THE Scene_Asset_Manager SHALL 保持界面元素的视觉一致性
14. THE Fusion_Module SHALL 保持界面元素的视觉一致性
15. THE Reconstruction_Module SHALL 保持界面元素的视觉一致性
16. THE Dashboard SHALL 保持界面元素的视觉一致性
