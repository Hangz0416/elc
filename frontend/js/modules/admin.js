// 系统管理模块
import { getToken } from './core.js';

let adminCurrentPage = { users: 1, logs: 1 };
const adminPageSize = 20;

export function loadAdminContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="content-card">
            <div class="card-title">
                <span>⚙️</span>
                <span>系统管理</span>
            </div>
            
            <div style="border-bottom: 2px solid #f0f0f0; margin-bottom: 20px;">
                <button id="admin-tab-users" class="btn-process admin-tab-btn" style="width: auto; margin: 0 10px 10px 0;" onclick="switchAdminTab('users')">用户管理</button>
                <button id="admin-tab-roles" class="btn-process admin-tab-btn" style="width: auto; margin: 0 10px 10px 0; background: #f0f0f0; color: #666;" onclick="switchAdminTab('roles')">角色管理</button>
                <button id="admin-tab-logs" class="btn-process admin-tab-btn" style="width: auto; margin: 0 10px 10px 0; background: #f0f0f0; color: #666;" onclick="switchAdminTab('logs')">日志审计</button>
            </div>

            <div id="admin-users-tab">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px;">
                    <input type="text" id="adminUserSearch" placeholder="搜索用户名..." style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    <button class="btn-process" style="width: auto;" onclick="showAdminCreateUserModal()">+ 新建用户</button>
                </div>
                
                <div style="background: white; border-radius: 8px; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead style="background: #f8f9fa;">
                            <tr>
                                <th style="padding: 12px; text-align: left;">ID</th>
                                <th style="padding: 12px; text-align: left;">用户名</th>
                                <th style="padding: 12px; text-align: left;">角色</th>
                                <th style="padding: 12px; text-align: left;">状态</th>
                                <th style="padding: 12px; text-align: left;">创建时间</th>
                                <th style="padding: 12px; text-align: left;">操作</th>
                            </tr>
                        </thead>
                        <tbody id="adminUsersTableBody">
                            <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div id="adminUsersPagination" style="text-align: center; padding: 20px;"></div>
            </div>

            <div id="admin-roles-tab" style="display: none;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <div></div>
                    <button class="btn-process" style="width: auto;" onclick="showAdminCreateRoleModal()">+ 新建角色</button>
                </div>

                
                <div style="background: white; border-radius: 8px; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead style="background: #f8f9fa;">
                            <tr>
                                <th style="padding: 12px; text-align: left;">ID</th>
                                <th style="padding: 12px; text-align: left;">角色名称</th>
                                <th style="padding: 12px; text-align: left;">描述</th>
                                <th style="padding: 12px; text-align: left;">权限</th>
                                <th style="padding: 12px; text-align: left;">创建时间</th>
                                <th style="padding: 12px; text-align: left;">操作</th>
                            </tr>
                        </thead>
                        <tbody id="adminRolesTableBody">
                            <tr><td colspan="6" style="text-align: center; padding: 40px;">加载中...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="admin-logs-tab" style="display: none;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px;">
                    <div style="display: flex; gap: 10px; flex: 1;">
                        <select id="adminModuleFilter" onchange="searchAdminLogs()" style="padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="">所有模块</option>
                            <option value="auth">认证</option>
                            <option value="users">用户管理</option>
                            <option value="roles">角色管理</option>
                            <option value="fusion">图像融合</option>
                            <option value="reconstruction">三维重建</option>
                            <option value="segmentation">场景分割</option>
                        </select>
                        <select id="adminLogStatusFilter" onchange="searchAdminLogs()" style="padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="">所有状态</option>
                            <option value="success">成功</option>
                            <option value="failed">失败</option>
                        </select>
                    </div>
                    <button class="btn-process" style="width: auto;" onclick="exportAdminLogs()">导出日志</button>
                </div>
                
                <div style="background: white; border-radius: 8px; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead style="background: #f8f9fa;">
                            <tr>
                                <th style="padding: 12px; text-align: left;">时间</th>
                                <th style="padding: 12px; text-align: left;">用户</th>
                                <th style="padding: 12px; text-align: left;">模块</th>
                                <th style="padding: 12px; text-align: left;">操作</th>
                                <th style="padding: 12px; text-align: left;">状态</th>

                                <th style="padding: 12px; text-align: left;">IP地址</th>
                                <th style="padding: 12px; text-align: left;">详情</th>
                            </tr>
                        </thead>
                        <tbody id="adminLogsTableBody">
                            <tr><td colspan="7" style="text-align: center; padding: 40px;">加载中...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div id="adminLogsPagination" style="text-align: center; padding: 20px;"></div>
            </div>
        </div>

        <!-- 用户模态框 -->
        <div id="adminUserModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 20px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <h3 id="adminUserModalTitle">新建用户</h3>
                    <button onclick="closeAdminUserModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                <div style="padding: 24px;">
                    <input type="hidden" id="adminUserId">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">用户名 *</label>
                        <input type="text" id="adminUserUsername" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div id="adminPasswordGroup" style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">密码 *</label>
                        <input type="password" id="adminUserPassword" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">角色 *</label>
                        <select id="adminUserRole" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"></select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">状态 *</label>
                        <select id="adminUserStatus" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="active">启用</option>
                            <option value="disabled">禁用</option>
                        </select>
                    </div>
                </div>
                <div style="padding: 16px 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="btn-secondary" onclick="closeAdminUserModal()">取消</button>
                    <button class="btn-process" style="width: auto;" onclick="saveAdminUser()">保存</button>
                </div>
            </div>
        </div>


        <!-- 角色模态框 -->
        <div id="adminRoleModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 20px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <h3 id="adminRoleModalTitle">新建角色</h3>
                    <button onclick="closeAdminRoleModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                <div style="padding: 24px;">
                    <input type="hidden" id="adminRoleId">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">角色名称 *</label>
                        <input type="text" id="adminRoleName" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">描述</label>
                        <input type="text" id="adminRoleDescription" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 10px; font-weight: 500;">权限配置</label>
                        <div id="adminPermissionsConfig"></div>
                    </div>
                </div>
                <div style="padding: 16px 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="btn-secondary" onclick="closeAdminRoleModal()">取消</button>
                    <button class="btn-process" style="width: auto;" onclick="saveAdminRole()">保存</button>
                </div>
            </div>
        </div>
    `;

    initAdminModule();
}

// ========== 初始化模块 ==========
async function initAdminModule() {
    await loadAdminRoles();
    await loadAdminUsers();
}

// ========== 标签切换 ==========
function switchAdminTab(tab) {
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.style.background = '#f0f0f0';
        btn.style.color = '#666';
    });
    document.getElementById(`admin-tab-${tab}`).style.background = '#1890ff';
    document.getElementById(`admin-tab-${tab}`).style.color = 'white';
    
    document.getElementById('admin-users-tab').style.display = tab === 'users' ? 'block' : 'none';
    document.getElementById('admin-roles-tab').style.display = tab === 'roles' ? 'block' : 'none';
    document.getElementById('admin-logs-tab').style.display = tab === 'logs' ? 'block' : 'none';

    
    if (tab === 'roles') {
        loadAdminRolesTable();
    } else if (tab === 'logs') {
        loadAdminLogs();
    }
}

// ========== 用户管理功能 ==========
async function loadAdminRoles() {
    try {
        const response = await fetch('/api/roles', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            const userRole = document.getElementById('adminUserRole');
            if (userRole) {
                userRole.innerHTML = data.data
                    .filter(role => role.name !== 'admin')
                    .map(role => `<option value="${role.id}">${role.description}</option>`).join('');
            }
        }
    } catch (error) {
        console.error('加载角色失败:', error);
    }
}

async function loadAdminUsers(page = 1) {
    try {
        const response = await fetch(`/api/users?page=${page}&page_size=${adminPageSize}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            displayAdminUsers(data.data.users);
            displayAdminPagination('users', data.data.page, data.data.page_size, data.data.total);
        }
    } catch (error) {
        console.error('加载用户失败:', error);
    }
}

