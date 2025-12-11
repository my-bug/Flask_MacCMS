/**
 * MacCMS10 采集页面交互逻辑
 */

let statusInterval = null;

// 加载采集源URL
function loadSourceUrl() {
    const select = document.getElementById('sourceSelect');
    const urlInput = document.getElementById('collectUrl');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        urlInput.value = selectedOption.dataset.url;
    } else {
        urlInput.value = '';
    }
}

// 测试采集URL
function testUrl() {
    const url = document.getElementById('collectUrl').value;
    const at = document.querySelector('select[name="at"]').value;
    
    if (!url) {
        showMessage('请输入采集接口URL', 'error');
        return;
    }
    
    const btn = event.target;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 测试中...';
    btn.disabled = true;
    
    fetch('/admin/collect/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({url: url, at: at})
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        
        if (data.success) {
            showMessage(`测试成功！共 ${data.info.total} 个视频，当前页 ${data.info.sample_count} 个`, 'success');
        } else {
            showMessage('测试失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        showMessage('测试失败: ' + error, 'error');
    });
}

// 加载分类列表
function loadCategories() {
    const url = document.getElementById('collectUrl').value;
    const at = document.querySelector('select[name="at"]').value;
    
    if (!url) {
        showMessage('请输入采集接口URL', 'error');
        return;
    }
    
    const btn = event.target;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中...';
    btn.disabled = true;
    
    fetch('/admin/collect/categories', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({url: url, at: at})
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        
        if (data.success) {
            // 显示分类卡片
            displayCategoryCards(data.categories);
            // 显示视频预览
            if (data.videos && data.videos.length > 0) {
                displayVideoCards(data.videos);
            }
            showMessage(`成功加载 ${data.categories.length} 个分类`, 'success');
        } else {
            showMessage('获取分类失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        showMessage('获取分类失败: ' + error, 'error');
    });
}

// 显示分类卡片
function displayCategoryCards(categories) {
    const container = document.getElementById('categoryCards');
    const preview = document.getElementById('categoryPreview');
    
    if (!categories || categories.length === 0) {
        preview.style.display = 'none';
        return;
    }
    
    preview.style.display = 'block';
    container.innerHTML = '';
    
    categories.forEach(cat => {
        const card = document.createElement('div');
        card.className = 'category-card';
        card.dataset.typeId = cat.type_id;
        card.innerHTML = `
            <div class="category-name">${cat.type_name}</div>
            <div class="category-id">ID: ${cat.type_id}</div>
        `;
        
        // 点击选择分类（支持多选）
        card.onclick = function() {
            const input = document.querySelector('input[name="type_id"]');
            const isActive = card.classList.contains('active');
            
            if (isActive) {
                // 取消选中
                card.classList.remove('active');
                // 从输入框移除该ID
                const ids = input.value.split(',').filter(id => id.trim() && id.trim() !== String(cat.type_id));
                input.value = ids.join(',');
            } else {
                // 选中
                card.classList.add('active');
                // 添加ID到输入框（用逗号分隔）
                const currentIds = input.value.trim();
                input.value = currentIds ? currentIds + ',' + cat.type_id : String(cat.type_id);
            }
        };
        
        container.appendChild(card);
    });
}

// 显示视频卡片
function displayVideoCards(videos) {
    const container = document.getElementById('videoCards');
    const preview = document.getElementById('videoPreview');
    
    if (!videos || videos.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无视频数据</div>';
        return;
    }
    
    preview.style.display = 'block';
    container.innerHTML = '';
    
    videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'video-card';
        
        const imgUrl = video.vod_pic || '';
        const videoName = video.vod_name || '未知';
        const videoRemarks = video.vod_remarks || '';
        const videoYear = video.vod_year || '';
        const typeName = video.type_name || '未分类';
        
        card.innerHTML = `
            <img src="${imgUrl}" alt="${videoName}" class="video-thumb" 
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'120\\'%3E%3Crect fill=\\'%23f0f0f0\\' width=\\'200\\' height=\\'120\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%23999\\' font-size=\\'14\\'%3E暂无图片%3C/text%3E%3C/svg%3E'">
            <div class="video-info">
                <div class="video-name" title="${videoName}">${videoName}</div>
                <div class="video-meta">
                    <span>📂 ${typeName}</span>
                    ${videoYear ? `<span>📅 ${videoYear}</span>` : ''}
                    ${videoRemarks ? `<span>📺 ${videoRemarks}</span>` : ''}
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// 提交采集表单
document.getElementById('collectForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const btn = this.querySelector('button[type="submit"]');
    const originalHtml = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 启动中...';
    btn.disabled = true;
    
    fetch('/admin/collect/start', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        
        if (data.success) {
            showMessage('采集任务已启动', 'success');
            // 开始轮询状态
            if (data.task_id) {
                startStatusPolling(data.task_id);
                // 添加新任务卡片到列表
                addTaskCard(data.task_id);
            }
        } else {
            showMessage('启动失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        showMessage('启动失败: ' + error, 'error');
    });
});

// 停止采集任务
function stopTask(taskId) {
    if (!confirm('确定要停止这个采集任务吗？')) {
        return;
    }
    
    fetch(`/admin/collect/stop/${taskId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('任务已停止', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showMessage('停止失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showMessage('停止失败: ' + error, 'error');
    });
}

// 清理已完成任务
function cleanupTasks() {
    if (!confirm('确定要清理所有已完成的任务吗？')) {
        return;
    }
    
    fetch('/admin/collect/cleanup', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('清理完成', 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            showMessage('清理失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showMessage('清理失败: ' + error, 'error');
    });
}

// 开始状态轮询
function startStatusPolling(taskId) {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    
    // 立即更新一次
    updateTaskStatus(taskId);
    
    statusInterval = setInterval(() => {
        updateTaskStatus(taskId);
    }, 2000);
}

// 更新任务状态
function updateTaskStatus(taskId) {
    fetch(`/admin/collect/status/${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTaskDisplay(taskId, data.status);
                
                // 如果任务已完成，停止轮询
                if (!data.status.is_running) {
                    clearInterval(statusInterval);
                }
            }
        })
        .catch(error => {
            console.error('状态更新失败:', error);
        });
}

// 更新任务显示
function updateTaskDisplay(taskId, status) {
    const taskElement = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
    if (!taskElement) return;
    
    // 更新状态标签
    const badge = taskElement.querySelector('.task-badge');
    if (badge) {
        if (status.is_running) {
            badge.className = 'task-badge badge-running';
            badge.textContent = '运行中';
        } else {
            badge.className = 'task-badge badge-completed';
            badge.textContent = '已完成';
        }
    }
    
    // 更新停止按钮
    const stopBtn = taskElement.querySelector('button');
    if (stopBtn) {
        if (status.is_running) {
            stopBtn.style.display = '';
        } else {
            stopBtn.style.display = 'none';
        }
    }
    
    // 更新统计数据
    const successStat = taskElement.querySelector('.stat-success .stat-value');
    const skipStat = taskElement.querySelector('.stat-warning .stat-value');
    const failedStat = taskElement.querySelector('.stat-danger .stat-value');
    
    if (successStat) successStat.textContent = status.success_count;
    if (skipStat) skipStat.textContent = status.skip_count;
    if (failedStat) failedStat.textContent = status.failed_count;
    
    // 更新重复计数
    const infoElement = taskElement.querySelector('.task-info');
    if (infoElement) {
        infoElement.textContent = `重复: ${status.consecutive_duplicates}/20`;
    }
}

// 添加任务卡片
function addTaskCard(taskId) {
    const taskList = document.getElementById('taskList');
    if (!taskList) return;
    
    const taskCard = document.createElement('div');
    taskCard.className = 'task-item';
    taskCard.setAttribute('data-task-id', taskId);
    taskCard.innerHTML = `
        <div class="task-header">
            <span class="task-title">任务 #${taskId}</span>
            <span class="task-badge badge-running">运行中</span>
        </div>
        <button class="maccms-btn maccms-btn-sm" style="background: var(--macos-red); margin-bottom: var(--spacing-sm)" 
                onclick="stopTask(${taskId})">
            <i class="fas fa-stop"></i> 停止
        </button>
        <div class="task-stats">
            <div class="stat-item stat-success">
                <span class="stat-label">成功:</span>
                <span class="stat-value">0</span>
            </div>
            <div class="stat-item stat-warning">
                <span class="stat-label">跳过:</span>
                <span class="stat-value">0</span>
            </div>
            <div class="stat-item stat-danger">
                <span class="stat-label">失败:</span>
                <span class="stat-value">0</span>
            </div>
        </div>
        <div class="task-info">重复: 0/20</div>
    `;
    taskList.insertBefore(taskCard, taskList.firstChild);
}

// 显示消息提示
function showMessage(message, type = 'info') {
    // 创建提示元素
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? 'var(--macos-green)' : type === 'error' ? 'var(--macos-red)' : 'var(--macos-blue)'};
        color: white;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    alert.textContent = message;
    
    document.body.appendChild(alert);
    
    // 3秒后自动移除
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('MacCMS采集页面已加载');
});
