// 主应用入口文件

import { updateTime, setToken } from './modules/core.js';
import { initAuth } from './modules/auth.js';
import { initNavigation } from './modules/navigation.js';
import { loadDashboardData } from './modules/dashboard.js';

// 初始化应用
async function initApp() {
    // 更新时间
    updateTime();
    setInterval(updateTime, 1000);

    // 检查登录状态并获取用户信息
    const user = await initAuth();
    if (!user) {
        return; // 已重定向到登录页
    }

    // 初始化导航
    initNavigation();

    // 加载Dashboard数据
    await loadDashboardData();
}

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);