function displayAdminUsers(users) {
    const tbody = document.getElementById('adminUsersTableBody');
    if (!tbody) return;
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无用户数据</td></tr>';
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr style="border-top: 1px solid #f0f0f0;">
            <td style="padding: 12px;">${user.id}</td>
            <td style="padding: 12px;">${user.username}</td>
            <td style="padding: 12px;">${user.role_name || '-'}</td>
            <td style="padding: 12px;">
                <span style="padding: 4px 10px; border-radius: 12px; font-size: 12px; background: ${user.status === 'active' ? '#d4edda' : '#f8d7da'}; color: ${user.status === 'active' ? '#155724' : '#721c24'};">
                    ${user.status === 'active' ? '启用' : '禁用'}
                </span>
            </td>
            <td style="padding: 12px;">${new Date(user.created_at).toLocaleString('zh-CN')}</td>
            <td style="padding: 12px;">
                <button class="btn-secondary" style="padding: 6px 12px; font-size: 13px;" onclick="editAdminUser(${user.id})">编辑</button>

                ${user.role_name !== 'admin' ? `<button class="btn-secondary" style="padding: 6px 12px; font-size: 13px; background: #ff4757; color: white; margin-left: 5px;" onclick="deleteAdminUser(${user.id}, '${user.username}')">删除</button>` : ''}
            </td>
        </tr>
    `).join('');
}

function displayAdminPagination(type, page, pageSize, total) {
    const totalPages = Math.ceil(total / pageSize);
    const container = document.getElementById(`admin${type.charAt(0).toUpperCase() + type.slice(1)}Pagination`);
    if (!container) return;
    
    container.innerHTML = `
        <button onclick="changeAdminPage('${type}', ${page - 1})" ${page <= 1 ? 'disabled' : ''} style="padding: 8px 12px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer;">上一页</button>
        <span style="margin: 0 15px;">第 ${page} / ${totalPages} 页，共 ${total} 条</span>
        <button onclick="changeAdminPage('${type}', ${page + 1})" ${page >= totalPages ? 'disabled' : ''} style="padding: 8px 12px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer;">下一页</button>
    `;
}

function changeAdminPage(type, page) {
    adminCurrentPage[type] = page;
    if (type === 'users') loadAdminUsers(page);
    else if (type === 'logs') loadAdminLogs(page);
}

function showAdminCreateUserModal() {
    document.getElementById('adminUserModalTitle').textContent = '新建用户';
    document.getElementById('adminUserId').value = '';
    document.getElementById('adminUserUsername').value = '';
    document.getElementById('adminUserPassword').value = '';
    document.getElementById('adminPasswordGroup').style.display = 'block';
    document.getElementById('adminUserModal').style.display = 'flex';
}

async function editAdminUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            const user = data.data;
            document.getElementById('adminUserModalTitle').textContent = '编辑用户';
            document.getElementById('adminUserId').value = user.id;
            document.getElementById('adminUserUsername').value = user.username;
            document.getElementById('adminUserRole').value = user.role_id;
            document.getElementById('adminUserStatus').value = user.status;
            document.getElementById('adminPasswordGroup').style.display = 'none';
            document.getElementById('adminUserModal').style.display = 'flex';
        }
    } catch (error) {
        alert('获取用户信息失败: ' + error.message);
    }
}


async function saveAdminUser() {
    const userId = document.getElementById('adminUserId').value;
    const username = document.getElementById('adminUserUsername').value;
    const password = document.getElementById('adminUserPassword').value;
    const roleId = parseInt(document.getElementById('adminUserRole').value);
    const status = document.getElementById('adminUserStatus').value;

    if (!username || !roleId) {
        alert('请填写必填项');
        return;
    }

    if (!userId && !password) {
        alert('请输入密码');
        return;
    }

    try {
        let response;
        if (userId) {
            response = await fetch(`/api/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, role_id: roleId, status })
            });
        } else {
            response = await fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password, role_id: roleId, status })
            });
        }

        if (response.ok) {
            alert(userId ? '用户更新成功' : '用户创建成功');
            closeAdminUserModal();
            loadAdminUsers(adminCurrentPage.users);
        } else {
            const data = await response.json();
            throw new Error(data.message || data.detail);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function deleteAdminUser(userId, username) {
    if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复。`)) return;

    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });

        if (response.ok) {
            alert('用户删除成功');
            loadAdminUsers(adminCurrentPage.users);
        } else {
            const data = await response.json();
            throw new Error(data.message || data.detail);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

function closeAdminUserModal() {
    document.getElementById('adminUserModal').style.display = 'none';
}


// ========== 角色管理功能 ==========
async function loadAdminRolesTable() {
    try {
        const response = await fetch('/api/roles', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            displayAdminRoles(data.data);
        }
    } catch (error) {
        console.error('加载角色失败:', error);
    }
}

function displayAdminRoles(roles) {
    const tbody = document.getElementById('adminRolesTableBody');
    if (!tbody) return;
    
    if (roles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无角色数据</td></tr>';
        return;
    }

    tbody.innerHTML = roles.map(role => `
        <tr style="border-top: 1px solid #f0f0f0;">
            <td style="padding: 12px;">${role.id}</td>
            <td style="padding: 12px;">${role.name}</td>
            <td style="padding: 12px;">${role.description || '-'}</td>
            <td style="padding: 12px;"><code style="font-size: 12px;">${JSON.stringify(role.permissions).substring(0, 50)}...</code></td>
            <td style="padding: 12px;">${new Date(role.created_at).toLocaleString('zh-CN')}</td>
            <td style="padding: 12px;">
                ${role.name !== 'admin' ? `
                    <button class="btn-secondary" style="padding: 6px 12px; font-size: 13px;" onclick="editAdminRole(${role.id})">编辑</button>
                    <button class="btn-secondary" style="padding: 6px 12px; font-size: 13px; background: #ff4757; color: white; margin-left: 5px;" onclick="deleteAdminRole(${role.id}, '${role.name}')">删除</button>
                ` : '-'}
            </td>
        </tr>
    `).join('');
}

function showAdminCreateRoleModal() {
    document.getElementById('adminRoleModalTitle').textContent = '新建角色';
    document.getElementById('adminRoleId').value = '';
    document.getElementById('adminRoleName').value = '';
    document.getElementById('adminRoleDescription').value = '';
    renderAdminPermissionsConfig({});
    document.getElementById('adminRoleModal').style.display = 'flex';
}

async function editAdminRole(roleId) {
    try {
        const response = await fetch(`/api/roles/${roleId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            const role = data.data;
            document.getElementById('adminRoleModalTitle').textContent = '编辑角色';
            document.getElementById('adminRoleId').value = role.id;

            document.getElementById('adminRoleName').value = role.name;
            document.getElementById('adminRoleDescription').value = role.description || '';
            renderAdminPermissionsConfig(role.permissions);
            document.getElementById('adminRoleModal').style.display = 'flex';
        }
    } catch (error) {
        alert('获取角色信息失败: ' + error.message);
    }
}

