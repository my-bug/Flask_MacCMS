# 数据库迁移使用指南

## 概述

项目现在使用 Flask-Migrate（基于Alembic）来管理数据库迁移，无需手动编写SQL语句。

## 工作原理

Flask-Migrate 会自动：
1. 检测 `app/models/` 中的模型变化
2. 生成迁移脚本
3. 应用变更到数据库

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

这会安装 Flask-Migrate==4.0.5

### 2. 修改数据模型

在 `app/models/` 目录中修改你的模型，例如：

```python
# app/models/video.py
class Video(db.Model):
    # 添加新字段
    new_field = db.Column(db.String(100), default='')
    
    # 或修改现有字段
    vod_name = db.Column(db.String(300), nullable=False)  # 从200改为300
```

### 3. 运行迁移

```bash
python3 migrate.py
```

脚本会自动：
- 首次运行时初始化 `migrations/` 目录
- 检测模型变化
- 生成迁移脚本
- 应用到数据库

### 4. 查看结果

迁移成功后，你的数据库会自动更新为新的结构。

## 迁移目录结构

```
WEB_CMSMovie/
├── migrations/              # 迁移脚本目录（自动生成）
│   ├── versions/           # 版本历史
│   │   ├── xxxx_auto_migration.py
│   │   └── yyyy_auto_migration.py
│   ├── alembic.ini         # Alembic配置
│   └── env.py              # 环境配置
└── migrate.py              # 迁移入口脚本
```

## 常见场景

### 场景1：添加新字段

```python
# 在模型中添加字段
class CollectSource(db.Model):
    description = db.Column(db.Text, default='')  # 新增描述字段
```

运行 `python3 migrate.py` 即可。

### 场景2：修改字段类型

```python
# 修改字段长度
class Video(db.Model):
    vod_name = db.Column(db.String(500), nullable=False)  # 原来是200
```

运行 `python3 migrate.py` 即可。

### 场景3：删除字段

```python
# 删除不需要的字段
class Video(db.Model):
    # vod_old_field = db.Column(...)  # 注释或删除
    pass
```

运行 `python3 migrate.py` 即可。

## 高级用法

### 手动生成迁移脚本

```bash
# 进入Python环境
python3
```

```python
from flask_migrate import init, migrate, upgrade
from app import create_app, db

app = create_app()
with app.app_context():
    # 初始化（首次）
    init()
    
    # 生成迁移脚本
    migrate(message='添加新字段')
    
    # 应用迁移
    upgrade()
```

### 回滚迁移

```python
from flask_migrate import downgrade
from app import create_app

app = create_app()
with app.app_context():
    # 回滚到上一个版本
    downgrade()
```

### 查看迁移历史

```bash
# 查看migrations/versions/目录
ls -la migrations/versions/
```

## 优势

相比手动编写SQL：

1. 自动检测变化 - 无需记住修改了什么
2. 类型安全 - 基于Python模型定义
3. 版本控制 - 每次迁移都有记录
4. 可回滚 - 支持降级到旧版本
5. 跨数据库 - 同样的代码支持SQLite、MySQL、PostgreSQL
6. 团队协作 - migrations目录可提交到Git

## 注意事项

1. 首次运行 - 会创建 `migrations/` 目录
2. 数据安全 - 迁移前建议备份数据库
3. 冲突解决 - 多人开发时注意合并migrations目录
4. SQLite限制 - SQLite不支持某些ALTER操作（如改列名），Flask-Migrate会使用重建表的方式

## 故障排除

### 问题1：migrations目录已存在但有问题

```bash
# 删除migrations目录重新开始
rm -rf migrations/
python3 migrate.py
```

### 问题2：检测不到模型变化

确保：
- 模型已正确导入到 `app/__init__.py`
- 数据库连接正常
- 模型定义语法正确

### 问题3：迁移失败

检查：
- 数据库文件是否被锁定
- 权限是否足够
- 模型定义是否有冲突

## 与旧版本兼容

如果你的数据库是用旧的migrate.py（手动SQL）创建的：

1. 首次运行新migrate.py会初始化迁移系统
2. 它会将当前数据库状态作为基准
3. 后续变更都可以自动管理

## 示例：完整迁移流程

```bash
# 1. 修改模型
vim app/models/video.py

# 2. 运行迁移
python3 migrate.py

# 输出示例：
# [初始化] 首次运行，正在初始化迁移环境...
# [成功] 迁移环境初始化完成
# [检测] 正在检测数据库模型变化...
# [成功] 迁移脚本生成完成
# [执行] 正在应用数据库变更...
# [成功] 数据库更新完成！

# 3. 启动应用
python3 start.py
```

## 总结

现在你只需要：
1. 修改 models
2. 运行 `python3 migrate.py`
3. 完成！

不再需要手动写SQL，系统会自动处理一切。
