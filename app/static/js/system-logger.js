/**
 * 系统日志页面JavaScript
 * 处理日志详情模态框和清理功能
 */

/**
 * 显示日志详情模态框
 * @param {number} logId - 日志ID
 */
function showLogDetail(logId) {
    const modal = document.getElementById('logDetailModal');
    const content = document.getElementById('logDetailContent');
    
    modal.style.display = 'block';
    content.innerHTML = '<p>加载中...</p>';
    
    fetch(`/admin/logs/${logId}`)
        .then(response => response.json())
        .then(data => {
            content.innerHTML = `
                <div class="log-detail">
                    <div class="detail-row">
                        <label>ID:</label>
                        <span>${data.id}</span>
                    </div>
                    <div class="detail-row">
                        <label>类型:</label>
                        <span>${data.log_type}</span>
                    </div>
                    <div class="detail-row">
                        <label>级别:</label>
                        <span>${data.level}</span>
                    </div>
                    <div class="detail-row">
                        <label>模块:</label>
                        <span>${data.module || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <label>消息:</label>
                        <span>${data.message}</span>
                    </div>
                    <div class="detail-row">
                        <label>详细信息:</label>
                        <pre>${data.details || '-'}</pre>
                    </div>
                    <div class="detail-row">
                        <label>时间:</label>
                        <span>${data.created_at}</span>
                    </div>
                    <div class="detail-row">
                        <label>IP地址:</label>
                        <span>${data.ip_address || '-'}</span>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            content.innerHTML = '<p>加载失败，请重试</p>';
        });
}

/**
 * 关闭日志详情模态框
 */
function closeLogDetail() {
    document.getElementById('logDetailModal').style.display = 'none';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 点击模态框外部关闭
    window.onclick = function(event) {
        const modal = document.getElementById('logDetailModal');
        if (event.target == modal) {
            closeLogDetail();
        }
    };

    // 关闭按钮事件
    const closeBtn = document.getElementById('closeLogDetailBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeLogDetail);
    }

    // 为详情按钮添加点击事件
    const detailButtons = document.querySelectorAll('[data-log-id]');
    detailButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const logId = parseInt(this.getAttribute('data-log-id'));
            showLogDetail(logId);
        });
    });
});
