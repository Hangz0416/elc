// 核心模块 - 全局变量和工具函数

export let currentUser = null;
export let token = null;

export function setToken(newToken) {
    token = newToken;
    if (newToken) {
        localStorage.setItem('token', newToken);
    } else {
        localStorage.removeItem('token');
    }
}

export function setCurrentUser(user) {
    currentUser = user;
}

export function getToken() {
    if (!token) {
        token = localStorage.getItem('token');
    }
    return token;
}

// 更新时间显示
export function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = timeStr;
    }
}

// 退出登录
export function logout() {
    if (confirm('确定要退出登录吗？')) {
        fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        }).finally(() => {
            setToken(null);
            localStorage.removeItem('user');
            window.location.href = '/login.html';
        });
    }
}

// 挂载到window对象供HTML调用
window.logout = logout;
