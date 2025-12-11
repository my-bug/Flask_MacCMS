"""
MacCMS10 采集器模块
"""
from app.collectors.maccms_collector import MacCMSCollector
from app.collectors.maccms_manager import MacCMSCollectorManager, maccms_manager

__all__ = ['MacCMSCollector', 'MacCMSCollectorManager', 'maccms_manager']
