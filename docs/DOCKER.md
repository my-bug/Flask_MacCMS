# Docker 部署指南

## 快速开始

### 1. 构建镜像

```bash
docker build -t cmsmovie:latest .
```

### 2. 使用 Docker Compose 启动

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件修改管理员密码和密钥
nano .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 初始化数据库

```bash
docker exec -it cmsmovie python3 db_manager.py init
```

### 4. 访问应用

```
http://localhost:5000
```

## 手动 Docker 命令

### 构建镜像

```bash
docker build -t cmsmovie:latest .
```

### 运行容器

```bash
docker run -d \
  --name cmsmovie \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/backups:/app/backups \
  -v $(pwd)/app/static/uploads:/app/app/static/uploads \
  -v $(pwd)/logs:/app/logs \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=your-password \
  -e SECRET_KEY=your-secret-key \
  cmsmovie:latest
```

### 常用命令

```bash
# 查看日志
docker logs -f cmsmovie

# 进入容器
docker exec -it cmsmovie bash

# 停止容器
docker stop cmsmovie

# 启动容器
docker start cmsmovie

# 重启容器
docker restart cmsmovie

# 删除容器
docker rm -f cmsmovie
```

## 数据持久化

容器使用以下卷进行数据持久化:

- `./instance` - 数据库文件
- `./backups` - 数据库备份
- `./app/static/uploads` - 上传的图片
- `./logs` - 应用日志

## 环境变量配置

在 `.env` 文件中配置以下环境变量:

```bash
# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Flask密钥(必须修改)
SECRET_KEY=your-very-long-random-secret-key

# Flask环境
FLASK_ENV=production
```

## 数据库管理

### 备份数据库

```bash
docker exec cmsmovie python3 db_manager.py backup
```

### 恢复数据库

```bash
docker exec cmsmovie python3 db_manager.py restore backups/database_backup_YYYYMMDD_HHMMSS.db
```

### 查看数据库状态

```bash
docker exec cmsmovie python3 db_manager.py status
```

## 生产环境建议

### 1. 使用外部数据库

修改 `docker-compose.yml` 添加 PostgreSQL 或 MySQL:

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: cmsmovie
      POSTGRES_USER: cmsmovie
      POSTGRES_PASSWORD: secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    depends_on:
      - db
    environment:
      - SQLALCHEMY_DATABASE_URI=postgresql://cmsmovie:secure-password@db:5432/cmsmovie

volumes:
  postgres_data:
```

### 2. 使用 Nginx 反向代理

创建 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://cmsmovie:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

添加到 `docker-compose.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web
```

### 3. 启用 HTTPS

使用 Let's Encrypt:

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
echo "0 0 * * * certbot renew" | crontab -
```

### 4. 资源限制

在 `docker-compose.yml` 中添加:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

### 5. 健康检查

健康检查已在 Dockerfile 中配置,容器会自动监控应用状态。

## 故障排除

### 容器无法启动

```bash
# 查看详细日志
docker logs cmsmovie

# 检查容器状态
docker ps -a
```

### 端口冲突

修改 `docker-compose.yml` 中的端口映射:

```yaml
ports:
  - "8080:5000"  # 使用8080端口
```

### 权限问题

```bash
# 修复文件权限
chmod -R 755 instance backups app/static/uploads logs
```

### 数据库初始化失败

```bash
# 删除旧数据库
rm -f instance/cms.db

# 重新初始化
docker exec cmsmovie python3 db_manager.py init
```

## 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d

# 升级数据库
docker exec cmsmovie python3 db_manager.py upgrade
```

## 备份策略

### 自动备份

创建定时任务:

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨3点备份
0 3 * * * docker exec cmsmovie python3 db_manager.py backup
```

### 手动备份

```bash
# 备份数据库
docker exec cmsmovie python3 db_manager.py backup

# 备份整个数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz instance backups app/static/uploads
```

## 监控

### 查看资源使用

```bash
docker stats cmsmovie
```

### 查看实时日志

```bash
docker-compose logs -f --tail=100
```

## 支持

如遇问题,请检查:
1. Docker 日志: `docker logs cmsmovie`
2. 应用日志: `docker exec cmsmovie cat logs/app.log`
3. 容器状态: `docker ps -a`
4. 数据库状态: `docker exec cmsmovie python3 db_manager.py status`
