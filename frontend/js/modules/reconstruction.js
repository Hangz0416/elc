/**
 * 3D Reconstruction Module
 * Handles 3D reconstruction with Three.js visualization
 */

import { getToken } from './core.js';

// Import Three.js modules
import * as THREE from 'three';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

/**
 * Load and display the reconstruction page content
 */
export function loadReconstructionContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>🧊</span>
                <span>三维重建</span>
            </div>

            <!-- 重建选项 -->
            <div class="process-section">
                <h3>三维重建选项</h3>
                <select id="reconstructionSceneSelect">
                    <option value="">正在加载可用场景...</option>
                </select>
                <select id="reconstructionMethodSelect">
                    <option value="MSMG">方法: 多模态单高斯 (MSMG)</option>
                    <option value="MFTG">方法: 多模态微调 (MFTG)</option>
                    <option value="OMMG">方法: 一体化多模态 (OMMG)</option>
                </select>
                <button class="btn-process" id="reconstructionBtn" disabled>开始三维重建</button>
                <div class="progress-bar" id="reconstructionProgressBar">
                    <div class="progress-fill" id="reconstructionProgressFill"></div>
                </div>
            </div>

            <!-- 重建结果 -->
            <div class="result-panel" id="reconstructionResults">
                <div class="result-title">🧊 3D重建结果</div>
                <p id="reconstructionStatus" style="text-align: center; margin-bottom: 15px; color: #666;">等待执行重建...</p>
                
                <div class="result-grid" style="grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div class="result-item" id="colorViewerItem">
                        <h4>🎨 彩色模型</h4>
                        <div id="reconstructionViewerColor" class="model-viewer">等待模型加载...</div>
                    </div>
                    <div class="result-item" id="thermalViewerItem">
                        <h4>🌡️ 热成像模型</h4>
                        <div id="reconstructionViewerThermal" class="model-viewer">等待模型加载...</div>
                    </div>
                </div>

                <div class="result-item">
                    <h4>渲染图片预览 (可点击放大)</h4>
                    <div id="renderedImagesReconstruction" class="rendered-images-gallery-paired">等待渲染结果...</div>
                </div>
            </div>
        </div>
    `;

    initReconstructionModule();
}

/**
 * Initialize reconstruction module
 */
function initReconstructionModule() {
    const sceneSelect = document.getElementById('reconstructionSceneSelect');
    const reconstructionBtn = document.getElementById('reconstructionBtn');

    loadScenesForReconstruction();

    sceneSelect.addEventListener('change', () => {
        reconstructionBtn.disabled = !sceneSelect.value;
    });

    reconstructionBtn.addEventListener('click', startReconstruction);
}

/**
 * Load available scenes for reconstruction
 */
async function loadScenesForReconstruction() {
    try {
        const token = getToken();
        const response = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('无法获取场景列表');
        
        const data = await response.json();
        const scenes = data.scenes || [];
        
        const select = document.getElementById('reconstructionSceneSelect');
        select.innerHTML = '<option value="">--请选择一个场景--</option>';
        
        scenes.forEach(scene => {
            const option = document.createElement('option');
            option.value = scene.name;
            option.textContent = scene.name;
            select.appendChild(option);
        });
        
        document.getElementById('reconstructionBtn').disabled = true;
    } catch (error) {
        console.error('加载场景失败:', error);
        document.getElementById('reconstructionSceneSelect').innerHTML = '<option value="">加载场景失败</option>';
    }
}

/**
 * Start the reconstruction process
 */
async function startReconstruction() {
    const selectedScene = document.getElementById('reconstructionSceneSelect').value;
    const selectedMethod = document.getElementById('reconstructionMethodSelect').value;
    const reconstructionBtn = document.getElementById('reconstructionBtn');
    const statusEl = document.getElementById('reconstructionStatus');
    const resultsPanel = document.getElementById('reconstructionResults');

    if (!selectedScene) {
        alert('请选择一个场景进行重建!');
        return;
    }

    reconstructionBtn.disabled = true;
    reconstructionBtn.innerHTML = '<span class="loading-spinner"></span>正在重建...';
    resultsPanel.classList.add('active');
    statusEl.textContent = `场景: ${selectedScene}, 方法: ${selectedMethod} - 正在重建... (这可能需要几分钟)`;

    // Reset UI
    document.getElementById('reconstructionViewerColor').innerHTML = '等待模型加载...';
    document.getElementById('reconstructionViewerThermal').innerHTML = '等待模型加载...';
    document.getElementById('renderedImagesReconstruction').innerHTML = '';
    document.getElementById('colorViewerItem').style.display = 'block';
    document.getElementById('thermalViewerItem').style.display = 'block';

    const formData = new FormData();
    formData.append('scene_name', selectedScene);
    formData.append('method', selectedMethod);

    try {
        const token = getToken();
        const response = await fetch('/api/reconstruction', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '重建失败');
        }

        const data = await response.json();
        statusEl.textContent = '模型已生成，正在加载并渲染结果...';

        // Load 3D models
        if (data.model_url_color) {
            create3DViewer('reconstructionViewerColor', data.model_url_color);
        } else {
            document.getElementById('reconstructionViewerColor').textContent = '彩色模型生成失败。';
        }

        if (data.model_url_thermal) {
            create3DViewer('reconstructionViewerThermal', data.model_url_thermal);
        } else if (data.model_url_color && !data.model_url_thermal) {
            document.getElementById('colorViewerItem').style.gridColumn = '1 / -1';
            document.getElementById('thermalViewerItem').style.display = 'none';
        } else {
            document.getElementById('reconstructionViewerThermal').textContent = '热成像模型生成失败。';
        }

        // Handle rendered images
        const colorImages = data.rendered_images_color || [];
        const thermalImages = data.rendered_images_thermal || [];

        if (colorImages.length > 0 && colorImages.length === thermalImages.length) {
            const pairedImages = colorImages.map((colorUrl, index) => ({
                gt_url: colorUrl,
                gt_color_url: thermalImages[index]
            }));
            displayRenderedImages('renderedImagesReconstruction', pairedImages, true);
        } else {
            document.getElementById('colorViewerItem').style.gridColumn = '1 / -1';
            document.getElementById('thermalViewerItem').style.display = 'none';
            displayRenderedImages('renderedImagesReconstruction', colorImages, false);
        }

        statusEl.textContent = '重建与渲染完成！(可拖动旋转/滚轮缩放)';

    } catch (error) {
        console.error('重建错误:', error);
        statusEl.textContent = `重建失败: ${error.message}`;
        alert(`重建过程中发生错误: ${error.message}`);
    } finally {
        reconstructionBtn.disabled = false;
        reconstructionBtn.innerHTML = '重新重建';
    }
}

/**
 * Create 3D viewer with Three.js
 */
function create3DViewer(containerId, modelUrl) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`3D查看器容器 #${containerId} 未找到`);
        return;
    }
    container.innerHTML = '';
    container.style.position = 'relative';

    const statusOverlay = document.createElement('div');
    statusOverlay.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #333; background: rgba(240, 240, 240, 0.85); z-index: 10;';
    statusOverlay.textContent = '正在加载模型...';
    container.appendChild(statusOverlay);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);

    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 5;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xcccccc, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 0).normalize();
    scene.add(directionalLight);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1;
    controls.maxDistance = 50;

    const loader = new PLYLoader();
    loader.load(
        modelUrl,
        function (geometry) {
            if (container.contains(statusOverlay)) {
                container.removeChild(statusOverlay);
            }

            geometry.computeBoundingBox();
            const material = new THREE.PointsMaterial({ 
                vertexColors: true,
                size: 0.02
            });

            const points = new THREE.Points(geometry, material);
            
            const box = new THREE.Box3().setFromObject(points);
            const center = box.getCenter(new THREE.Vector3());
            points.position.sub(center);
            
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const fov = camera.fov * (Math.PI / 180);
            let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
            cameraZ *= 1.5;
            camera.position.z = camera.position.y = cameraZ;
            
            controls.target.set(0, 0, 0);
            controls.update();
            
            scene.add(points);
            animateViewer();
        },
        function (xhr) {
            if(xhr.total > 0){
                const percentComplete = (xhr.loaded / xhr.total * 100).toFixed(2);
                statusOverlay.textContent = `正在加载模型: ${percentComplete}%`;
            }
        },
        function (error) {
            console.error('加载PLY模型时出错:', error);
            statusOverlay.textContent = '加载3D模型失败。';
            statusOverlay.style.color = 'red';
        }
    );

    function animateViewer() {
        requestAnimationFrame(animateViewer);
        controls.update();
        renderer.render(scene, camera);
    }

    function onResize() {
        if (container.clientWidth > 0 && container.clientHeight > 0) {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }
    }

    new ResizeObserver(onResize).observe(container);
}

/**
 * Display rendered images
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
            gtImg.alt = '彩色渲染图';
            gtImg.onclick = () => window.open(pair.gt_url, '_blank');

            const gtColorImg = document.createElement('img');
            gtColorImg.src = pair.gt_color_url;
            gtColorImg.alt = '热渲染图';
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
            img.alt = '渲染图片';
            img.onclick = () => window.open(url, '_blank');
            gallery.appendChild(img);
        });
        container.appendChild(gallery);
    }
}
