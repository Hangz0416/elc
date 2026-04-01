/**
 * Image Fusion Module
 * Handles RGB and thermal image fusion functionality
 */

import { getToken } from './core.js';

/**
 * Load and display the fusion page content
 * @param {Object} params - Optional parameters, e.g., { scene: 'sceneName' }
 */
export async function loadFusionContent(params = {}) {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>🔀</span>
                <span>图像融合</span>
            </div>
            
            ${params.scene ? `
            <div style="background: #e6f7ff; border-left: 4px solid #1890ff; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
                <p style="margin: 0; color: #0050b3; font-size: 14px;">
                    📦 正在处理场景: <strong>${params.scene}</strong>
                </p>
            </div>
            ` : ''}
            
            <!-- 图像上传区 -->
            <div class="upload-section">
                <div class="upload-box" id="fusionRgbBox">
                    <div class="upload-icon">📷</div>
                    <div class="upload-text">上传RGB图像</div>
                    <div class="upload-hint">支持多选, JPG, PNG 格式</div>
                    <input type="file" id="fusionRgbInput" class="file-input" accept="image/*" multiple>
                    <div id="fusionRgbPreview" class="image-preview"></div>
                </div>
                
                <div class="upload-box" id="fusionThermalBox">
                    <div class="upload-icon">🌡️</div>
                    <div class="upload-text">上传热成像图像</div>
                    <div class="upload-hint">支持多选, JPG, PNG 格式</div>
                    <input type="file" id="fusionThermalInput" class="file-input" accept="image/*" multiple>
                    <div id="fusionThermalPreview" class="image-preview"></div>
                </div>
            </div>

            <!-- 场景选择 -->
            <div class="process-section">
                <h3>场景选择</h3>
                <select id="fusionSceneSelect">
                    <option value="">--请选择一个场景以存放融合数据--</option>
                </select>
                <button class="btn-process" id="fusionBtn" disabled>开始图像融合</button>
                <div class="progress-bar" id="fusionProgressBar">
                    <div class="progress-fill" id="fusionProgressFill"></div>
                </div>
            </div>

            <!-- 融合结果 -->
            <div class="result-panel" id="fusionResults">
                <div class="result-title">🔀 图像融合结果</div>
                <div class="result-grid" id="fusionResultGrid"></div>
            </div>
        </div>
    `;

    await initFusionModule(params);
}

/**
 * Initialize fusion module event listeners and load scenes
 * @param {Object} params - Optional parameters, e.g., { scene: 'sceneName' }
 */
async function initFusionModule(params = {}) {
    const rgbInput = document.getElementById('fusionRgbInput');
    const thermalInput = document.getElementById('fusionThermalInput');
    const rgbBox = document.getElementById('fusionRgbBox');
    const thermalBox = document.getElementById('fusionThermalBox');
    const fusionBtn = document.getElementById('fusionBtn');
    const sceneSelect = document.getElementById('fusionSceneSelect');

    // 先加载场景列表
    await loadScenesForFusion();

    // Click upload boxes
    rgbBox.addEventListener('click', (e) => {
        if (e.target !== rgbInput) rgbInput.click();
    });
    thermalBox.addEventListener('click', (e) => {
        if (e.target !== thermalInput) thermalInput.click();
    });

    // File selection
    rgbInput.addEventListener('change', () => handleFusionFileSelection(rgbInput, 'fusionRgbPreview'));
    thermalInput.addEventListener('change', () => handleFusionFileSelection(thermalInput, 'fusionThermalPreview'));

    // Drag and drop
    setupDragDrop(rgbBox, rgbInput, 'fusionRgbPreview');
    setupDragDrop(thermalBox, thermalInput, 'fusionThermalPreview');

    // Scene selection change
    sceneSelect.addEventListener('change', checkFusionReady);

    // Start fusion
    fusionBtn.addEventListener('click', startFusion);
    
    // 如果传入了场景参数，自动加载该场景的图像
    if (params.scene) {
        // 延迟一下确保DOM完全准备好
        setTimeout(() => {
            loadSceneImages(params.scene);
        }, 100);
    }
}

/**
 * Load available scenes for fusion
 */
async function loadScenesForFusion() {
    try {
        const token = getToken();
        const response = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('无法获取场景列表');
        
        const data = await response.json();
        const scenes = data.scenes || [];
        
        const select = document.getElementById('fusionSceneSelect');
        select.innerHTML = '<option value="">--请选择一个场景以存放融合数据--</option>';
        
        scenes.forEach(scene => {
            const option = document.createElement('option');
            option.value = scene.name;
            option.textContent = scene.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载场景失败:', error);
    }
}

/**
 * Load images from a specific scene
 * @param {string} sceneName - The name of the scene to load images from
 */
async function loadSceneImages(sceneName) {
    console.log('开始加载场景图像:', sceneName);
    
    try {
        const token = getToken();
        
        // 显示加载提示
        const rgbPreview = document.getElementById('fusionRgbPreview');
        const thermalPreview = document.getElementById('fusionThermalPreview');
        
        if (!rgbPreview || !thermalPreview) {
            console.error('预览容器未找到');
            return;
        }
        
        rgbPreview.innerHTML = '<p style="text-align: center; padding: 20px; color: #999;">加载场景图像中...</p>';
        thermalPreview.innerHTML = '<p style="text-align: center; padding: 20px; color: #999;">加载场景图像中...</p>';
        
        // 获取场景图像列表
        console.log('请求场景图像列表...');
        const response = await fetch(`/api/scenes/${sceneName}/images`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API响应错误:', response.status, errorText);
            throw new Error('无法获取场景图像');
        }
        
        const data = await response.json();
        console.log('获取到的图像数据:', data);
        
        const rgbImages = data.rgb_images || [];
        const thermalImages = data.thermal_images || [];
        
        console.log(`RGB图像数量: ${rgbImages.length}, 热红外图像数量: ${thermalImages.length}`);
        
        if (rgbImages.length === 0 || thermalImages.length === 0) {
            alert('该场景没有可用的图像数据');
            rgbPreview.innerHTML = '';
            thermalPreview.innerHTML = '';
            return;
        }
        
        console.log('开始下载并转换图像...');
        
        // 限制数量避免过多
        const maxImages = Math.min(rgbImages.length, thermalImages.length, 10);
        
        // 下载并转换图像为File对象
        const rgbFiles = [];
        const thermalFiles = [];
        
        for (let i = 0; i < maxImages; i++) {
            console.log(`下载第 ${i + 1}/${maxImages} 对图像...`);
            
            try {
                // 下载RGB图像
                const rgbResponse = await fetch(rgbImages[i].path);
                if (!rgbResponse.ok) throw new Error(`RGB图像下载失败: ${rgbImages[i].path}`);
                const rgbBlob = await rgbResponse.blob();
                const rgbFile = new File([rgbBlob], rgbImages[i].filename, { type: rgbBlob.type || 'image/jpeg' });
                rgbFiles.push(rgbFile);
                console.log(`RGB图像已添加: ${rgbImages[i].filename}, 大小: ${rgbBlob.size}`);
                
                // 下载热红外图像
                const thermalResponse = await fetch(thermalImages[i].path);
                if (!thermalResponse.ok) throw new Error(`热红外图像下载失败: ${thermalImages[i].path}`);
                const thermalBlob = await thermalResponse.blob();
                const thermalFile = new File([thermalBlob], thermalImages[i].filename, { type: thermalBlob.type || 'image/jpeg' });
                thermalFiles.push(thermalFile);
                console.log(`热红外图像已添加: ${thermalImages[i].filename}, 大小: ${thermalBlob.size}`);
            } catch (err) {
                console.error(`下载第 ${i + 1} 对图像失败:`, err);
            }
        }
        
        console.log(`总共下载了 ${rgbFiles.length} 对图像`);
        
        if (rgbFiles.length === 0) {
            throw new Error('没有成功下载任何图像');
        }
        
        // 使用DataTransfer设置文件
        const rgbInput = document.getElementById('fusionRgbInput');
        const thermalInput = document.getElementById('fusionThermalInput');
        
        if (!rgbInput || !thermalInput) {
            console.error('输入元素未找到');
            return;
        }
        
        // 创建DataTransfer并添加文件
        const rgbDataTransfer = new DataTransfer();
        const thermalDataTransfer = new DataTransfer();
        
        rgbFiles.forEach(file => rgbDataTransfer.items.add(file));
        thermalFiles.forEach(file => thermalDataTransfer.items.add(file));
        
        // 设置files属性
        rgbInput.files = rgbDataTransfer.files;
        thermalInput.files = thermalDataTransfer.files;
        
        console.log('文件已设置到input元素');
        console.log('RGB input files:', rgbInput.files.length);
        console.log('Thermal input files:', thermalInput.files.length);
        
        // 手动显示预览
        rgbPreview.innerHTML = '';
        thermalPreview.innerHTML = '';
        
        // RGB预览
        const rgbFileCount = document.createElement('p');
        rgbFileCount.textContent = `已选择 ${rgbFiles.length} 张图片`;
        rgbFileCount.style.cssText = 'text-align: left; padding: 0 5px; font-size: 0.9em; color: #666; grid-column: 1 / -1;';
        rgbPreview.appendChild(rgbFileCount);
        
        rgbFiles.slice(0, 6).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('preview-img');
                rgbPreview.appendChild(img);
            }
            reader.readAsDataURL(file);
        });
        
        // 热红外预览
        const thermalFileCount = document.createElement('p');
        thermalFileCount.textContent = `已选择 ${thermalFiles.length} 张图片`;
        thermalFileCount.style.cssText = 'text-align: left; padding: 0 5px; font-size: 0.9em; color: #666; grid-column: 1 / -1;';
        thermalPreview.appendChild(thermalFileCount);
        
        thermalFiles.slice(0, 6).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('preview-img');
                thermalPreview.appendChild(img);
            }
            reader.readAsDataURL(file);
        });
        
        console.log('预览已更新');
        
        // 自动选择场景
        const sceneSelect = document.getElementById('fusionSceneSelect');
        if (sceneSelect) {
            sceneSelect.value = sceneName;
            console.log('场景已选择:', sceneName);
        }
        
        // 检查是否可以开始融合
        checkFusionReady();
        
        alert(`✅ 已加载场景图像！\n\n场景: ${sceneName}\n图像对数: ${rgbFiles.length}`);
        
    } catch (error) {
        console.error('加载场景图像失败:', error);
        alert('加载场景图像失败: ' + error.message);
        const rgbPreview = document.getElementById('fusionRgbPreview');
        const thermalPreview = document.getElementById('fusionThermalPreview');
        if (rgbPreview) rgbPreview.innerHTML = '<p style="text-align: center; padding: 20px; color: #f56565;">加载失败: ' + error.message + '</p>';
        if (thermalPreview) thermalPreview.innerHTML = '<p style="text-align: center; padding: 20px; color: #f56565;">加载失败: ' + error.message + '</p>';
    }
}

/**
 * Handle file selection and preview
 */
function handleFusionFileSelection(input, previewId) {
    const previewContainer = document.getElementById(previewId);
    previewContainer.innerHTML = '';

    if (input.files.length > 0) {
        const fileCount = document.createElement('p');
        fileCount.textContent = `已选择 ${input.files.length} 张图片`;
        fileCount.style.cssText = 'text-align: left; padding: 0 5px; font-size: 0.9em; color: #666; grid-column: 1 / -1;';
        previewContainer.appendChild(fileCount);

        Array.from(input.files).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('preview-img');
                previewContainer.appendChild(img);
            }
            reader.readAsDataURL(file);
        });
    }
    checkFusionReady();
}

/**
 * Check if fusion is ready to start
 */
function checkFusionReady() {
    const rgbFiles = document.getElementById('fusionRgbInput').files;
    const thermalFiles = document.getElementById('fusionThermalInput').files;
    const sceneName = document.getElementById('fusionSceneSelect').value;
    const fusionBtn = document.getElementById('fusionBtn');

    if (rgbFiles.length > 0 && rgbFiles.length === thermalFiles.length && sceneName) {
        fusionBtn.disabled = false;
        fusionBtn.innerHTML = `开始融合 (${rgbFiles.length} 对)`;
    } else {
        fusionBtn.disabled = true;
        if (!sceneName) {
            fusionBtn.innerHTML = '请先选择场景';
        } else if (rgbFiles.length > 0 && thermalFiles.length > 0 && rgbFiles.length !== thermalFiles.length) {
            fusionBtn.innerHTML = '图像数量不匹配';
        } else {
            fusionBtn.innerHTML = '开始图像融合';
        }
    }
}

/**
 * Start the fusion process
 */
async function startFusion() {
    const fusionBtn = document.getElementById('fusionBtn');
    const progressBar = document.getElementById('fusionProgressBar');
    const progressFill = document.getElementById('fusionProgressFill');
    
    fusionBtn.innerHTML = '<span class="loading-spinner"></span>融合处理中...';
    fusionBtn.disabled = true;
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';

    const progressInterval = setInterval(() => {
        const currentWidth = parseInt(progressFill.style.width) || 0;
        if (currentWidth < 90) {
            progressFill.style.width = (currentWidth + 10) + '%';
        }
    }, 300);

    try {
        const rgbFiles = document.getElementById('fusionRgbInput').files;
        const thermalFiles = document.getElementById('fusionThermalInput').files;
        const sceneName = document.getElementById('fusionSceneSelect').value;

        const formData = new FormData();
        for (const file of rgbFiles) formData.append('rgb_images', file);
        for (const file of thermalFiles) formData.append('thermal_images', file);
        formData.append('scene_name', sceneName);

        const token = getToken();
        const response = await fetch('/api/fusion', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '融合请求失败');
        }

        const results = await response.json();
        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        // Display results
        const fusionResultGrid = document.getElementById('fusionResultGrid');
        fusionResultGrid.innerHTML = '';

        results.forEach(result => {
            const resultItem = document.createElement('div');
            resultItem.classList.add('result-item');
            resultItem.innerHTML = `
                <img src="${result.fused_image}" class="result-img" alt="融合图像">
                <h4>${result.original_filename}</h4>
                <div class="fusion-metrics">
                    <p>平均梯度 (AG): ${result.metrics.ag}</p>
                    <p>标准差 (SD): ${result.metrics.sd}</p>
                    <p>视觉信息保真度 (VIF): ${result.metrics.vif}</p>
                </div>
            `;
            fusionResultGrid.appendChild(resultItem);
        });

        document.getElementById('fusionResults').classList.add('active');
        setTimeout(() => progressBar.style.display = 'none', 500);

    } catch (error) {
        clearInterval(progressInterval);
        console.error('融合失败:', error);
        alert('图像融合失败: ' + error.message);
        progressBar.style.display = 'none';
    } finally {
        checkFusionReady();
    }
}

/**
 * Setup drag and drop for file upload
 */
function setupDragDrop(box, input, previewId) {
    box.addEventListener('dragover', (e) => {
        e.preventDefault();
        box.classList.add('dragover');
    });

    box.addEventListener('dragleave', (e) => {
        e.preventDefault();
        box.classList.remove('dragover');
    });

    box.addEventListener('drop', (e) => {
        e.preventDefault();
        box.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            handleFusionFileSelection(input, previewId);
        }
    });
}


// ========== 演示数据加载功能 ==========
