"""
Flask应用初始化模块

该模块负责创建和配置Flask应用实例，包括：
- 数据库初始化
- 蓝图注册
- 数据模型加载
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建全局SQLAlchemy实例，用于数据库操作
db = SQLAlchemy()

def create_app():
    """
    创建并配置Flask应用实例
    
    该函数执行以下步骤：
    1. 创建Flask应用对象
    2. 加载配置文件
    3. 初始化数据库扩展
    4. 注册前台和后台蓝图
    5. 创建数据库表结构
    
    Returns:
        Flask: 配置完成的Flask应用实例
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 从config.py加载配置（数据库路径、密钥等）
    app.config.from_object('config.Config')
    
    # 将数据库实例与当前应用绑定
    db.init_app(app)
    
    # 注册蓝图模块
    # 前台蓝图：处理视频浏览、搜索等前台功能
    from app.blueprints.frontend import frontend_bp
    # 后台蓝图：处理管理员登录、视频采集等后台功能
    from app.blueprints.admin import admin_bp
    
    # 前台路由前缀为 /（根路径）
    app.register_blueprint(frontend_bp, url_prefix='/')
    # 后台路由前缀为 /admin
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 在应用上下文中创建数据库表
    with app.app_context():
        # 导入所有数据模型（必须导入才能创建对应的表）
        from app.models.video import Video  # 视频信息表
        from app.models.collect_source import CollectSource  # 采集源表
        from app.models.system_log import SystemLog  # 系统日志表
        
        # 根据模型定义创建所有表（如果表不存在）
        db.create_all()
    
    return app
