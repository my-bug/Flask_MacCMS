# 常见问题解答

## 安装和启动

### Q1: 启动时报错 "ModuleNotFoundError"

原因: 未安装依赖包

解决:
```bash
pip install -r requirements.txt
```

### Q2: 端口5002已被占用

解决方案1: 修改端口
```python
# config.py
PORT = 5003  # 改为其他端口
```

解决方案2: 关闭占用端口的进程
```bash
# macOS/Linux
lsof -ti:5002 | xargs kill -9

# Windows
netstat -ano | findstr :5002
taskkill /PID <进程ID> /F
```

### Q3: 数据库文件权限错误

解决:
```bash
chmod 755 instance
chmod 644 instance/videos.db
```

## 采集问题

### Q4: 采集失败，显示连接错误

检查清单:
- [ ] 采集源URL是否正确
- [ ] 网络连接是否正常
- [ ] 采集源服务器是否在线
- [ ] 是否有防火墙拦截

测试方法:
```bash
curl -I "https://aosikazy.com/api.php/provide/vod?ac=detail"
```

### Q5: 采集速度很慢

原因: 网络延迟或服务器响应慢

优化:
```python
# collector.py
self.timeout = 10  # 减少超时时间
```

### Q6: 采集到的视频重复

说明: 这是正常的，系统会自动跳过重复视频

配置:
- 勾选"更新已存在的视频"会更新重复视频
- 不勾选则跳过重复视频
- 连续20个重复会自动停止采集

### Q7: 分类列表为空

原因:
1. 未从API获取分类
2. 分类API地址错误
3. API返回数据格式不正确

解决:
```
1. 进入"采集源管理"
2. 点击"分类"
3. 点击"从API获取分类"
4. 检查返回结果
```

测试API:
```bash
curl "https://aosikazy.com/api.php/provide/vod?ac=list"
```

## 视频播放

### Q8: 视频无法播放，显示"ERR_CONNECTION_RESET"

原因: 视频源服务器问题，不是代码问题

可能情况:
1. 视频文件已被删除
2. 视频服务器暂时不可用
3. 网络连接不稳定
4. 防盗链限制

解决:
1. 播放器会自动重试3-6次
2. 如果持续失败，视频源可能已失效
3. 重新采集视频
4. 更换其他采集源

### Q9: 视频播放卡顿

原因: 网络带宽不足或服务器速度慢

优化:
```javascript
// video_detail.html
maxBufferLength: 60,  // 增加缓冲
```

### Q10: 移动端播放异常

检查:
- iOS设备是否启用HLS原生支持
- Android设备是否支持HLS.js
- 浏览器是否为最新版本

## 数据库问题

### Q11: 数据库表不存在

解决:
```bash
# 删除旧数据库
rm instance/videos.db

# 重新启动应用，会自动创建表
python3 start.py
```

### Q12: 需要添加新字段

方法1: 使用迁移脚本
```bash
python3 migrate.py
```

方法2: 手动修改
```python
# models/video.py
new_field = db.Column(db.String(100), default='')
```

然后删除数据库重新创建（会丢失数据）

### Q13: 数据库损坏

恢复:
```bash
# 备份
cp instance/videos.db instance/videos.db.backup

# 尝试修复
sqlite3 instance/videos.db "PRAGMA integrity_check;"

# 如果无法修复，删除重建
rm instance/videos.db
python3 start.py
```

## URL问题

### Q14: 采集的URL格式不正确

现象: 包含 `第1集$` 或 `\/` 字符

解决: 系统已自动清理，如果旧数据有问题：
```bash
python3 clean_existing_urls.py
```

### Q15: 播放URL显示错误

检查:
1. 数据库中URL格式
2. 模板是否正确显示
3. JavaScript是否正确解析

测试:
```python
from app import create_app, db
from app.models.video import Video

app = create_app()
with app.app_context():
    video = Video.query.first()
    print(video.vod_play_url)
```

## 性能优化

### Q16: 首页加载慢

优化:
```python
# routes.py
per_page = 20  # 减少每页显示数量

# 添加索引
CREATE INDEX idx_vod_id ON videos(vod_id);
CREATE INDEX idx_type_id ON videos(type_id);
```

### Q17: 采集占用CPU高

优化:
```python
# collector.py
time.sleep(2)  # 增加请求间隔
```

### Q18: 内存占用过高

原因: SQLAlchemy缓存

解决:
```python
# 定期清理会话
db.session.expire_all()
```

## 系统维护

### Q19: 如何备份数据

数据库备份:
```bash
cp instance/videos.db backups/videos_$(date +%Y%m%d).db
```

完整备份:
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz \
  instance/ app/ config.py requirements.txt
```

### Q20: 如何清理日志

手动清理:
```bash
# 如果有日志文件
rm logs/*.log
```

自动清理:
```python
# 添加日志轮转
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=3)
```

## 开发问题

### Q21: 修改CSS/JS后不生效

原因: 浏览器缓存

解决:
1. 硬刷新: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)
2. 清除浏览器缓存
3. 使用无痕模式测试

### Q22: 修改Python代码后不生效

解决:
```bash
# 重启应用
Ctrl+C
python3 start.py
```

开发模式:
```python
# config.py
DEBUG = True  # 启用调试模式，自动重载
```

### Q23: 如何查看详细错误信息

开启调试:
```python
# config.py
DEBUG = True

# start.py
app.run(debug=True)
```

## 部署问题

### Q24: 生产环境部署

使用Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 "app:create_app()"
```

使用Nginx反向代理:
```nginx
location / {
    proxy_pass http://127.0.0.1:5002;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Q25: HTTPS配置

使用Nginx SSL:
```nginx
listen 443 ssl;
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;
```

---

更多问题？
- 查看日志文件
- 运行测试: `python3 test.py`
- 提交Issue到GitHub
