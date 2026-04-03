/**
 * Image Fusion Module
 * Handles RGB and thermal image fusion functionality
 */

import { getToken } from './core.js';
import { getIcon } from '../icons.js';

/**
 * Load and display the fusion page content
 * @param {Object} params - Optional parameters, e.g., { scene: 'sceneName' }
 */
export async function loadFusionContent(params = {}) {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>${getIcon('fusion', 20)}</span>
                <span>图像融合</span>
            </div>
            
            ${params.scene ? `
            <div style="background: #e6f7ff; border-left: 4px solid #1890ff; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
                <p style="margin: 0; color: #0050b3; font-size: 14px;">
                    ${getIcon('box', 16)} 正在处理场景: <strong>${params.scene}</strong>
                </p>
            </div>
            ` : ''}
            
            <!-- 场景选择 -->
            <div class="process-section" style="margin-bottom: 24px;">
                <h3 style="margin-bottom: 12px; color: #333;">选择场景</h3>
                <select id="fusionSceneSelect" style="width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; margin-bottom: 16px;">
                    <option value="">--请选择一个场景进行融合--</option>
                </select>
                <div id="sceneImagePreview" style="display: none;">
                    <h4 style="margin: 16px 0 12px 0; color: #333;">场景图像预览</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                        <div>
                            <div style="font-weight: 500; margin-bottom: 8px; color: #666;">${getIcon('camera', 16)} RGB图像 (<span id="rgbImageCount">0</span>张)</div>
                            <div id="fusionRgbPreview" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; padding: 12px; background: #f8f9fa; border-radius: 4px; min-height: 120px;"></div>
                        </div>
                        <div>
                            <div style="font-weight: 500; margin-bottom: 8px; color: #666;">${getIcon('thermal', 16)} 热红外图像 (<span id="thermalImageCount">0</span>张)</div>
                            <div id="fusionThermalPreview" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; padding: 12px; background: #f8f9fa; border-radius: 4px; min-height: 120px;"></div>
                        </div>
                    </div>
                    <div id="imageCountWarning" style="display: none; background: #fff7e6; border-left: 4px solid #fa8c16; padding: 12px 16px; margin-bottom: 16px; border-radius: 4px;">
                        <p style="margin: 0; color: #ad6800; font-size: 14px;">
                            ${getIcon('warning', 16, '#fa8c16')} <span id="warningMessage">图像数量不匹配</span>
                        </p>
                    </div>
                </div>
                <button class="btn-process" id="fusionBtn" disabled style="margin-top: 0;">开始图像融合</button>
                <div class="progress-bar" id="fusionProgressBar">
                    <div class="progress-fill" id="fusionProgressFill"></div>
                </div>
            </div>

            <!-- 融合结果 -->
            <div class="result-panel" id="fusionResults">
                <div class="result-title">${getIcon('fusion', 20)} 图像融合结果</div>
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
    const fusionBtn = document.getElementById('fusionBtn');
    const sceneSelect = document.getElementById('fusionSceneSelect');

    // 加载场景列表
    await loadScenesForFusion();

    // 场景选择变化时加载图像预览
    sceneSelect.addEventListener('change', async (e) => {
        const sceneName = e.target.value;
        if (sceneName) {
            await loadSceneImagesPreview(sceneName);
        } else {
            // 隐藏预览区域
            const previewSection = document.getElementById('sceneImagePreview');
            if (previewSection) previewSection.style.display = 'none';
            checkFusionReady();
        }
    });

    // 开始融合按钮
    fusionBtn.addEventListener('click', startFusion);
    
    // 如果传入了场景参数，自动选择并加载该场景
    if (params.scene) {
        setTimeout(() => {
            sceneSelect.value = params.scene;
            loadSceneImagesPreview(params.scene);
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
        
        if (scenes.length === 0) {
            select.innerHTML = '<option value="">暂无场景，请先在场景资产页面创建场景</option>';
            select.disabled = true;
            return;
        }
        
        select.innerHTML = '<option value="">--请选择一个场景进行融合--</option>';
        select.disabled = false;
        
        scenes.forEach(scene => {
            const option = document.createElement('option');
            option.value = scene.name;
            option.textContent = `${scene.name} (RGB: ${scene.rgb_count}, 热红外: ${scene.thermal_count})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载场景失败:', error);
        const select = document.getElementById('fusionSceneSelect');
        select.innerHTML = '<option value="">加载场景失败，请刷新重试</option>';
        select.disabled = true;
    }
}

/**
 * Load and preview images from a specific scene
 * @param {string} sceneName - The name of the scene to load images from
 */
async function loadSceneImagesPreview(sceneName) {
    console.log('加载场景图像预览:', sceneName);
    
    const previewSection = document.getElementById('sceneImagePreview');
    const rgbPreview = document.getElementById('fusionRgbPreview');
    const thermalPreview = document.getElementById('fusionThermalPreview');
    const rgbCountEl = document.getElementById('rgbImageCount');
    const thermalCountEl = document.getElementById('thermalImageCount');
    const warningDiv = document.getElementById('imageCountWarning');
    const warningMsg = document.getElementById('warningMessage');
    
    if (!previewSection || !rgbPreview || !thermalPreview) {
        console.error('预览容器未找到');
        return;
    }
    
    // 显示预览区域
    previewSection.style.display = 'block';
    
    // 显示加载状态
    rgbPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">加载中...</div>';
    thermalPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">加载中...</div>';
    
    try {
        const token = getToken();
        
        // 获取场景图像列表
        const response = await fetch(`/api/scenes/${sceneName}/images`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('无法获取场景图像');
        }
        
        const data = await response.json();
        const rgbImages = data.rgb_images || [];
        const thermalImages = data.thermal_images || [];
        
        console.log(`RGB图像: ${rgbImages.length}, 热红外图像: ${thermalImages.length}`);
        
        // 更新图像数量
        if (rgbCountEl) rgbCountEl.textContent = rgbImages.length;
        if (thermalCountEl) thermalCountEl.textContent = thermalImages.length;
        
        // 检查图像数量是否匹配
        if (rgbImages.length === 0 || thermalImages.length === 0) {
            warningDiv.style.display = 'block';
            warningMsg.textContent = '该场景缺少图像数据，请先在场景资产页面上传图像';
            rgbPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">暂无图像</div>';
            thermalPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">暂无图像</div>';
            checkFusionReady();
            return;
        }
        
        if (rgbImages.length !== thermalImages.length) {
            warningDiv.style.display = 'block';
            warningMsg.textContent = `图像数量不匹配：RGB ${rgbImages.length}张，热红外 ${thermalImages.length}张。融合需要相同数量的图像对。`;
        } else {
            warningDiv.style.display = 'none';
        }
        
        // 显示RGB图像缩略图（前6张）
        rgbPreview.innerHTML = '';
        const rgbToShow = rgbImages.slice(0, 6);
        rgbToShow.forEach(img => {
            const imgEl = document.createElement('img');
            imgEl.src = img.path;
            imgEl.style.cssText = 'width: 100%; height: 100px; object-fit: cover; border-radius: 4px; cursor: pointer;';
            imgEl.title = img.filename;
            imgEl.onclick = () => window.open(img.path, '_blank');
            rgbPreview.appendChild(imgEl);
        });
        
        if (rgbImages.length > 6) {
            const moreDiv = document.createElement('div');
            moreDiv.style.cssText = 'display: flex; align-items: center; justify-content: center; background: #f0f0f0; border-radius: 4px; color: #666; font-size: 14px;';
            moreDiv.textContent = `+${rgbImages.length - 6}`;
            rgbPreview.appendChild(moreDiv);
        }
        
        // 显示热红外图像缩略图（前6张）
        thermalPreview.innerHTML = '';
        const thermalToShow = thermalImages.slice(0, 6);
        thermalToShow.forEach(img => {
            const imgEl = document.createElement('img');
            imgEl.src = img.path;
            imgEl.style.cssText = 'width: 100%; height: 100px; object-fit: cover; border-radius: 4px; cursor: pointer;';
            imgEl.title = img.filename;
            imgEl.onclick = () => window.open(img.path, '_blank');
            thermalPreview.appendChild(imgEl);
        });
        
        if (thermalImages.length > 6) {
            const moreDiv = document.createElement('div');
            moreDiv.style.cssText = 'display: flex; align-items: center; justify-content: center; background: #f0f0f0; border-radius: 4px; color: #666; font-size: 14px;';
            moreDiv.textContent = `+${thermalImages.length - 6}`;
            thermalPreview.appendChild(moreDiv);
        }
        
        // 检查融合准备状态
        checkFusionReady();
        
    } catch (error) {
        console.error('加载场景图像预览失败:', error);
        rgbPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #f56565;">加载失败</div>';
        thermalPreview.innerHTML = '<div style="text-align: center; padding: 20px; color: #f56565;">加载失败</div>';
    }
}

/**
 * Check if fusion is ready to start
 */
function checkFusionReady() {
    const sceneName = document.getElementById('fusionSceneSelect').value;
    const fusionBtn = document.getElementById('fusionBtn');
    const rgbCountEl = document.getElementById('rgbImageCount');
    const thermalCountEl = document.getElementById('thermalImageCount');
    
    if (!fusionBtn) return;
    
    const rgbCount = parseInt(rgbCountEl?.textContent || '0');
    const thermalCount = parseInt(thermalCountEl?.textContent || '0');

    if (!sceneName) {
        fusionBtn.disabled = true;
        fusionBtn.innerHTML = '请先选择场景';
    } else if (rgbCount === 0 || thermalCount === 0) {
        fusionBtn.disabled = true;
        fusionBtn.innerHTML = '场景缺少图像数据';
    } else if (rgbCount !== thermalCount) {
        fusionBtn.disabled = true;
        fusionBtn.innerHTML = `图像数量不匹配 (RGB: ${rgbCount}, 热红外: ${thermalCount})`;
    } else {
        fusionBtn.disabled = false;
        const pairsToProcess = Math.min(rgbCount, 10);
        if (rgbCount > 10) {
            fusionBtn.innerHTML = `开始融合 (处理前 ${pairsToProcess} 对)`;
        } else {
            fusionBtn.innerHTML = `开始融合 (${pairsToProcess} 对)`;
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
    const sceneName = document.getElementById('fusionSceneSelect').value;
    
    if (!sceneName) {
        alert('请先选择场景');
        return;
    }
    
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
        const token = getToken();
        
        // 使用场景名称调用融合API
        const response = await fetch('/api/fusion', {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ scene_name: sceneName })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '融合请求失败');
        }

        const results = await response.json();
        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        // 显示融合结果
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
        
        alert(`融合完成！\n\n成功融合 ${results.length} 对图像`);

    } catch (error) {
        clearInterval(progressInterval);
        console.error('融合失败:', error);
        alert('图像融合失败: ' + error.message);
        progressBar.style.display = 'none';
    } finally {
        fusionBtn.disabled = false;
        fusionBtn.innerHTML = '开始图像融合';
        checkFusionReady();
    }
}

// ========== 演示数据加载功能 ==========
