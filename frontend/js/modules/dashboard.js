// 工作台模块

import { getToken, currentUser, updateTime } from './core.js';
import { getIcon } from '../icons.js';

// 加载工作台内容
export function loadDashboardContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <!-- 欢迎卡片 -->
        <div class="welcome-card">
            <div class="welcome-header">
                <div>
                    <div class="welcome-title">下午好，<span id="welcomeUserName">${currentUser?.username || 'admin'}</span></div>
                    <div class="welcome-subtitle">祝您开心每一天！</div>
                </div>
                <div class="welcome-time" id="currentTime"></div>
            </div>
            <div class="welcome-stats">
                <div class="stat-item">
                    <span class="stat-icon">${getIcon('sun', 20)}</span>
                    <div class="stat-info">
                        <span class="stat-label">今日</span>
                        <span class="stat-value">晴天</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">${getIcon('thermal', 20)}</span>
                    <div class="stat-info">
                        <span class="stat-label">温度</span>
                        <span class="stat-value">15°C</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">${getIcon('wind', 20)}</span>
                    <div class="stat-info">
                        <span class="stat-label">风力</span>
                        <span class="stat-value">3级</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 数据概览 -->
        <div class="section-header">
            <span class="section-icon">${getIcon('chart', 20)}</span>
            <span class="section-title">数据概览</span>
        </div>

        <!-- KPI指标卡片 -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">场景工厂</div>
                <div class="kpi-value green" id="totalScenes">0 <span style="font-size: 16px;">个</span></div>
                <div class="kpi-trend">本月新增 0 个</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">加工点</div>
                <div class="kpi-value green" id="totalImages">0 <span style="font-size: 16px;">个</span></div>
                <div class="kpi-trend">今日处理 0 张</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">重建任务</div>
                <div class="kpi-value orange" id="pendingTasks">0 <span style="font-size: 16px;">单</span></div>
                <div class="kpi-trend">队列中任务</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">累积时长</div>
                <div class="kpi-value green" id="totalHours">0 <span style="font-size: 16px;">时</span></div>
                <div class="kpi-trend">本周新增 0 时</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">重建完成</div>
                <div class="kpi-value blue" id="completedTasks">0 <span style="font-size: 16px;">个</span></div>
                <div class="kpi-trend">完成率 0%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">报告数量</div>
                <div class="kpi-value green" id="totalReports">0 <span style="font-size: 16px;">份</span></div>
                <div class="kpi-trend">本周新增 0 份</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">场景数量</div>
                <div class="kpi-value blue" id="totalScenes2">0 <span style="font-size: 16px;">个</span></div>
                <div class="kpi-trend">活跃场景</div>
            </div>
        </div>

        <!-- 快捷操作 -->
        <div class="content-card">
            <div class="card-title">
                <span>${getIcon('fusion', 20)}</span>
                <span>快捷操作</span>
            </div>
            <div class="action-grid">
                <a href="#" class="action-btn" data-page="scenes">
                    <div class="action-btn-icon">${getIcon('plus', 24)}</div>
                    <div class="action-btn-text">场景资产</div>
                </a>
                <a href="#" class="action-btn" data-page="fusion">
                    <div class="action-btn-icon">${getIcon('fusion', 24)}</div>
                    <div class="action-btn-text">图像融合</div>
                </a>
                <a href="#" class="action-btn" data-page="reconstruction">
                    <div class="action-btn-icon">${getIcon('cube', 24)}</div>
                    <div class="action-btn-text">三维重建</div>
                </a>
                <a href="#" class="action-btn" data-page="reports">
                    <div class="action-btn-icon">${getIcon('file', 24)}</div>
                    <div class="action-btn-text">查看报告</div>
                </a>
            </div>
        </div>

        <!-- 最近项目 -->
        <div class="content-card">
            <div class="card-title">
                <span>${getIcon('clock', 20)}</span>
                <span>最近项目</span>
            </div>
            <div class="project-list" id="recentProjects">
                <div class="empty-state">
                    <div class="empty-icon">${getIcon('box', 48, '#ccc')}</div>
                    <div>暂无最近项目</div>
                </div>
            </div>
        </div>
    `;
    
    // 重新绑定快捷操作按钮
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const page = btn.getAttribute('data-page');
            if (page) {
                e.preventDefault();
                window.navigateToPage(page);
            }
        });
    });
    
    updateTime();
    loadDashboardData();
}

// 加载Dashboard数据
export async function loadDashboardData() {
    try {
        const token = getToken();
        
        // 加载场景数据
        const scenesResponse = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (scenesResponse.ok) {
            const scenesData = await scenesResponse.json();
            const scenes = scenesData.scenes || [];
            
            // 更新场景数量
            const totalScenesEl = document.getElementById('totalScenes');
            const totalScenes2El = document.getElementById('totalScenes2');
            if (totalScenesEl) {
                totalScenesEl.innerHTML = `${scenes.length} <span style="font-size: 16px;">个</span>`;
            }
            if (totalScenes2El) {
                totalScenes2El.innerHTML = `${scenes.length} <span style="font-size: 16px;">个</span>`;
            }
            
            // 计算总图像数量
            let totalRgb = 0;
            let totalThermal = 0;
            let totalFused = 0;
            
            scenes.forEach(scene => {
                totalRgb += scene.rgb_count || 0;
                totalThermal += scene.thermal_count || 0;
                totalFused += scene.fused_count || 0;
            });
            
            const totalImagesCount = totalRgb + totalThermal;
            const totalImagesEl = document.getElementById('totalImages');
            if (totalImagesEl) {
                totalImagesEl.innerHTML = `${totalImagesCount} <span style="font-size: 16px;">张</span>`;
            }
            
            // 更新重建任务数（已融合的场景数）
            const scenesWithFusion = scenes.filter(s => s.fused_count > 0).length;
            const pendingTasksEl = document.getElementById('pendingTasks');
            if (pendingTasksEl) {
                pendingTasksEl.innerHTML = `${scenesWithFusion} <span style="font-size: 16px;">个</span>`;
            }
            
            // 更新累积时长（基于场景数量和图像数量估算）
            // 假设每个场景平均处理时间为2小时，每对图像融合约0.1小时
            const estimatedHours = Math.round(scenes.length * 2 + totalFused * 0.1);
            const totalHoursEl = document.getElementById('totalHours');
            if (totalHoursEl) {
                totalHoursEl.innerHTML = `${estimatedHours} <span style="font-size: 16px;">时</span>`;
            }
            
            // 更新重建完成数（有COLMAP数据的场景）
            const completedReconstruction = scenes.filter(s => s.has_colmap).length;
            const completedTasksEl = document.getElementById('completedTasks');
            if (completedTasksEl) {
                completedTasksEl.innerHTML = `${completedReconstruction} <span style="font-size: 16px;">个</span>`;
            }
        }
        
        // 加载报告数据
        try {
            const reportsResponse = await fetch('/api/reports/statistics', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (reportsResponse.ok) {
                const result = await reportsResponse.json();
                const stats = result.data;
                const totalReportsEl = document.getElementById('totalReports');
                if (totalReportsEl) {
                    totalReportsEl.innerHTML = `${stats.total} <span style="font-size: 16px;">份</span>`;
                }
            }
        } catch (error) {
            console.log('报告数据加载失败，使用默认值:', error);
            // 如果API失败，显示0
            const totalReportsEl = document.getElementById('totalReports');
            if (totalReportsEl) {
                totalReportsEl.innerHTML = `0 <span style="font-size: 16px;">份</span>`;
            }
        }
        
    } catch (error) {
        console.error('加载Dashboard数据失败:', error);
    }
}
