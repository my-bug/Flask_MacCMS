# -*- coding: utf-8 -*-
"""
系统日志模型
用于记录系统运行日志和后台采集日志
"""

from datetime import datetime
from app import db


class SystemLog(db.Model):
    """
    系统日志表
    记录所有系统运行日志和后台采集日志
    """
    __tablename__ = 'system_logs'

    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    
    # 日志类型：system-系统日志, collector-采集日志, download-下载日志
    log_type = db.Column(db.String(20), nullable=False, index=True, default='system', comment='日志类型')
    
    # 日志级别：debug, info, warning, error, critical
    level = db.Column(db.String(10), nullable=False, index=True, default='info', comment='日志级别')
    
    # 日志模块：标识产生日志的模块或功能
    module = db.Column(db.String(50), default='', comment='日志模块')
    
    # 日志消息
    message = db.Column(db.Text, nullable=False, comment='日志消息')
    
    # 详细信息：JSON格式存储详细数据
    details = db.Column(db.Text, default='', comment='详细信息')
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.now, index=True, comment='创建时间')
    
    # IP地址
    ip_address = db.Column(db.String(45), default='', comment='IP地址')
    
    # 用户标识
    user_agent = db.Column(db.String(255), default='', comment='用户代理')

    def __repr__(self):
        """对象字符串表示"""
        return f'<SystemLog {self.id}: [{self.level}] {self.message[:50]}>'

    def to_dict(self):
        """
        转换为字典格式
        用于API返回和前端展示
        """
        return {
            'id': self.id,
            'log_type': self.log_type,
            'level': self.level,
            'module': self.module,
            'message': self.message,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

    @staticmethod
    def log(log_type='system', level='info', module='', message='', details='', ip_address='', user_agent=''):
        """
        创建日志记录的静态方法
        
        参数:
            log_type: 日志类型 (system/collector/download)
            level: 日志级别 (debug/info/warning/error/critical)
            module: 日志模块
            message: 日志消息
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
        
        返回:
            SystemLog: 创建的日志对象
        """
        log_entry = SystemLog(
            log_type=log_type,
            level=level,
            module=module,
            message=message,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            print(f'日志记录失败: {str(e)}')
            return None

    @staticmethod
    def clean_old_logs(days=30):
        """
        清理指定天数之前的日志
        
        参数:
            days: 保留的天数，默认30天
        
        返回:
            int: 删除的日志条数
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            deleted_count = SystemLog.query.filter(SystemLog.created_at < cutoff_date).delete()
            db.session.commit()
            return deleted_count
        except Exception as e:
            db.session.rollback()
            print(f'清理日志失败: {str(e)}')
            return 0

    @staticmethod
    def get_stats():
        """
        获取日志统计信息
        
        返回:
            dict: 包含各类统计数据的字典
        """
        from sqlalchemy import func
        
        # 总日志数
        total = SystemLog.query.count()
        
        # 按类型统计
        type_stats = db.session.query(
            SystemLog.log_type,
            func.count(SystemLog.id)
        ).group_by(SystemLog.log_type).all()
        
        # 按级别统计
        level_stats = db.session.query(
            SystemLog.level,
            func.count(SystemLog.id)
        ).group_by(SystemLog.level).all()
        
        # 今日日志数
        from datetime import date
        today = date.today()
        today_count = SystemLog.query.filter(
            func.date(SystemLog.created_at) == today
        ).count()
        
        return {
            'total': total,
            'today': today_count,
            'by_type': {t: c for t, c in type_stats},
            'by_level': {l: c for l, c in level_stats}
        }
