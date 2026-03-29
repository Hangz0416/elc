// 场景资产模块

import { getToken } from './core.js';

// 加载场景资产内容
export function loadScenesContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <!-- 统计卡片 -->
        <div class="kpi-grid" style="margin-bottom: 24px;">
            <div class="kpi-card">
                <div class="kpi-label">📦 总场景数</div>
                <div class="kpi-value blue" id="scenesTotalCount">0 <span style="font-size: 16px;">个</span></div>
                <div class="kpi-trend">本月新增 0 个</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">📸 图像对数量</div>
                <div class="kpi-value green" id="scenesImagePairs">0 <span style="font-size: 16px;">对</span></div>
                <div class="kpi-trend">已配准图像对</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">💾 存储占用</div>
                <div class="kpi-value orange" id="scenesStorageSize">0 <span style="font-size: 16px;">GB</span></div>
                <div class="kpi-trend">数据集总大小</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">✅ 标定成功率</div>
                <div class="kpi-value green" id="scenesCalibrationRate">100 <span style="font-size: 16px;">%</span></div>
                <div class="kpi-trend">相机标定质量</div>
            </div>
        </div>

        <!-- 工具栏 -->
        <div class="content-card" style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; gap: 10px; flex: 1; max-width: 600px;">
                    <input type="text" id="sceneSearchInput" placeholder="搜索场景名称..." style="flex: 1; padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                    <select id="sceneStatusFilter" onchange="filterScenes()" style="padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="">所有状态</option>
                        <option value="active">活跃</option>
                        <option value="processing">处理中</option>
                        <option value="completed">已完成</option>
                    </select>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn-process" style="width: auto; padding: 10px 20px;" onclick="showCreateSceneModal()">
                        <span style="font-size: 16px; margin-right: 5px;">➕</span> 新建场景
                    </button>
                    <button class="btn-secondary" style="padding: 10px 20px;" onclick="refreshScenesList()">
                        <span style="font-size: 16px; margin-right: 5px;">🔄</span> 刷新
                    </button>
                </div>
            </div>
        </div>

        <!-- 场景列表 -->
        <div class="content-card">
            <div class="card-title">
                <span>🗂️</span>
                <span>场景列表</span>
                <span style="margin-left: auto; font-size: 14px; font-weight: normal; color: #666;">
                    <label style="display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                        <input type="radio" name="viewMode" value="grid" checked onchange="switchViewMode('grid')"> 网格视图
                    </label>
                    <label style="display: inline-flex; align-items: center; gap: 5px; margin-left: 15px; cursor: pointer;">
                        <input type="radio" name="viewMode" value="list" onchange="switchViewMode('list')"> 列表视图
                    </label>
                </span>
            </div>

            <!-- 网格视图 -->
            <div id="scenesGridView" class="scenes-grid">
                <div style="text-align: center; padding: 60px; color: #999;">
                    <div class="loading-spinner" style="width: 40px; height: 40px; margin: 0 auto 20px;"></div>
                    <p>加载场景数据中...</p>
                </div>
            </div>

            <!-- 列表视图 -->
            <div id="scenesListView" style="display: none;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead style="background: #f8f9fa;">
                        <tr>
                            <th style="padding: 12px; text-align: left;">场景名称</th>
                            <th style="padding: 12px; text-align: left;">图像数量</th>
                            <th style="padding: 12px; text-align: left;">状态</th>
                            <th style="padding: 12px; text-align: left;">创建时间</th>
                            <th style="padding: 12px; text-align: left;">最后更新</th>
                            <th style="padding: 12px; text-align: left;">操作</th>
                        </tr>
                    </thead>
                    <tbody id="scenesListTableBody">
                        <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 新建场景模态框 -->
        <div id="createSceneModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; width: 90%; max-width: 600px; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 20px 24px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px;">新建场景项目</h3>
                    <button onclick="closeCreateSceneModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                </div>
                <div style="padding: 24px;">
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #333;">场景名称 *</label>
                        <input type="text" id="newSceneName" placeholder="例如: Building, Factory, Warehouse" style="width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">建议使用英文，不含空格和特殊字符</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #333;">场景描述</label>
                        <textarea id="newSceneDescription" placeholder="描述场景的用途、特点等信息..." style="width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; min-height: 80px; resize: vertical;"></textarea>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #333;">场景类型</label>
                        <select id="newSceneType" style="width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                            <option value="indoor">室内场景</option>
                            <option value="outdoor">室外场景</option>
                            <option value="industrial">工业场景</option>
                            <option value="other">其他</option>
                        </select>
                    </div>
                </div>
                <div style="padding: 16px 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="btn-secondary" onclick="closeCreateSceneModal()">取消</button>
                    <button class="btn-process" style="width: auto;" onclick="createNewScene()">创建场景</button>
                </div>
            </div>
        </div>

        <!-- 场景详情模态框 -->
        <div id="sceneDetailModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; width: 90%; max-width: 900px; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 20px 24px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px;" id="sceneDetailTitle">场景详情</h3>
                    <button onclick="closeSceneDetailModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                </div>
                <div id="sceneDetailContent" style="padding: 24px;">
                    加载中...
                </div>
            </div>
        </div>
    `;

    // 初始化场景管理模块
    initScenesModule();
}

// 初始化场景管理模块
async function initScenesModule() {
    await loadScenesList();
    
    // 搜索功能
    const searchInput = document.getElementById('sceneSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterScenes);
    }
}

// 加载场景列表
async function loadScenesList() {
    try {
        const response = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) throw new Error('无法获取场景列表');
        
        const data = await response.json();
        const scenes = Array.isArray(data) ? data : data.unique_scenes || [];
        
        // 更新统计数据
        const totalCountEl = document.getElementById('scenesTotalCount');
        if (totalCountEl) {
            totalCountEl.innerHTML = `${scenes.length} <span style="font-size: 16px;">个</span>`;
        }
        
        // 显示场景卡片
        displayScenesGrid(scenes);
        displayScenesList(scenes);
        
    } catch (error) {
        console.error('加载场景失败:', error);
        const gridView = document.getElementById('scenesGridView');
        if (gridView) {
            gridView.innerHTML = `
                <div style="text-align: center; padding: 60px; color: #999;">
                    <p style="font-size: 48px; margin-bottom: 16px;">😕</p>
                    <p>加载场景失败: ${error.message}</p>
                </div>
            `;
        }
    }
}

// 显示网格视图
function displayScenesGrid(scenes) {
    const gridView = document.getElementById('scenesGridView');
    if (!gridView) return;
    
    if (scenes.length === 0) {
        gridView.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px; color: #999;">
                <p style="font-size: 48px; margin-bottom: 16px;">📭</p>
                <p style="font-size: 16px; margin-bottom: 20px;">暂无场景数据</p>
                <button class="btn-process" style="width: auto;" onclick="showCreateSceneModal()">创建第一个场景</button>
            </div>
        `;
        return;
    }

    gridView.innerHTML = scenes.map((scene, index) => {
        const icons = ['🏢', '🏭', '🏗️', '🌆', '🏪', '🏠', '🏛️', '🏰'];
        const icon = icons[index % icons.length];
        const colors = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
            'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
        ];
        const bgColor = colors[index % colors.length];
        
        return `
            <div class="scene-card" onclick="showSceneDetail('${scene}')">
                <div class="scene-card-image" style="background: ${bgColor};">
                    ${icon}
                    <div class="scene-card-badge" style="color: #52c41a;">活跃</div>
                </div>
                <div class="scene-card-body">
                    <div class="scene-card-title">${scene}</div>
                    <div class="scene-card-meta">
                        <span>📸 图像: --</span>
                        <span>💾 --MB</span>
                    </div>
                    <div class="scene-card-actions">
                        <button class="scene-card-btn" onclick="event.stopPropagation(); window.navigateToPage('fusion')">融合</button>
                        <button class="scene-card-btn" onclick="event.stopPropagation(); window.navigateToPage('reconstruction')">重建</button>
                        <button class="scene-card-btn" onclick="event.stopPropagation(); showSceneDetail('${scene}')">详情</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 显示列表视图
function displayScenesList(scenes) {
    const tbody = document.getElementById('scenesListTableBody');
    if (!tbody) return;
    
    if (scenes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #999;">暂无场景数据</td></tr>';
        return;
    }

    tbody.innerHTML = scenes.map(scene => `
        <tr style="border-top: 1px solid #f0f0f0; cursor: pointer;" onclick="showSceneDetail('${scene}')">
            <td style="padding: 12px; font-weight: 500;">${scene}</td>
            <td style="padding: 12px;">--</td>
            <td style="padding: 12px;">
                <span style="padding: 4px 10px; border-radius: 12px; font-size: 12px; background: #d4edda; color: #155724;">活跃</span>
            </td>
            <td style="padding: 12px; color: #666;">--</td>
            <td style="padding: 12px; color: #666;">--</td>
            <td style="padding: 12px;">
                <button class="scene-card-btn" style="padding: 4px 8px; font-size: 12px;" onclick="event.stopPropagation(); showSceneDetail('${scene}')">查看</button>
            </td>
        </tr>
    `).join('');
}

// 切换视图模式
window.switchViewMode = function(mode) {
    const gridView = document.getElementById('scenesGridView');
    const listView = document.getElementById('scenesListView');
    if (gridView) gridView.style.display = mode === 'grid' ? 'grid' : 'none';
    if (listView) listView.style.display = mode === 'list' ? 'block' : 'none';
}

// 筛选场景
window.filterScenes = function() {
    const searchText = document.getElementById('sceneSearchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('sceneStatusFilter')?.value || '';
    console.log('筛选:', searchText, statusFilter);
}

// 刷新场景列表
window.refreshScenesList = function() {
    loadScenesList();
}

// 显示新建场景模态框
window.showCreateSceneModal = function() {
    const modal = document.getElementById('createSceneModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('newSceneName').value = '';
        document.getElementById('newSceneDescription').value = '';
    }
}

// 关闭新建场景模态框
window.closeCreateSceneModal = function() {
    const modal = document.getElementById('createSceneModal');
    if (modal) modal.style.display = 'none';
}

// 创建新场景
window.createNewScene = async function() {
    const name = document.getElementById('newSceneName')?.value.trim();
    const description = document.getElementById('newSceneDescription')?.value.trim();
    const type = document.getElementById('newSceneType')?.value;

    if (!name) {
        alert('请输入场景名称');
        return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
        alert('场景名称只能包含字母、数字、下划线和连字符');
        return;
    }

    try {
        const response = await fetch('/api/scenes', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description, type })
        });

        if (response.ok) {
            alert('场景创建成功！');
            window.closeCreateSceneModal();
            loadScenesList();
        } else {
            const data = await response.json();
            throw new Error(data.detail || '创建失败');
        }
    } catch (error) {
        alert('创建场景失败: ' + error.message);
    }
}

// 显示场景详情
window.showSceneDetail = function(sceneName) {
    const titleEl = document.getElementById('sceneDetailTitle');
    const modal = document.getElementById('sceneDetailModal');
    const contentEl = document.getElementById('sceneDetailContent');
    
    if (titleEl) titleEl.textContent = `场景详情 - ${sceneName}`;
    if (modal) modal.style.display = 'flex';
    
    if (contentEl) {
        contentEl.innerHTML = `
            <div style="margin-bottom: 24px;">
                <h4 style="margin-bottom: 12px; color: #333;">📊 基本信息</h4>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <p style="margin: 8px 0;"><strong>场景名称:</strong> ${sceneName}</p>
                    <p style="margin: 8px 0;"><strong>场景类型:</strong> 工业场景</p>
                    <p style="margin: 8px 0;"><strong>创建时间:</strong> --</p>
                    <p style="margin: 8px 0;"><strong>最后更新:</strong> --</p>
                </div>
            </div>

            <div style="margin-bottom: 24px;">
                <h4 style="margin-bottom: 12px; color: #333;">📸 数据统计</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                    <div style="background: #e6f7ff; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 600; color: #1890ff;">--</div>
                        <div style="font-size: 13px; color: #666; margin-top: 4px;">RGB 图像</div>
                    </div>
                    <div style="background: #fff7e6; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 600; color: #fa8c16;">--</div>
                        <div style="font-size: 13px; color: #666; margin-top: 4px;">热红外图像</div>
                    </div>
                    <div style="background: #f6ffed; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 600; color: #52c41a;">--</div>
                        <div style="font-size: 13px; color: #666; margin-top: 4px;">融合图像</div>
                    </div>
                    <div style="background: #f9f0ff; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 600; color: #722ed1;">--MB</div>
                        <div style="font-size: 13px; color: #666; margin-top: 4px;">存储大小</div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 24px;">
                <h4 style="margin-bottom: 12px; color: #333;">🔧 处理状态</h4>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>📷 相机标定</span>
                        <span style="color: #52c41a;">✓ 已完成</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>🔀 图像融合</span>
                        <span style="color: #999;">- 未开始</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>🧊 三维重建</span>
                        <span style="color: #999;">- 未开始</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>🎯 场景分割</span>
                        <span style="color: #999;">- 未开始</span>
                    </div>
                </div>
            </div>

            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="btn-secondary" style="padding: 10px 20px;" onclick="closeSceneDetailModal()">关闭</button>
                <button class="btn-process" style="width: auto; padding: 10px 20px;" onclick="closeSceneDetailModal(); window.navigateToPage('fusion')">开始处理</button>
            </div>
        `;
    }
}

// 关闭场景详情模态框
window.closeSceneDetailModal = function() {
    const modal = document.getElementById('sceneDetailModal');
    if (modal) modal.style.display = 'none';
}
