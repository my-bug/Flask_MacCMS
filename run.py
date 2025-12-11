"""
Flask应用运行入口

简单的运行脚本，用于开发环境快速启动
生产环境建议使用 start.py 或 WSGI服务器（如gunicorn）
"""

from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 启动开发服务器
    # debug=True: 启用调试模式，代码修改后自动重载
    # host='127.0.0.1': 只允许本地访问
    # port=5002: 监听5002端口
    app.run(debug=True, host='127.0.0.1', port=5002)
