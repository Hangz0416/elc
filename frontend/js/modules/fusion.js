/**
 * Image Fusion Module
 * Handles RGB and thermal image fusion functionality
 */

import { getToken } from './core.js';

/**
 * Load and display the fusion page content
 */
export function loadFusionContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>🔀</span>
                <span>图像融合</span>
            </div>
            
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

    initFusionModule();
}

/**
 * Initialize fusion module event listeners and load scenes
 */
function initFusionModule() {
    const rgbInput = document.getElementById('fusionRgbInput');
    const thermalInput = document.getElementById('fusionThermalInput');
    const rgbBox = document.getElementById('fusionRgbBox');
    const thermalBox = document.getElementById('fusionThermalBox');
    const fusionBtn = document.getElementById('fusionBtn');
    const sceneSelect = document.getElementById('fusionSceneSelect');

    loadScenesForFusion();

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
        const scenes = Array.isArray(data) ? data : data.unique_scenes || [];
        
        const select = document.getElementById('fusionSceneSelect');
        select.innerHTML = '<option value="">--请选择一个场景以存放融合数据--</option>';
        
        scenes.forEach(scene => {
            const option = document.createElement('option');
            option.value = scene;
            option.textContent = scene;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载场景失败:', error);
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
