/**
 * 前端视频播放器脚本
 * 支持HLS.js播放，错误处理和重试机制
 */

class VideoPlayer {
    constructor(videoElement, videoSrc) {
        this.video = videoElement;
        this.videoSrc = videoSrc;
        this.hls = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    /**
     * 初始化播放器
     */
    init() {
        if (!this.video || !this.videoSrc) {
            console.warn('视频元素或视频源不存在');
            return;
        }
        
        // 检查是否为HLS格式
        if (this.videoSrc.includes('.m3u8')) {
            this.initHLSPlayer();
        } else {
            // 普通视频直接播放
            this.video.src = this.videoSrc;
            this.bindVideoEvents();
        }
    }
    
    /**
     * 初始化HLS播放器
     */
    initHLSPlayer() {
        if (Hls.isSupported()) {
            this.hls = new Hls({
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90,
                maxBufferLength: 30,
                maxMaxBufferLength: 600,
                maxBufferSize: 60 * 1000 * 1000,
                maxBufferHole: 0.5,
                manifestLoadingRetryDelay: 1000,
                manifestLoadingMaxRetry: 3,
                levelLoadingRetryDelay: 1000,
                levelLoadingMaxRetry: 4,
                fragLoadingRetryDelay: 1000,
                fragLoadingMaxRetry: 6
            });
            
            this.hls.loadSource(this.videoSrc);
            this.hls.attachMedia(this.video);
            
            this.bindHLSEvents();
        } else if (this.video.canPlayType('application/vnd.apple.mpegurl')) {
            // iOS设备原生支持HLS
            this.video.src = this.videoSrc;
            this.bindVideoEvents();
        } else {
            this.showError('您的浏览器不支持HLS视频播放');
        }
    }
    
    /**
     * 绑定HLS事件
     */
    bindHLSEvents() {
        // 加载成功
        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('视频加载成功');
            this.hideError();
            this.retryCount = 0;
        });
        
        // 错误处理
        this.hls.on(Hls.Events.ERROR, (event, data) => {
            console.log('HLS错误:', data.type, data.details, data.fatal);
            
            if (data.fatal) {
                this.handleFatalError(data);
            }
        });
        
        // 播放进度
        this.hls.on(Hls.Events.FRAG_LOADED, () => {
            this.hideError();
        });
    }
    
    /**
     * 绑定视频元素事件
     */
    bindVideoEvents() {
        this.video.addEventListener('error', (e) => {
            console.log('视频播放错误:', e);
            this.handleVideoError();
        });
        
        this.video.addEventListener('loadeddata', () => {
            console.log('视频数据加载完成');
            this.hideError();
        });
        
        this.video.addEventListener('waiting', () => {
            console.log('视频缓冲中...');
        });
        
        this.video.addEventListener('playing', () => {
            console.log('视频播放中');
            this.hideError();
        });
    }
    
    /**
     * 处理致命错误
     */
    handleFatalError(data) {
        switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
                console.log('网络错误，尝试恢复...');
                if (this.retryCount < this.maxRetries) {
                    this.showError(`网络连接错误，正在重试 (${this.retryCount + 1}/${this.maxRetries})...`);
                    this.retryCount++;
                    setTimeout(() => {
                        this.hls.startLoad();
                    }, 1000 * this.retryCount);
                } else {
                    this.showError('网络连接失败，请检查网络后刷新页面重试');
                }
                break;
                
            case Hls.ErrorTypes.MEDIA_ERROR:
                console.log('媒体错误，尝试恢复...');
                if (this.retryCount < this.maxRetries) {
                    this.showError(`视频加载错误，正在重试 (${this.retryCount + 1}/${this.maxRetries})...`);
                    this.retryCount++;
                    this.hls.recoverMediaError();
                } else {
                    this.showError('视频解码失败，该视频可能已损坏');
                    this.hls.destroy();
                }
                break;
                
            default:
                console.log('无法恢复的错误');
                this.showError('视频播放失败：该视频源可能已失效或无法访问');
                this.hls.destroy();
                break;
        }
    }
    
    /**
     * 处理视频元素错误
     */
    handleVideoError() {
        const error = this.video.error;
        let errorMessage = '视频播放失败';
        
        if (error) {
            switch(error.code) {
                case error.MEDIA_ERR_ABORTED:
                    errorMessage = '视频播放被中止';
                    break;
                case error.MEDIA_ERR_NETWORK:
                    errorMessage = '网络错误导致视频加载失败';
                    break;
                case error.MEDIA_ERR_DECODE:
                    errorMessage = '视频解码失败';
                    break;
                case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    errorMessage = '视频格式不支持或视频源无效';
                    break;
            }
        }
        
        this.showError(errorMessage);
    }
    
    /**
     * 显示错误提示
     */
    showError(message) {
        let errorDiv = document.getElementById('video-error-msg');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'video-error-msg';
            errorDiv.className = 'video-error-message';
            
            const playerContainer = this.video.parentElement;
            playerContainer.style.position = 'relative';
            playerContainer.appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <div class="error-icon">⚠️</div>
            <div class="error-text">${message}</div>
        `;
        errorDiv.style.display = 'flex';
        
        // 添加CSS样式（如果还没有）
        this.addErrorStyles();
    }
    
    /**
     * 隐藏错误提示
     */
    hideError() {
        const errorDiv = document.getElementById('video-error-msg');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    
    /**
     * 添加错误提示样式
     */
    addErrorStyles() {
        if (document.getElementById('video-error-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'video-error-styles';
        style.textContent = `
            .video-error-message {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(244, 67, 54, 0.95);
                color: white;
                padding: 20px 30px;
                border-radius: 8px;
                z-index: 1000;
                max-width: 80%;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                display: none;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease-out;
            }
            
            .error-icon {
                font-size: 32px;
            }
            
            .error-text {
                font-size: 14px;
                line-height: 1.6;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translate(-50%, -60%);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, -50%);
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * 销毁播放器
     */
    destroy() {
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        this.hideError();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化视频播放器
    const videoElement = document.getElementById('videoPlayer');
    if (videoElement) {
        const videoSrc = videoElement.getAttribute('data-src');
        if (videoSrc) {
            new VideoPlayer(videoElement, videoSrc);
        }
    }
    
    // 懒加载图片
    initLazyLoading();
    
    // 视频卡片动画
    initVideoCardAnimations();
});

/**
 * 初始化懒加载
 */
function initLazyLoading() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
}

/**
 * 初始化视频卡片动画
 */
function initVideoCardAnimations() {
    const cards = document.querySelectorAll('.video-card');
    
    cards.forEach((card, index) => {
        card.style.setProperty('--index', index);
    });
}

/**
 * 平滑滚动到顶部
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 导出全局函数
window.VideoPlayer = VideoPlayer;
window.scrollToTop = scrollToTop;
