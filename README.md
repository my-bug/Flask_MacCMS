# CMS Movie - 影视内容管理系统

一个基于 Flask 的现代化影视内容管理系统,支持MacCMS10通用采集接口,图片本地化下载,完整的后台管理功能。

## 主要特性

- 视频管理: 完整的视频信息管理和展示
- MacCMS10采集: 支持所有标准MacCMS10资源站接口
- 多线程图片下载: 10线程并发本地化存储
- macOS风格界面: 现代化响应式设计
- 用户认证: 完整的登录和权限管理
- 数据库迁移: 支持Flask-Migrate自动迁移
- 系统日志: 完整的操作日志记录

## 快速开始

### 环境要求

- Python 3.14.0
- pip

### 安装部署

#### 方式一: 传统部署

1. 安装依赖
```bash
pip3 install -r requirements.txt
```

2. 初始化数据库
```bash
python3 db_manager.py init
```

3. 启动应用
```bash
# 方式1: 使用start.py(推荐,包含检查和初始化)
python3 start.py

# 方式2: 直接运行
python3 run.py
```

#### 方式二: Docker部署 (推荐)

1. 使用Docker Compose
```bash
# 复制环境变量配置
cp .env.example .env

# 启动服务
docker-compose up -d

# 初始化数据库
docker exec -it cmsmovie python3 db_manager.py init
```

2. 查看详细的Docker部署文档: [docs/DOCKER.md](docs/DOCKER.md)

### 访问系统

传统部署:
```
前台: http://localhost:5002/
后台: http://localhost:5002/admin/login
```

Docker部署:
```
前台: http://localhost:5000/
后台: http://localhost:5000/admin/login
```

### 管理员账户

默认账户配置在 `config.py` 中:
- 用户名: admin
- 密码: admin

生产环境请修改 ADMIN_USERNAME 和 ADMIN_PASSWORD 配置项。

查看当前配置: `python3 db_manager.py admin`

## 命令速查

### 启动应用

```bash
python3 start.py      # 完整启动(检查依赖+初始化+运行)
python3 run.py        # 快速启动(仅运行)
```

### 数据库管理

```bash
python3 db_manager.py init          # 初始化数据库
python3 db_manager.py status        # 查看状态
python3 db_manager.py backup        # 备份数据库
python3 db_manager.py restore FILE  # 恢复数据库
python3 db_manager.py admin         # 查看管理员配置
python3 db_manager.py upgrade       # 升级数据库
python3 db_manager.py reset         # 重置数据库(危险)

## 项目结构

```
WEB_CMSMovie/
├── app/                      # 应用核心
│   ├── blueprints/          # 路由蓝图
│   │   ├── admin/          # 后台管理
│   │   └── frontend/       # 前台展示
│   ├── collectors/         # MacCMS10采集器
│   ├── downloaders/        # 图片下载器
│   ├── models/             # 数据库模型
│   ├── static/             # 静态资源
│   └── templates/          # 模板文件
├── backups/                # 数据库备份
├── docs/                   # 项目文档
├── instance/               # 实例数据(数据库)
├── migrations/             # 数据库迁移脚本
├── config.py              # 配置文件
├── db_manager.py          # 数据库管理工具
├── run.py                 # 快速启动入口
└── start.py               # 完整启动脚本
```

## 文档

- [Docker部署](docs/DOCKER.md) - Docker容器化部署完整指南
- [采集器文档](docs/MACCMS_COLLECTOR.md) - MacCMS10采集器使用指南
- [数据库迁移](docs/DATABASE_MIGRATION.md) - Flask-Migrate使用说明
- [API文档](docs/API.md) - MacCMS10 API接口说明
- [开发指南](docs/DEVELOPMENT.md) - 开发环境和代码规范
- [常见问题](docs/FAQ.md) - 问题排查和解决方案

## 技术栈

- Flask 3.0 - Web框架
- SQLAlchemy 3.1 - ORM
- Flask-Login - 用户认证
- Flask-Migrate - 数据库迁移
- Requests - HTTP客户端
- lxml - XML解析
- ThreadPoolExecutor - 并发处理

## 许可证

本项目仅供学习和研究使用。

---

Python 3.14.0
