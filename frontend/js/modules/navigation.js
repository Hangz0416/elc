// 导航模块

import { loadDashboardContent } from './dashboard.js';
import { loadScenesContent } from './scenes.js';
import { loadFusionContent } from './fusion.js';
import { loadReconstructionContent } from './reconstruction.js';
import { loadSegmentationContent } from './segmentation.js';
import { loadReportsContent } from './reports.js';
import { loadAdminContent } from './admin.js';

// 初始化导航
export function initNavigation() {
    // 导航切换
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const page = item.getAttribute('data-page');
            if (page) {
                e.preventDefault();
                navigateToPage(page);
            }
        });
    });

    // 快捷操作按钮
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const page = btn.getAttribute('data-page');
            if (page) {
                e.preventDefault();
                navigateToPage(page);
            }
        });
    });
}

// 页面导航函数
export function navigateToPage(page, params = {}) {
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        }
    });

    // 根据页面加载不同内容
    switch(page) {
        case 'dashboard':
            document.getElementById('pageTitle').textContent = '工作台';
            loadDashboardContent();
            break;
        case 'scenes':
            document.getElementById('pageTitle').textContent = '场景资产';
            loadScenesContent();
            break;
        case 'fusion':
            document.getElementById('pageTitle').textContent = '图像融合';
            loadFusionContent(params);
            break;
        case 'reconstruction':
            document.getElementById('pageTitle').textContent = '三维重建';
            loadReconstructionContent();
            break;
        case 'segmentation':
            document.getElementById('pageTitle').textContent = '场景分割';
            loadSegmentationContent();
            break;
        case 'reports':
            document.getElementById('pageTitle').textContent = '报告中心';
            loadReportsContent();
            break;
        case 'admin':
            document.getElementById('pageTitle').textContent = '系统管理';
            loadAdminContent();
            break;
    }
}

// 挂载到window对象供其他模块调用
window.navigateToPage = navigateToPage;
