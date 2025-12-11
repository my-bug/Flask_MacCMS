"""
MacCMS10采集管理器

管理MacCMS10采集任务的单例管理器
"""

from app.collectors.maccms_collector import MacCMSCollector
from flask import current_app
import threading


class MacCMSCollectorManager:
    """MacCMS10采集管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.collectors = {}  # {task_id: collector}
        self.task_id_counter = 0
        self._initialized = True
    
    def start_collect(self, url, params=None, max_workers=3, timeout=30, max_retries=3):
        """
        启动采集任务
        
        Args:
            url: 采集接口URL
            params: 采集参数
            max_workers: 并发线程数
            timeout: 超时时间
            max_retries: 重试次数
            
        Returns:
            int: 任务ID
        """
        # 获取Flask应用实例（必须在请求上下文中调用）
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except (RuntimeError, AttributeError) as e:
            print(f"警告：无法获取Flask应用上下文: {str(e)}")
            # 尝试从全局获取app
            try:
                from app import create_app
                app = create_app()
            except:
                app = None
        
        # 创建采集器
        collector = MacCMSCollector(
            url=url,
            params=params,
            max_workers=max_workers,
            timeout=timeout,
            max_retries=max_retries,
            app=app
        )
        
        # 生成任务ID
        self.task_id_counter += 1
        task_id = self.task_id_counter
        
        # 保存采集器
        self.collectors[task_id] = collector
        
        # 在新线程中启动采集
        thread = threading.Thread(
            target=self._run_collector,
            args=(collector, params.get('update_existing', True))
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _run_collector(self, collector, update_existing):
        """在线程中运行采集器"""
        import traceback
        
        # 必须在应用上下文中运行（访问数据库需要）
        if not collector.app:
            print("错误：未找到Flask应用实例，无法启动采集")
            collector.errors.append("未找到Flask应用实例")
            collector.is_running = False
            return
        
        try:
            with collector.app.app_context():
                collector.collect(update_existing=update_existing)
        except Exception as e:
            print(f"采集线程异常: {str(e)}")
            print(traceback.format_exc())
            if collector:
                collector.errors.append(f"采集异常: {str(e)}")
                collector.is_running = False
    
    def stop_collect(self, task_id):
        """
        停止采集任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        collector = self.collectors.get(task_id)
        if collector:
            collector.stop()
            return True
        return False
    
    def get_status(self, task_id):
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 状态信息
        """
        collector = self.collectors.get(task_id)
        if collector:
            return collector.get_status()
        return None
    
    def get_all_status(self):
        """
        获取所有任务状态
        
        Returns:
            dict: {task_id: status}
        """
        return {
            task_id: collector.get_status()
            for task_id, collector in self.collectors.items()
        }
    
    def cleanup_finished_tasks(self):
        """清理已完成的任务"""
        finished = [
            task_id for task_id, collector in self.collectors.items()
            if not collector.is_running
        ]
        for task_id in finished:
            del self.collectors[task_id]
        return len(finished)


# 创建单例实例
maccms_manager = MacCMSCollectorManager()
