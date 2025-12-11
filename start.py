#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频CMS系统 - 快速启动脚本
"""

import os
import sys

def check_requirements():
    """
    检查系统运行所需的Python依赖包是否已安装
    
    Returns:
        bool: 如果所有依赖包都安装则返回True，否则返回False
    """
    try:
        # 尝试导入关键依赖包
        import flask
        import flask_sqlalchemy
        import requests
        print("[成功] 所有依赖包已安装")
        return True
    except ImportError as e:
        # 如果缺少依赖包，显示错误信息和解决方案
        print(f"[错误] 缺少依赖包: {e}")
        print("\n请运行以下命令安装依赖：")
        print("pip3 install -r requirements.txt")
        return False

def init_database():
    """
    初始化数据库，创建所需的数据表
    
    该函数会：
    1. 创建Flask应用实例
    2. 根据模型定义创建数据库表
    3. 检查是否需要添加初始数据
    """
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        # 根据模型定义自动创建所有表
        db.create_all()
        print("[成功] 数据库表创建成功")
        
        # 检查采集源表是否为空，提示用户添加数据
        from app.models.collect_source import CollectSource
        if CollectSource.query.count() == 0:
            print("\n[提示] 数据库为空，建议添加采集源")
            print("访问: http://localhost:5002/admin/sources")

def main():
    """
    程序主入口函数
    
    执行顺序：
    1. 检查依赖包
    2. 初始化数据库
    3. 启动Flask Web服务器
    """
    print("=" * 60)
    print("视频CMS系统 v2.0.0 - 启动检查")
    print("=" * 60)
    
    # 第一步：检查必需的Python依赖包
    if not check_requirements():
        sys.exit(1)
    
    # 第二步：初始化SQLite数据库和表结构
    try:
        init_database()
    except Exception as e:
        print(f"[错误] 数据库初始化失败: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("系统准备就绪！")
    print("=" * 60)
    print("\n访问地址:")
    print("  前台首页: http://localhost:5002/")
    print("  后台登录: http://localhost:5002/admin/login")
    print("\n默认账号:")
    print("  用户名: admin")
    print("  密码: admin")
    print("\n启动服务器...")
    print("=" * 60 + "\n")
    
    # 启动Flask应用
    from app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)

if __name__ == '__main__':
    main()
