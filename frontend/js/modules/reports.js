// 报告中心模块
import { getToken } from './core.js';

let currentReportPage = 1;
const reportPageSize = 15;
let currentReportType = 'all';

export function loadReportsContent() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <!-- 统计卡片 -->
        <div class="kpi-grid" style="margin-bottom: 24px;">
            <div class="kpi-card">
                <div class="kpi-label">📊 总报告数</div>
                <div class="kpi-value blue" id="reportsTotalCount">0 <span style="font-size: 16px;">份</span></div>
                <div class="kpi-trend">历史累计报告</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">🔀 图像融合</div>
                <div class="kpi-value green" id="reportsFusionCount">0 <span style="font-size: 16px;">次</span></div>
                <div class="kpi-trend">融合处理记录</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">🧊 三维重建</div>
                <div class="kpi-value orange" id="reportsReconstructionCount">0 <span style="font-size: 16px;">次</span></div>
                <div class="kpi-trend">重建任务记录</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">🎯 场景分割</div>
                <div class="kpi-value" style="color: #722ed1;" id="reportsSegmentationCount">0 <span style="font-size: 16px;">次</span></div>
                <div class="kpi-trend">分割任务记录</div>
            </div>
        </div>

        <!-- 工具栏 -->
        <div class="content-card" style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; gap: 10px; flex: 1; max-width: 600px;">
                    <select id="reportTypeFilter" onchange="filterReports()" style="padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="all">所有类型</option>
                        <option value="fusion">图像融合</option>
                        <option value="reconstruction">三维重建</option>
                        <option value="segmentation">场景分割</option>
                    </select>
                    <select id="reportSceneFilter" onchange="filterReports()" style="padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="">所有场景</option>
                    </select>
                    <input type="date" id="reportDateFilter" onchange="filterReports()" style="padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn-process" style="width: auto; padding: 10px 20px;" onclick="exportReports()">
                        <span style="font-size: 16px; margin-right: 5px;">📥</span> 导出报告
                    </button>
                    <button class="btn-secondary" style="padding: 10px 20px;" onclick="refreshReports()">
                        <span style="font-size: 16px; margin-right: 5px;">🔄</span> 刷新
                    </button>
                </div>
            </div>
        </div>

        <!-- 报告列表 -->
        <div class="content-card">
            <div class="card-title">
                <span>📋</span>
                <span>处理记录</span>
            </div>

            <div id="reportsListView">
                <div style="text-align: center; padding: 60px; color: #999;">
                    <div class="loading-spinner" style="width: 40px; height: 40px; margin: 0 auto 20px;"></div>
                    <p>加载报告数据中...</p>
                </div>
            </div>

            <div id="reportsPagination" style="text-align: center; padding: 20px;"></div>
        </div>

        <!-- 报告详情模态框 -->
        <div id="reportDetailModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; width: 90%; max-width: 1000px; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 20px 24px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px;" id="reportDetailTitle">报告详情</h3>
                    <button onclick="closeReportDetailModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                </div>
                <div id="reportDetailContent" style="padding: 24px;">
                    加载中...
                </div>
            </div>
        </div>

        <style>
            .report-card {
                background: #fafafa;
                border: 1px solid #f0f0f0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                transition: all 0.3s;
                cursor: pointer;
            }

            .report-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }

            .report-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }

            .report-type-badge {
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }

            .report-type-fusion {
                background: #e6f7ff;
                color: #1890ff;
            }

            .report-type-reconstruction {
                background: #fff7e6;
                color: #fa8c16;
            }

            .report-type-segmentation {
                background: #f9f0ff;
                color: #722ed1;
            }

            .report-body {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
            }

            .report-info-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .report-info-label {
                font-size: 12px;
                color: #999;
            }

            .report-info-value {
                font-size: 14px;
                color: #333;
                font-weight: 500;
            }
        </style>
    `;

    initReportsModule();
}


// ========== 初始化模块 ==========
async function initReportsModule() {
    await loadScenesList();
    await loadReportsData();
}

// ========== 加载场景列表 ==========
async function loadScenesList() {
    try {
        const response = await fetch('/api/scenes', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const scenes = Array.isArray(data) ? data : data.unique_scenes || [];
            
            const select = document.getElementById('reportSceneFilter');
            if (select) {
                scenes.forEach(scene => {
                    const option = document.createElement('option');
                    option.value = scene;
                    option.textContent = scene;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载场景列表失败:', error);
    }
}

// ========== 加载报告数据 ==========
async function loadReportsData() {
    try {
        const typeFilter = document.getElementById('reportTypeFilter')?.value || 'all';
        const sceneFilter = document.getElementById('reportSceneFilter')?.value || '';
        const dateFilter = document.getElementById('reportDateFilter')?.value || '';
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentReportPage,
            page_size: reportPageSize
        });
        
        if (typeFilter !== 'all') params.append('type', typeFilter);
        if (sceneFilter) params.append('scene', sceneFilter);
        if (dateFilter) params.append('date', dateFilter);
        
        // 从后端API获取报告数据
        const response = await fetch(`/api/reports?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) {
            throw new Error('获取报告数据失败');
        }
        
        const result = await response.json();
        const reports = result.data.reports;
        const total = result.data.total;
        
        // 更新统计数据
        await updateReportStatistics();
        
        // 显示报告列表
        displayReportsList(reports, total);
        
    } catch (error) {
        console.error('加载报告数据失败:', error);
        document.getElementById('reportsListView').innerHTML = `
            <div style="text-align: center; padding: 60px; color: #999;">
                <p style="font-size: 48px; margin-bottom: 16px;">😕</p>
                <p>加载报告失败: ${error.message}</p>
            </div>
        `;
    }
}

