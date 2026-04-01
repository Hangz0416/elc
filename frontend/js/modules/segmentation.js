/**
 * Scene Segmentation Module
 * Handles scene segmentation functionality
 */

import { getToken } from './core.js';

/**
 * Load and display the segmentation page content
 */
export function loadSegmentationContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>🎯</span>
                <span>场景分割</span>
            </div>

            <!-- 分割选项 -->
            <div class="process-section">
                <h3>场景分割选项</h3>
                <select id="segmentationSceneSelect">
                    <option value="">--请选择一个场景进行分割--</option>
                </select>
                <button class="btn-process" id="segmentationBtn" disabled>开始分割</button>
                <div class="progress-bar" id="segmentationProgressBar">
                    <div class="progress-fill" id="segmentationProgressFill"></div>
                </div>
            </div>

            <!-- 分割结果 -->
            <div class="result-panel" id="segmentationResults">
                <div class="result-title">🎯 场景分割结果</div>
                <p id="segmentationStatus" style="text-align: center; margin-bottom: 15px; color: #666;">等待执行分割操作...</p>
                
                <div class="result-item">
                    <h4>🎨 真实分割图与原图对比 (Ground Truth & Original)</h4>
                    <div id="renderedImagesSegmentation" class="rendered-images-gallery-paired">等待渲染结果...</div>
                </div>
            </div>
        </div>
    `;

    initSegmentationModule();
}

/**
 * Initialize segmentation module
 */
function initSegmentationModule() {
    const sceneSelect = document.getElementById('segmentationSceneSelect');
    const segmentationBtn = document.getElementById('segmentationBtn');

    loadScenesForSegmentation();

    sceneSelect.addEventListener('change', () => {
        segmentationBtn.disabled = !sceneSelect.value;
    });

    segmentationBtn.addEventListener('click', startSegmentation);
}

/**
 * Load available scenes for segmentation
 */
async function loadScenesForSegmentation() {
    try {
        const token = getToken();
        const response = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('无法获取场景列表');
        
        const data = await response.json();
        const scenes = data.scenes || [];
        
        const select = document.getElementById('segmentationSceneSelect');
        select.innerHTML = '<option value="">--请选择一个场景进行分割--</option>';
        
        scenes.forEach(scene => {
            const option = document.createElement('option');
            option.value = scene.name;
            option.textContent = scene.name;
            select.appendChild(option);
        });
        
        document.getElementById('segmentationBtn').disabled = true;
    } catch (error) {
        console.error('加载场景失败:', error);
        document.getElementById('segmentationSceneSelect').innerHTML = '<option value="">加载场景失败</option>';
    }
}

/**
 * Start the segmentation process
 */
async function startSegmentation() {
    const sceneName = document.getElementById('segmentationSceneSelect').value;
    const segmentationBtn = document.getElementById('segmentationBtn');
    const statusEl = document.getElementById('segmentationStatus');
    const resultsPanel = document.getElementById('segmentationResults');

    if (!sceneName) {
        alert('请选择一个场景进行分割！');
        return;
    }

    segmentationBtn.disabled = true;
    segmentationBtn.innerHTML = '<span class="loading-spinner"></span>正在分割...';
    resultsPanel.classList.add('active');
    statusEl.textContent = `场景: ${sceneName}, 正在执行分割... (这可能非常耗时，请耐心等待)`;

    document.getElementById('renderedImagesSegmentation').innerHTML = '等待渲染结果...';

    const formData = new FormData();
    formData.append('scene_name', sceneName);

    try {
        const token = getToken();
        const response = await fetch('/api/segmentation', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '分割失败');
        }

        const data = await response.json();
        statusEl.textContent = '分割与渲染完成！';

        displayRenderedImages('renderedImagesSegmentation', data.segmentation_pairs, true);

    } catch (error) {
        console.error('分割错误:', error);
        statusEl.textContent = `分割失败: ${error.message}`;
        alert(`分割过程中发生错误: ${error.message}`);
    } finally {
        segmentationBtn.disabled = false;
        segmentationBtn.innerHTML = '重新分割';
    }
}

/**
 * Display rendered images (paired or single)
 */
function displayRenderedImages(containerId, imageUrls, isPaired = false) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (!imageUrls || imageUrls.length === 0) {
        container.textContent = '没有可用的渲染图片。';
        return;
    }

    if (isPaired) {
        imageUrls.forEach(pair => {
            const pairContainer = document.createElement('div');
            pairContainer.className = 'image-pair-container';

            const gtImg = document.createElement('img');
            gtImg.src = pair.gt_url;
            gtImg.alt = '分割图';
            gtImg.onclick = () => window.open(pair.gt_url, '_blank');

            const gtColorImg = document.createElement('img');
            gtColorImg.src = pair.gt_color_url;
            gtColorImg.alt = '原图';
            gtColorImg.onclick = () => window.open(pair.gt_color_url, '_blank');

            pairContainer.appendChild(gtImg);
            pairContainer.appendChild(gtColorImg);
            container.appendChild(pairContainer);
        });
    } else {
        const gallery = document.createElement('div');
        gallery.className = 'rendered-images-gallery';
        imageUrls.forEach(url => {
            const img = document.createElement('img');
            img.src = url;
            img.alt = '分割图片';
            img.onclick = () => window.open(url, '_blank');
            gallery.appendChild(img);
        });
        container.appendChild(gallery);
    }
}