function renderAdminPermissionsConfig(permissions) {
    const modules = [
        { key: 'fusion', label: '图像融合' },
        { key: 'reconstruction', label: '三维重建' },
        { key: 'segmentation', label: '场景分割' },
        { key: 'scenes', label: '场景管理' },
        { key: 'reports', label: '报告查看' }
    ];

    const container = document.getElementById('adminPermissionsConfig');
    container.innerHTML = modules.map(module => `
        <div style="margin-bottom: 12px; padding: 10px; background: #f8f9fa; border-radius: 6px;">
            <label style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" id="perm_${module.key}_r" ${permissions[module.key]?.includes('r') ? 'checked' : ''}>
                <span>${module.label} - 读权限</span>
            </label>
            <label style="display: flex; align-items: center; gap: 10px; margin-top: 6px;">
                <input type="checkbox" id="perm_${module.key}_w" ${permissions[module.key]?.includes('w') ? 'checked' : ''}>
                <span>${module.label} - 写权限</span>
            </label>
        </div>
    `).join('');
}

function getAdminPermissionsFromForm() {
    const modules = ['fusion', 'reconstruction', 'segmentation', 'scenes', 'reports'];
    const permissions = {};

    modules.forEach(module => {
        const read = document.getElementById(`perm_${module}_r`)?.checked;
        const write = document.getElementById(`perm_${module}_w`)?.checked;
        
        if (read || write) {
            let perm = '';
            if (read) perm += 'r';
            if (write) perm += 'w';
            permissions[module] = perm;
        }
    });

    return permissions;
}