// ========== 更新统计数据 ==========
async function updateReportStatistics() {
    try {
        const response = await fetch('/api/reports/statistics', {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (response.ok) {
            const result = await response.json();
            const stats = result.data;
            
            document.getElementById('reportsTotalCount').innerHTML = `${stats.total} <span style="font-size: 16px;">份</span>`;
            document.getElementById('reportsFusionCount').innerHTML = `${stats.fusion} <span style="font-size: 16px;">次</span>`;
            document.getElementById('reportsReconstructionCount').innerHTML = `${stats.reconstruction} <span style="font-size: 16px;">次</span>`;
            document.getElementById('reportsSegmentationCount').innerHTML = `${stats.segmentation} <span style="font-size: 16px;">次</span>`;
        }
    } catch (error) {
        console.error('更新统计数据失败:', error);
    }
}

// ========== 显示报告列表 ==========
function displayReportsList(reports, totalCount) {
    const listView = document.getElementById('reportsListView');
    
    if (reports.length === 0) {
        listView.innerHTML = `
            <div style="text-align: center; padding: 60px; color: #999;">
                <p style="font-size: 48px; margin-bottom: 16px;">📭</p>
                <p style="font-size: 16px;">暂无报告数据</p>
            </div>
        `;
        document.getElementById('reportsPagination').innerHTML = '';
        return;
    }

    const typeLabels = {
        fusion: '图像融合',
        reconstruction: '三维重建',
        segmentation: '场景分割'
    };
    
    const statusLabels = {
        completed: '已完成',
        processing: '处理中',
        failed: '失败'
    };
    
    const statusColors = {
        completed: '#52c41a',
        processing: '#1890ff',
        failed: '#ff4757'
    };
    
    listView.innerHTML = reports.map(report => {
        return `
            <div class="report-card" onclick="showReportDetail(${report.id})">
                <div class="report-header">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span class="report-type-badge report-type-${report.type}">
                            ${typeLabels[report.type]}
                        </span>
                        <span style="font-weight: 600; font-size: 16px;">${report.scene}</span>
                    </div>
                    <span style="padding: 4px 10px; border-radius: 12px; font-size: 12px; background: ${statusColors[report.status]}20; color: ${statusColors[report.status]};">
                        ${statusLabels[report.status]}
                    </span>
                </div>
                <div class="report-body">
                    <div class="report-info-item">
                        <span class="report-info-label">报告ID</span>
                        <span class="report-info-value">#${report.id.toString().padStart(4, '0')}</span>
                    </div>
                    <div class="report-info-item">
                        <span class="report-info-label">创建时间</span>
                        <span class="report-info-value">${new Date(report.created_at).toLocaleString('zh-CN')}</span>
                    </div>
                    <div class="report-info-item">
                        <span class="report-info-label">处理时长</span>
                        <span class="report-info-value">${formatDuration(report.duration)}</span>
                    </div>
                    ${report.images_count ? `
                        <div class="report-info-item">
                            <span class="report-info-label">图像数量</span>
                            <span class="report-info-value">${report.images_count} 张</span>
                        </div>
                    ` : ''}
                    ${report.method ? `
                        <div class="report-info-item">
                            <span class="report-info-label">重建方法</span>
                            <span class="report-info-value">${report.method}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // 更新分页
    displayReportsPagination(totalCount);
}


// ========== 显示分页 ==========
function displayReportsPagination(totalCount) {
    const totalPages = Math.ceil(totalCount / reportPageSize);
    const container = document.getElementById('reportsPagination');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <button onclick="changeReportPage(${currentReportPage - 1})" ${currentReportPage <= 1 ? 'disabled' : ''} 
            style="padding: 8px 12px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; margin: 0 5px;">
            上一页
        </button>
        <span style="margin: 0 15px;">第 ${currentReportPage} / ${totalPages} 页，共 ${totalCount} 条</span>
        <button onclick="changeReportPage(${currentReportPage + 1})" ${currentReportPage >= totalPages ? 'disabled' : ''} 
            style="padding: 8px 12px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; margin: 0 5px;">
            下一页
        </button>
    `;
}

// ========== 切换页码 ==========
function changeReportPage(page) {
    currentReportPage = page;
    loadReportsData();
}

// ========== 格式化时长 ==========
function formatDuration(seconds) {
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) return `${minutes}分${remainingSeconds}秒`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}小时${remainingMinutes}分`;
}

// ========== 显示报告详情 ==========
async function showReportDetail(reportId) {
    try {
        // 从后端获取报告详情
        const response = await fetch(`/api/reports/${reportId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) {
            throw new Error('获取报告详情失败');
        }
        
        const result = await response.json();
        const report = result.data;
        
        const typeLabels = {
            fusion: '图像融合',
            reconstruction: '三维重建',
            segmentation: '场景分割'
        };
        
        const statusLabels = {
            completed: '已完成',
            processing: '处理中',
            failed: '失败'
        };
        
        document.getElementById('reportDetailTitle').textContent = `${typeLabels[report.type]}报告 - #${report.id.toString().padStart(4, '0')}`;
        document.getElementById('reportDetailModal').style.display = 'flex';
        
        let detailContent = `
            <div style="margin-bottom: 24px;">
                <h4 style="margin-bottom: 12px; color: #333;">📊 基本信息</h4>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">报告ID</p>
                            <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 600;">#${report.id.toString().padStart(4, '0')}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">处理类型</p>
                            <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 600;">${typeLabels[report.type]}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">场景名称</p>
                            <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 600;">${report.scene}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">状态</p>
                            <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 600;">${statusLabels[report.status]}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">创建时间</p>
                            <p style="margin: 4px 0 0 0; font-size: 14px;">${new Date(report.created_at).toLocaleString('zh-CN')}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">处理时长</p>
                            <p style="margin: 4px 0 0 0; font-size: 14px;">${formatDuration(report.duration)}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 12px; color: #999;">操作员</p>
                            <p style="margin: 4px 0 0 0; font-size: 14px;">${report.user || '未知'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 根据类型添加特定信息
        if (report.type === 'fusion' && report.metrics) {
            detailContent += `
                <div style="margin-bottom: 24px;">
                    <h4 style="margin-bottom: 12px; color: #333;">📈 融合质量指标</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                        ${report.metrics.avg_ag ? `
                            <div style="background: #e6f7ff; padding: 16px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 24px; font-weight: 600; color: #1890ff;">${report.metrics.avg_ag}</div>
                                <div style="font-size: 13px; color: #666; margin-top: 4px;">平均梯度 (AG)</div>
                            </div>
                        ` : ''}
                        ${report.metrics.avg_sd ? `
                            <div style="background: #f6ffed; padding: 16px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 24px; font-weight: 600; color: #52c41a;">${report.metrics.avg_sd}</div>
                                <div style="font-size: 13px; color: #666; margin-top: 4px;">标准差 (SD)</div>
                            </div>
                        ` : ''}
                        ${report.metrics.avg_vif ? `
                            <div style="background: #fff7e6; padding: 16px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 24px; font-weight: 600; color: #fa8c16;">${report.metrics.avg_vif}</div>
                                <div style="font-size: 13px; color: #666; margin-top: 4px;">视觉信息保真度 (VIF)</div>
                            </div>
                        ` : ''}
                    </div>
                    ${report.images_count ? `
                        <p style="margin-top: 12px; font-size: 13px; color: #666;">
                            处理了 ${report.images_count} 张图像对，平均每对处理时间约 ${(report.duration / report.images_count).toFixed(1)} 秒
                        </p>
                    ` : ''}
                </div>
            `;
        }
        
        if (report.type === 'reconstruction' && report.method) {
            const methodDescriptions = {
                'MSMG': '多模态单高斯 - 使用单一高斯模型处理多模态数据',
                'MFTG': '多模态微调 - 在预训练模型基础上进行微调',
                'OMMG': '一体化多模态 - 端到端的多模态融合重建'
            };
            
            detailContent += `
                <div style="margin-bottom: 24px;">
                    <h4 style="margin-bottom: 12px; color: #333;">🧊 重建信息</h4>
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                        <p style="margin: 0 0 8px 0;"><strong>重建方法:</strong> ${report.method}</p>
                        <p style="margin: 0; font-size: 13px; color: #666;">${methodDescriptions[report.method] || '自定义重建方法'}</p>
                    </div>
                </div>
            `;
        }
        
        if (report.output_path) {
            detailContent += `
                <div style="margin-bottom: 24px;">
                    <h4 style="margin-bottom: 12px; color: #333;">📁 输出文件</h4>
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                        <p style="margin: 0 0 12px 0; color: #666;">处理结果已保存到以下位置：</p>
                        <div style="font-family: monospace; font-size: 13px; background: white; padding: 12px; border-radius: 4px; border: 1px solid #e0e0e0;">
                            ${report.output_path}
                        </div>
                    </div>
                </div>
            `;
        }
        
        detailContent += `
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="btn-secondary" style="padding: 10px 20px;" onclick="closeReportDetailModal()">关闭</button>
                <button class="btn-process" style="width: auto; padding: 10px 20px;" onclick="downloadReport(${report.id}, 'json')">
                    <span style="font-size: 16px; margin-right: 5px;">📄</span> 下载JSON
                </button>
                <button class="btn-process" style="width: auto; padding: 10px 20px; background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);" onclick="downloadReport(${report.id}, 'zip')">
                    <span style="font-size: 16px; margin-right: 5px;">📦</span> 下载ZIP
                </button>
            </div>
        `;
        
        document.getElementById('reportDetailContent').innerHTML = detailContent;
        
    } catch (error) {
        console.error('获取报告详情失败:', error);
        alert('获取报告详情失败: ' + error.message);
    }
}

// ========== 关闭报告详情 ==========
function closeReportDetailModal() {
    document.getElementById('reportDetailModal').style.display = 'none';
}

// ========== 下载报告 ==========
async function downloadReport(reportId, format = 'json') {
    try {
        const response = await fetch(`/api/reports/${reportId}/download?format=${format}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) {
            throw new Error('下载报告失败');
        }
        
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `report_${reportId}.${format}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert(`报告 #${reportId.toString().padStart(4, '0')} 下载成功！`);
        
    } catch (error) {
        console.error('下载报告失败:', error);
        alert('下载报告失败: ' + error.message);
    }
}

// ========== 导出报告 ==========
async function exportReports() {
    try {
        const typeFilter = document.getElementById('reportTypeFilter')?.value || 'all';
        const sceneFilter = document.getElementById('reportSceneFilter')?.value || '';
        const dateFilter = document.getElementById('reportDateFilter')?.value || '';
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (typeFilter !== 'all') params.append('type', typeFilter);
        if (sceneFilter) params.append('scene', sceneFilter);
        if (dateFilter) params.append('date', dateFilter);
        
        const response = await fetch(`/api/reports/export?${params.toString()}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) {
            throw new Error('导出报告失败');
        }
        
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `reports_export_${new Date().toISOString().split('T')[0]}.csv`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // 下载CSV文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('报告导出成功！');
        
    } catch (error) {
        console.error('导出报告失败:', error);
        alert('导出报告失败: ' + error.message);
    }
}

// ========== 刷新报告 ==========
function refreshReports() {
    currentReportPage = 1;
    loadReportsData();
}

// ========== 筛选报告 ==========
function filterReports() {
    currentReportPage = 1;
    loadReportsData();
}

// ========== 挂载到 window 对象 ==========
window.showReportDetail = showReportDetail;
window.closeReportDetailModal = closeReportDetailModal;
window.downloadReport = downloadReport;
window.exportReports = exportReports;
window.refreshReports = refreshReports;
window.filterReports = filterReports;
window.changeReportPage = changeReportPage;
