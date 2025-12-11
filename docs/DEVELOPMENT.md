# 开发指南

## 开发环境设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd WEB_CMSMovie
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置开发环境

```python
# config.py
class Config:
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/cms.db'
```

### 5. 启动应用

```bash
# 完整启动(推荐)
python3 start.py

# 快速启动
python3 run.py
```

访问: http://localhost:5002

## 项目架构

### MVC架构

```
Model (模型) -> app/models/
View (视图)  -> app/templates/
Controller   -> app/blueprints/
```

### 蓝图结构

```python
# app/blueprints/admin/__init__.py
from flask import Blueprint
admin_bp = Blueprint('admin', __name__)

# app/blueprints/admin/routes.py
from . import admin_bp

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html')
```

### 数据模型

```python
# app/models/video.py
class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    vod_id = db.Column(db.Integer, unique=True, nullable=False)
    vod_name = db.Column(db.String(200), nullable=False)
    # ... 其他字段
```

## 添加新功能

### 1. 添加新路由

```python
# app/blueprints/admin/routes.py

@admin_bp.route('/new-feature')
@login_required
def new_feature():
    """新功能路由"""
    return render_template('admin/new_feature.html')
```

### 2. 添加新模型

```python
# app/models/new_model.py
from app import db
from datetime import datetime

class NewModel(db.Model):
    __tablename__ = 'new_table'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<NewModel {self.name}>'
```

### 3. 添加新模板

```html
<!-- app/templates/admin/new_feature.html -->
{% extends "admin/base.html" %}

{% block title %}新功能{% endblock %}

{% block content %}
<div class="container">
    <h2>新功能</h2>
    <!-- 内容 -->
</div>
{% endblock %}
```

### 4. 添加静态资源

```javascript
// app/static/js/new_feature.js
document.addEventListener('DOMContentLoaded', function() {
    // 初始化代码
});
```

```css
/* app/static/css/new_feature.css */
.new-feature {
    /* 样式 */
}
```

## 数据库操作

### 查询

```python
# 查询所有
videos = Video.query.all()

# 条件查询
video = Video.query.filter_by(vod_id=123).first()

# 复杂查询
videos = Video.query.filter(
    Video.vod_name.like('%关键词%')
).order_by(Video.created_at.desc()).limit(10).all()

# 分页
page = Video.query.paginate(page=1, per_page=20)
```

### 添加

```python
new_video = Video(
    vod_id=123,
    vod_name='测试视频'
)
db.session.add(new_video)
db.session.commit()
```

### 更新

```python
video = Video.query.get(1)
video.vod_name = '新名称'
db.session.commit()
```

### 删除

```python
video = Video.query.get(1)
db.session.delete(video)
db.session.commit()
```

## 采集器扩展

### 自定义采集器

```python
# app/collectors/custom_collector.py
from app.collectors.collector import VideoCollector

class CustomCollector(VideoCollector):
    """自定义采集器"""
    
    def parse_video_data(self, video_json):
        """重写解析方法"""
        data = super().parse_video_data(video_json)
        # 自定义处理
        data['custom_field'] = video_json.get('custom')
        return data
```

### 使用自定义采集器

```python
from app.collectors.custom_collector import CustomCollector

collector = CustomCollector(
    url='https://api.example.com',
    timeout=30
)
result = collector.collect()
```

## 前端开发

### Material Design组件

```html
<!-- 按钮 -->
<button class="btn btn-primary">主要按钮</button>
<button class="btn btn-secondary">次要按钮</button>

<!-- 卡片 -->
<div class="card">
    <div class="card-image">
        <img src="image.jpg" alt="封面">
    </div>
    <div class="card-content">
        <h3>标题</h3>
        <p>内容</p>
    </div>
</div>

<!-- 表单 -->
<div class="form-group">
    <label for="input">标签</label>
    <input type="text" id="input" name="input">
</div>
```

### JavaScript工具函数

```javascript
// 发送AJAX请求
function fetchData(url, callback) {
    fetch(url)
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => console.error('Error:', error));
}

// 显示提示
function showMessage(message, type = 'info') {
    const msg = document.createElement('div');
    msg.className = `message message-${type}`;
    msg.textContent = message;
    document.body.appendChild(msg);
    
    setTimeout(() => msg.remove(), 3000);
}
```

## 测试

### 编写测试

```python
# tests/test_collector.py
def test_url_cleaning():
    """测试URL清理"""
    from app.collectors.collector import VideoCollector
    
    collector = VideoCollector('http://test.com')
    
    input_url = r'第1集$https:\/\/test.com\/video.m3u8'
    expected = 'https://test.com/video.m3u8'
    
    result = collector.clean_play_urls_in_data(input_url)
    
    assert result == expected, f"Expected {expected}, got {result}"
```

### 运行测试

```bash
# 运行所有测试
python3 test.py

# 运行特定测试
python3 -m pytest tests/test_collector.py -v
```

## 调试技巧

### 使用Flask调试工具

```python
# 启用调试模式
app.run(debug=True)
```

### 打印调试

```python
# 使用print
print(f"Debug: {variable}")

# 使用Flask日志
from flask import current_app
current_app.logger.debug(f"Debug message: {variable}")
```

### 使用断点

```python
# 设置断点
import pdb; pdb.set_trace()

# 或使用breakpoint() (Python 3.7+)
breakpoint()
```

### Chrome DevTools

1. 打开开发者工具: `F12`
2. Network标签: 查看网络请求
3. Console标签: 查看JavaScript错误
4. Elements标签: 检查HTML/CSS

## 性能优化

### 数据库优化

```python
# 使用索引
class Video(db.Model):
    vod_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    type_id = db.Column(db.Integer, index=True)

# 批量插入
db.session.bulk_insert_mappings(Video, video_list)
db.session.commit()

# 懒加载关系
categories = db.relationship('Category', lazy='dynamic')
```

### 缓存

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_videos():
    return Video.query.all()
```

### 静态资源压缩

```bash
# 压缩CSS
pip install rcssmin
python -m rcssmin < material.css > material.min.css

# 压缩JS
pip install rjsmin
python -m rjsmin < main.js > main.min.js
```

## 代码规范

### Python风格 (PEP 8)

```python
# 导入顺序
import os  # 标准库
import sys

from flask import Flask  # 第三方库

from app.models import Video  # 本地模块

# 命名规范
class VideoCollector:  # 类名: PascalCase
    def collect_videos(self):  # 方法名: snake_case
        max_retry = 3  # 变量名: snake_case
        API_URL = 'https://...'  # 常量: UPPER_CASE
```

### 注释规范

```python
def function_name(param1, param2):
    """
    函数功能简述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    
    Raises:
        异常说明
    """
    pass
```

### Git提交规范

```bash
# 提交格式
git commit -m "feat: 添加新功能"
git commit -m "fix: 修复bug"
git commit -m "docs: 更新文档"
git commit -m "style: 代码格式化"
git commit -m "refactor: 代码重构"
git commit -m "test: 添加测试"
```

## 部署指南

### 使用Gunicorn

```bash
# 安装
pip install gunicorn

# 运行
gunicorn -w 4 -b 0.0.0.0:5002 "app:create_app()"

# 配置文件 gunicorn.conf.py
bind = "0.0.0.0:5002"
workers = 4
threads = 2
timeout = 120
```

### 使用Supervisor

```ini
[program:flask-cms]
command=/path/to/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"
directory=/path/to/WEB_CMSMovie
user=www-data
autostart=true
autorestart=true
```

### 使用Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
```

---

开发愉快！

如有问题，欢迎提交Issue或PR。
