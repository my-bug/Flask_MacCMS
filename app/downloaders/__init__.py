"""
图片下载管理器

管理图片下载任务的单例模式管理器
"""

import threading
from flask import current_app
from app.downloaders.image_downloader import ImageDownloader


class ImageDownloadManager:
    """
    图片下载管理器（单例模式）
    
    管理图片下载任务，确保同时只有一个下载任务在运行
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.downloader = None
                    cls._instance.thread = None
                    cls._instance.last_result = None
        return cls._instance
    
    def start_download(self, app):
        """
        启动图片下载任务
        
        Args:
            app: Flask应用实例
            
        Returns:
            tuple: (是否成功, 消息)
        """
        if self.downloader and self.downloader.is_running:
            return False, "已有下载任务正在运行"
        
        # 创建新的下载器，传入app实例
        self.downloader = ImageDownloader(app=app)
        
        # 在新线程中执行下载
        def run_download():
            with app.app_context():
                result = self.downloader.download_all()
                self.last_result = result
        
        self.thread = threading.Thread(target=run_download, daemon=True)
        self.thread.start()
        
        return True, "图片下载任务已启动"
    
    def stop_download(self):
        """
        停止图片下载任务
        
        Returns:
            tuple: (是否成功, 消息)
        """
        if not self.downloader or not self.downloader.is_running:
            return False, "没有正在运行的下载任务"
        
        self.downloader.stop()
        return True, "下载任务停止指令已发送"
    
    def get_status(self):
        """
        获取当前下载状态
        
        Returns:
            dict: 状态信息
        """
        if self.downloader:
            return self.downloader.get_result()
        return {
            'success_count': 0,
            'failed_count': 0,
            'skip_count': 0,
            'total_videos': 0,
            'processed_count': 0,
            'current_video': None,
            'is_running': False,
            'errors': []
        }
    
    def get_last_result(self):
        """
        获取最后一次下载结果
        
        Returns:
            dict: 结果信息
        """
        return self.last_result
    
    def verify_localization(self, app):
        """
        验证所有本地化图片
        
        Args:
            app: Flask应用实例
            
        Returns:
            dict: 验证结果
        """
        downloader = ImageDownloader(app=app)
        with app.app_context():
            return downloader.verify_all_localized()


# 全局下载管理器实例
download_manager = ImageDownloadManager()
