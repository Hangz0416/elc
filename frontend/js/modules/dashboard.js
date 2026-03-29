// 工作台模块

import { getToken, currentUser, updateTime } from './core.js';

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
                    <span class="stat-icon">☀️</span>
                    <div class="stat-info">
                        <span class="stat-label">今日</span>
                        <span class="stat-value">晴天</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">🌡️</span>
                    <div class="stat-info">
                        <span class="stat-label">温度</span>
                        <span class="stat-value">15°C</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">💨</span>
                    <div class="stat-info">
                        <span class="stat-label">风力</span>
                        <span class="stat-value">3级</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 数据概览 -->
        <div class="section-header">
            <span class="section-icon">📈</span>
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
                <span>⚡</span>
                <span>快捷操作</span>
            </div>
            <div class="action-grid">
                <a href="#" class="action-btn" data-page="scenes">
                    <div class="action-btn-icon">➕</div>
                    <div class="action-btn-text">新建场景</div>
                </a>
                <a href="#" class="action-btn" data-page="fusion">
                    <div class="action-btn-icon">🔀</div>
                    <div class="action-btn-text">图像融合</div>
                </a>
                <a href="#" class="action-btn" data-page="reconstruction">
                    <div class="action-btn-icon">🧊</div>
                    <div class="action-btn-text">三维重建</div>
                </a>
                <a href="#" class="action-btn" data-page="reports">
                    <div class="action-btn-icon">📄</div>
                    <div class="action-btn-text">查看报告</div>
                </a>
            </div>
        </div>

        <!-- 最近项目 -->
        <div class="content-card">
            <div class="card-title">
                <span>🕒</span>
                <span>最近项目</span>
            </div>
            <div class="project-list" id="recentProjects">
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
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
        // 加载场景数量
        const scenesResponse = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        if (scenesResponse.ok) {
            const scenesData = await scenesResponse.json();
            const scenes = Array.isArray(scenesData) ? scenesData : scenesData.unique_scenes || [];
            const totalScenesEl = document.getElementById('totalScenes');
            const totalScenes2El = document.getElementById('totalScenes2');
            if (totalScenesEl) {
                totalScenesEl.innerHTML = `${scenes.length} <span style="font-size: 16px;">个</span>`;
            }
            if (totalScenes2El) {
                totalScenes2El.innerHTML = `${scenes.length} <span style="font-size: 16px;">个</span>`;
            }
        }
    } catch (error) {
        console.error('加载Dashboard数据失败:', error);
    }
}
