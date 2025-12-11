"""
采集源数据模型

定义了视频采集源的数据库表结构
MacCMS10采集会自动从API获取分类，不需要存储在数据库
"""

from app import db
from datetime import datetime

class CollectSource(db.Model):
    """
    采集源模型
    
    存储视频采集API的配置信息
    支持启用/禁用、排序等管理功能
    """
    __tablename__ = 'collect_sources'
    
    # 基本字段
    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    name = db.Column(db.String(100), nullable=False, comment='采集源名称，如"奥斯影视"')
    url = db.Column(db.String(500), nullable=False, comment='MacCMS10规范API地址')
    api_type = db.Column(db.String(50), default='json', comment='API数据格式类型')
    
    # 状态和排序
    is_active = db.Column(db.Boolean, default=True, comment='是否启用该采集源')
    sort_order = db.Column(db.Integer, default=0, comment='显示排序值，数字越小越靠前')
    
    # 附加信息
    note = db.Column(db.Text, default='', comment='备注说明信息')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='最后更新时间')
    
    def __repr__(self):
        """字符串表示形式"""
        return f'<CollectSource {self.name}>'