async function saveAdminRole() {
    const roleId = document.getElementById('adminRoleId').value;
    const name = document.getElementById('adminRoleName').value;
    const description = document.getElementById('adminRoleDescription').value;
    const permissions = getAdminPermissionsFromForm();

    if (!name) {
        alert('请输入角色名称');
        return;
    }


    try {
        let response;
        if (roleId) {
            response = await fetch(`/api/roles/${roleId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description, permissions })
            });
        } else {
            response = await fetch('/api/roles', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description, permissions })
            });
        }

        if (response.ok) {
            alert(roleId ? '角色更新成功' : '角色创建成功');
            closeAdminRoleModal();
            loadAdminRolesTable();
            loadAdminRoles();
        } else {
            const data = await response.json();
            throw new Error(data.message || data.detail);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function deleteAdminRole(roleId, roleName) {
    if (!confirm(`确定要删除角色 "${roleName}" 吗？此操作不可恢复。`)) return;

    try {
        const response = await fetch(`/api/roles/${roleId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });

        if (response.ok) {
            alert('角色删除成功');
            loadAdminRolesTable();
        } else {
            const data = await response.json();
            throw new Error(data.message || data.detail);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

function closeAdminRoleModal() {
    document.getElementById('adminRoleModal').style.display = 'none';
}


// ========== 日志审计功能 ==========
async function loadAdminLogs(page = 1) {
    const module = document.getElementById('adminModuleFilter')?.value || '';
    const status = document.getElementById('adminLogStatusFilter')?.value || '';

    try {
        const params = new URLSearchParams({
            page,
            page_size: adminPageSize
        });
        if (module) params.append('module', module);
        if (status) params.append('status', status);

        const response = await fetch(`/api/logs?${params}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await response.json();
        if (response.ok) {
            displayAdminLogs(data.data.logs);
            displayAdminPagination('logs', data.data.page, data.data.page_size, data.data.total);
        }
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

function displayAdminLogs(logs) {
    const tbody = document.getElementById('adminLogsTableBody');
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">暂无日志数据</td></tr>';
        return;
    }

    tbody.innerHTML = logs.map(log => `
        <tr style="border-top: 1px solid #f0f0f0;">
            <td style="padding: 12px;">${new Date(log.created_at).toLocaleString('zh-CN')}</td>
            <td style="padding: 12px;">${log.username || '-'}</td>
            <td style="padding: 12px;">${log.module}</td>
            <td style="padding: 12px;">${log.action}</td>
            <td style="padding: 12px;">
                <span style="padding: 4px 10px; border-radius: 12px; font-size: 12px; background: ${log.status === 'success' ? '#d4edda' : '#f8d7da'}; color: ${log.status === 'success' ? '#155724' : '#721c24'};">
                    ${log.status === 'success' ? '成功' : '失败'}
                </span>
            </td>
            <td style="padding: 12px;">${log.ip_address || '-'}</td>
            <td style="padding: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${log.details || '-'}">
                ${log.details || '-'}
            </td>
        </tr>
    `).join('');
}

function searchAdminLogs() {
    adminCurrentPage.logs = 1;
    loadAdminLogs(1);
}

async function exportAdminLogs() {
    const module = document.getElementById('adminModuleFilter')?.value || '';
    const status = document.getElementById('adminLogStatusFilter')?.value || '';

    try {
        const params = new URLSearchParams({ format: 'csv' });
        if (module) params.append('module', module);
        if (status) params.append('status', status);


        const response = await fetch(`/api/logs/export?${params}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            alert('日志导出成功');
        } else {
            throw new Error('导出失败');
        }
    } catch (error) {
        alert('导出日志失败: ' + error.message);
    }
}

// ========== 挂载到 window 对象供 HTML 调用 ==========
window.switchAdminTab = switchAdminTab;
window.showAdminCreateUserModal = showAdminCreateUserModal;
window.editAdminUser = editAdminUser;
window.saveAdminUser = saveAdminUser;
window.deleteAdminUser = deleteAdminUser;
window.closeAdminUserModal = closeAdminUserModal;
window.showAdminCreateRoleModal = showAdminCreateRoleModal;
window.editAdminRole = editAdminRole;
window.saveAdminRole = saveAdminRole;
window.deleteAdminRole = deleteAdminRole;
window.closeAdminRoleModal = closeAdminRoleModal;
window.searchAdminLogs = searchAdminLogs;
window.exportAdminLogs = exportAdminLogs;
window.changeAdminPage = changeAdminPage;
