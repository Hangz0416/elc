// 认证模块

import { getToken, setToken, setCurrentUser } from './core.js';

// 初始化认证
export async function initAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return null;
    }

    try {
        const response = await fetch('/api/auth/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('未授权');
        }

        const data = await response.json();
        const user = data.data;
        setCurrentUser(user);

        // 显示用户信息
        updateUserUI(user);

        return user;

    } catch (error) {
        console.error('获取用户信息失败:', error);
        setToken(null);
        window.location.href = '/login.html';
        return null;
    }
}

// 更新用户界面
function updateUserUI(user) {
    const userNameEl = document.getElementById('userName');
    const welcomeUserNameEl = document.getElementById('welcomeUserName');
    const userRoleEl = document.getElementById('userRole');
    const userAvatarEl = document.getElementById('userAvatar');
    const adminLinkEl = document.getElementById('adminLink');

    if (userNameEl) userNameEl.textContent = user.username;
    if (welcomeUserNameEl) welcomeUserNameEl.textContent = user.username;
    if (userRoleEl) userRoleEl.textContent = user.role.description;
    if (userAvatarEl) userAvatarEl.textContent = user.username.charAt(0).toUpperCase();

    // 显示管理员菜单
    if (adminLinkEl && user.role.name === 'admin') {
        adminLinkEl.style.display = 'flex';
    }
}
