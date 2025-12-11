"""
Flask应用配置文件

包含数据库、安全、管理员和采集器的所有配置项
"""

import os

class Config:
    """
    Flask应用基础配置类
    
    该类包含了系统运行所需的所有配置参数
    """
    
    # Flask安全配置
    # SECRET_KEY用于session加密，优先从环境变量获取
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hduhygf43kajndjkwndf43234qjkdkb23w12786418675247298'
    
    # 数据库配置
    # 使用SQLite数据库，文件存储在instance目录下
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cms_video.db'
    # 关闭修改追踪功能，节省内存
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 管理员账号配置
    # 默认管理员用户名，生产环境应修改
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    # 默认管理员密码，生产环境应修改
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'
    
    # 前台分页配置
    # 每页显示的视频数量
    VIDEOS_PER_PAGE = 12
    
    # 文件上传配置
    # 上传文件存储目录
    UPLOAD_FOLDER = 'app/static/uploads'
    # 最大上传文件大小：16MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # 视频采集器配置
    # HTTP请求超时时间（30秒）
    COLLECTOR_TIMEOUT = 30
    # 请求失败时的最大重试次数
    COLLECTOR_MAX_RETRIES = 3
    # 是否验证SSL证书，设为False避免证书错误
    COLLECTOR_VERIFY_SSL = False
