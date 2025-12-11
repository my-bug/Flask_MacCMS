#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理工具
用于数据库初始化、迁移、备份和恢复操作
适用于项目部署和维护

使用方法:
    python3 db_manager.py init          # 初始化数据库
    python3 db_manager.py upgrade       # 升级数据库到最新版本
    python3 db_manager.py downgrade     # 降级数据库版本
    python3 db_manager.py reset         # 重置数据库(危险操作)
    python3 db_manager.py backup        # 备份数据库
    python3 db_manager.py restore FILE  # 从备份恢复数据库
    python3 db_manager.py admin         # 查看管理员配置
    python3 db_manager.py status        # 查看数据库状态
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init as migrate_init, migrate as migrate_db, upgrade, downgrade as migrate_downgrade

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Video


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self):
        self.app = create_app()
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def init_database(self):
        """初始化数据库"""
        print("=" * 60)
        print("初始化数据库")
        print("=" * 60)
        
        with self.app.app_context():
            # 检查是否已存在 migrations 目录
            if not os.path.exists('migrations'):
                print("→ 初始化 Flask-Migrate...")
                try:
                    migrate_init(directory='migrations')
                    print("[完成] Flask-Migrate 初始化完成")
                except Exception as e:
                    print(f"[警告] Flask-Migrate 初始化失败: {e}")
                    print("[继续] 将直接创建数据库表")
            else:
                print("[信息] migrations 目录已存在，跳过初始化")
            
            # 创建所有表
            print("[执行] 创建数据库表...")
            db.create_all()
            print("[完成] 数据库表创建完成")
            
            print("\n[完成] 数据库初始化完成！")
            print("\n管理员账户配置:")
            print(f"  用户名: {self.app.config.get('ADMIN_USERNAME', 'admin')}")
            print(f"  密码: {self.app.config.get('ADMIN_PASSWORD', 'admin')}")
            print("  [警告] 如需修改请编辑 config.py 文件")
            
            self._print_database_info()
    
    def upgrade_database(self):
        """升级数据库到最新版本"""
        print("=" * 60)
        print("升级数据库")
        print("=" * 60)
        
        with self.app.app_context():
            try:
                print("[执行] 执行数据库升级...")
                upgrade()
                print("[完成] 数据库升级完成！")
                self._print_database_info()
            except Exception as e:
                print(f"[错误] 升级失败: {str(e)}")
                sys.exit(1)
    
    def downgrade_database(self):
        """降级数据库版本"""
        print("=" * 60)
        print("降级数据库")
        print("=" * 60)
        print("[警告] 此操作将回退数据库到上一个版本")
        
        confirm = input("确认继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("操作已取消")
            return
        
        with self.app.app_context():
            try:
                print("[执行] 执行数据库降级...")
                migrate_downgrade()
                print("[完成] 数据库降级完成！")
                self._print_database_info()
            except Exception as e:
                print(f"[错误] 降级失败: {str(e)}")
                sys.exit(1)
    
    def reset_database(self):
        """重置数据库(删除所有数据)"""
        print("=" * 60)
        print("重置数据库")
        print("=" * 60)
        print("[警告] 此操作将删除所有数据！")
        print("[警告] 建议先执行备份操作: python3 db_manager.py backup")
        
        confirm = input("\n确认重置数据库? 输入 'RESET' 继续: ")
        if confirm != 'RESET':
            print("操作已取消")
            return
        
        with self.app.app_context():
            print("[执行] 删除所有表...")
            db.drop_all()
            print("[完成] 表已删除")
            
            print("[执行] 重新创建表...")
            db.create_all()
            print("[完成] 表已创建")
            
            print("\n[完成] 数据库重置完成！")
            print("\n管理员账户配置:")
            print(f"  用户名: {self.app.config.get('ADMIN_USERNAME', 'admin')}")
            print(f"  密码: {self.app.config.get('ADMIN_PASSWORD', 'admin123')}")
            print("  [警告] 如需修改请编辑 config.py 文件")
    
    def backup_database(self):
        """备份数据库"""
        print("=" * 60)
        print("备份数据库")
        print("=" * 60)
        
        with self.app.app_context():
            db_path = self.app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            
            if not db_path or not os.path.exists(db_path):
                print(f"[错误] 数据库文件不存在: {db_path}")
                sys.exit(1)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"database_backup_{timestamp}.db"
            
            print(f"[信息] 源文件: {db_path}")
            print(f"[信息] 备份到: {backup_file}")
            
            # 执行备份
            shutil.copy2(db_path, backup_file)
            
            # 显示备份文件大小
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            print(f"[完成] 备份完成！文件大小: {size_mb:.2f} MB")
            
            # 列出所有备份
            self._list_backups()
    
    def restore_database(self, backup_file):
        """从备份恢复数据库"""
        print("=" * 60)
        print("恢复数据库")
        print("=" * 60)
        
        if not os.path.exists(backup_file):
            print(f"[错误] 备份文件不存在: {backup_file}")
            sys.exit(1)
        
        print(f"[信息] 备份文件: {backup_file}")
        print("[警告] 此操作将覆盖当前数据库！")
        
        confirm = input("确认继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("操作已取消")
            return
        
        with self.app.app_context():
            db_path = self.app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            
            # 先备份当前数据库
            if os.path.exists(db_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                auto_backup = self.backup_dir / f"auto_backup_before_restore_{timestamp}.db"
                print(f"[信息] 自动备份当前数据库到: {auto_backup}")
                shutil.copy2(db_path, auto_backup)
            
            # 恢复备份
            print(f"[执行] 恢复数据库...")
            shutil.copy2(backup_file, db_path)
            print("[完成] 数据库恢复完成！")
            
            self._print_database_info()
    
    def show_admin_config(self):
        """显示管理员账户配置"""
        print("=" * 60)
        print("管理员账户配置")
        print("=" * 60)
        
        print("\n当前配置 (来自 config.py):")
        print("-" * 60)
        print(f"  用户名: {self.app.config.get('ADMIN_USERNAME', 'admin')}")
        print(f"  密码: {self.app.config.get('ADMIN_PASSWORD', 'admin123')}")
        
        print("\n如需修改管理员账户:")
        print("-" * 60)
        print("  1. 编辑 config.py 文件")
        print("  2. 找到以下配置项:")
        print("     ADMIN_USERNAME = 'admin'")
        print("     ADMIN_PASSWORD = 'admin123'")
        print("  3. 修改为您需要的值")
        print("  4. 重启应用使配置生效")
        
        print("\n[警告] 安全提示:")
        print("-" * 60)
        print("  - 生产环境请务必修改默认密码")
        print("  - 建议使用复杂密码 (字母+数字+特殊字符)")
        print("  - 不要在代码中硬编码密码，建议使用环境变量")
    
    def show_status(self):
        """显示数据库状态"""
        print("=" * 60)
        print("数据库状态")
        print("=" * 60)
        
        with self.app.app_context():
            self._print_database_info()
            
            # 显示数据统计
            print("\n数据统计:")
            print("-" * 60)
            
            try:
                video_count = Video.query.count()
                print(f"  视频总数: {video_count}")
                
                localized_count = Video.query.filter_by(is_localized=True).count()
                print(f"  已本地化图片: {localized_count}")
                
                unlocalized_count = video_count - localized_count
                print(f"  未本地化图片: {unlocalized_count}")
                
                # 统计各分类数量
                from sqlalchemy import func
                categories = db.session.query(
                    Video.vod_class, 
                    func.count(Video.id).label('count')
                ).group_by(Video.vod_class).limit(10).all()
                
                if categories:
                    print(f"\n  热门分类 (前10):")
                    for cat, count in categories:
                        print(f"    - {cat}: {count} 个视频")
                
            except Exception as e:
                print(f"  无法获取数据统计: {str(e)}")
            
            # 显示备份列表
            print("\n")
            self._list_backups()
    

    
    def _print_database_info(self):
        """打印数据库信息"""
        db_uri = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_path = db_uri.replace('sqlite:///', '')
        
        print("\n数据库信息:")
        print("-" * 60)
        print(f"  类型: SQLite")
        print(f"  路径: {db_path}")
        
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"  大小: {size_mb:.2f} MB")
            mod_time = datetime.fromtimestamp(os.path.getmtime(db_path))
            print(f"  最后修改: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  状态: 文件不存在")
    
    def _list_backups(self):
        """列出所有备份文件"""
        backups = sorted(self.backup_dir.glob('*.db'), key=os.path.getmtime, reverse=True)
        
        if not backups:
            print("备份文件:")
            print("-" * 60)
            print("  (无备份文件)")
            return
        
        print("备份文件:")
        print("-" * 60)
        for backup in backups[:10]:  # 只显示最近10个备份
            size_mb = os.path.getsize(backup) / (1024 * 1024)
            mod_time = datetime.fromtimestamp(os.path.getmtime(backup))
            print(f"  {backup.name}")
            print(f"    大小: {size_mb:.2f} MB")
            print(f"    时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if len(backups) > 10:
            print(f"  ... 还有 {len(backups) - 10} 个备份文件")


def print_usage():
    """打印使用说明"""
    print(__doc__)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = DatabaseManager()
    
    commands = {
        'init': manager.init_database,
        'upgrade': manager.upgrade_database,
        'downgrade': manager.downgrade_database,
        'reset': manager.reset_database,
        'backup': manager.backup_database,
        'admin': manager.show_admin_config,
        'status': manager.show_status,
    }
    
    if command == 'restore':
        if len(sys.argv) < 3:
            print("[错误] 请指定备份文件路径")
            print("用法: python3 db_manager.py restore <备份文件路径>")
            sys.exit(1)
        manager.restore_database(sys.argv[2])
    elif command in commands:
        commands[command]()
    else:
        print(f"[错误] 未知命令: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
