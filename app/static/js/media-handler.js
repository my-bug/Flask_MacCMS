/**
 * 图片下载管理 JavaScript
 * 
 * 处理图片下载页面的实时状态更新和进度显示
 */

(function() {
    'use strict';
    
    let statusInterval = null;
    
    /**
     * 更新下载状态
     */
    function updateStatus() {
        fetch('/admin/images/download/status')
            .then(response => response.json())
            .then(data => {
                if (data.is_running) {
                    // 更新进度信息
                    const processedCount = data.processed_count || 0;
                    const totalVideos = data.total_videos || 0;
                    
                    // 更新计数
                    updateElement('processed-count', processedCount);
                    updateElement('total-videos', totalVideos);
                    updateElement('success-count', data.success_count || 0);
                    updateElement('failed-count', data.failed_count || 0);
                    updateElement('skip-count', data.skip_count || 0);
                    
                    // 更新当前处理的视频
                    updateElement('current-video', data.current_video || '准备中...');
                    
                    // 更新进度条
                    if (totalVideos > 0) {
                        const percentage = Math.round((processedCount / totalVideos) * 100);
                        updateProgressBar(percentage);
                    }
                } else {
                    // 任务完成，刷新页面显示结果
                    if (statusInterval) {
                        clearInterval(statusInterval);
                        location.reload();
                    }
                }
            })
            .catch(error => console.error('状态更新失败:', error));
    }
    
    /**
     * 更新元素内容
     */
    function updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }
    
    /**
     * 更新进度条
     */
    function updateProgressBar(percentage) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        
        if (progressText) {
            progressText.textContent = percentage + '%';
        }
    }
    
    /**
     * 初始化
     */
    function init() {
        // 检查是否有任务在运行（通过检查是否有进度条元素）
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            // 只有在下载进行中时才启动定时更新
            statusInterval = setInterval(updateStatus, 2000); // 每2秒更新一次
            
            // 立即更新一次
            updateStatus();
        }
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
