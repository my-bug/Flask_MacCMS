"""
图片下载器模块

该模块负责下载视频封面图片到本地服务器
- 多线程下载图片
- 自动重试机制
- 支持启动和停止
- 更新数据库中的图片路径
- 线程安全的数据库操作
"""

import requests
import os
import time
import threading
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from app.models.video import Video
from app.models.system_log import SystemLog
from app import db
from werkzeug.utils import secure_filename
import hashlib
from urllib.parse import urlparse


class ImageDownloader:
    """
    图片下载器类
    
    负责从远程URL下载视频封面图片并保存到本地
    支持多线程并发下载
    """
    
    def __init__(self, app=None, upload_folder='app/static/uploads/posters', timeout=30, max_retries=3, max_workers=10):
        """
        初始化图片下载器
        
        Args:
            app: Flask应用实例
            upload_folder (str): 图片保存的文件夹路径
            timeout (int): 下载超时时间（秒）
            max_retries (int): 下载失败时的最大重试次数
            max_workers (int): 最大工作线程数
        """
        self.app = app
        self.upload_folder = upload_folder
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_workers = max_workers
        
        self.success_count = 0
        self.failed_count = 0
        self.skip_count = 0
        self.errors = []
        self.is_running = False
        self.should_stop = False
        self.current_video = None
        self.total_videos = 0
        self.processed_count = 0
        
        # 线程锁，用于保护共享资源
        self.count_lock = threading.Lock()
        self.db_lock = threading.Lock()
        
        # 确保上传文件夹存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def _create_session(self):
        """
        创建带重试机制的requests会话（线程本地）
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        })
        return session
    
    def _generate_filename(self, url, vod_id):
        """
        生成唯一的文件名
        
        Args:
            url (str): 图片URL
            vod_id (int): 视频ID
            
        Returns:
            str: 生成的文件名
        """
        # 获取文件扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1].lower()
        
        # 如果没有扩展名，默认使用.jpg
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            ext = '.jpg'
        
        # 使用视频ID和URL的MD5生成唯一文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"poster_{vod_id}_{url_hash}{ext}"
        
        return secure_filename(filename)
    
    def download_image(self, url, save_path):
        """
        下载单张图片（线程安全）
        
        Args:
            url (str): 图片URL
            save_path (str): 保存路径
            
        Returns:
            bool: 下载是否成功
        """
        # 每个线程创建自己的session
        session = self._create_session()
        
        for attempt in range(self.max_retries):
            try:
                response = session.get(url, timeout=self.timeout, stream=True, verify=False)
                response.raise_for_status()
                
                # 写入文件
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                session.close()
                return True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # 递增延迟
                else:
                    with self.count_lock:
                        self.errors.append(f"下载失败 {url}: {str(e)}")
                    session.close()
                    return False
            except Exception as e:
                with self.count_lock:
                    self.errors.append(f"保存失败 {save_path}: {str(e)}")
                session.close()
                return False
        
        session.close()
        return False
    
    def verify_local_image(self, video):
        """
        验证本地图片是否真实存在
        
        Args:
            video (Video): 视频对象
            
        Returns:
            bool: 本地图片是否存在
        """
        if not video.is_localized or not video.local_pic:
            return False
        
        file_path = os.path.join(self.upload_folder, video.local_pic)
        exists = os.path.exists(file_path)
        
        # 如果数据库标记为已本地化但文件不存在，重置标记
        if not exists:
            try:
                video.is_localized = False
                video.local_pic = ''
                db.session.commit()
            except:
                db.session.rollback()
        
        return exists
    
    def process_video(self, video_id):
        """
        处理单个视频的图片下载（线程安全）
        
        Args:
            video_id (int): 视频ID
            
        Returns:
            str: 处理结果 'success', 'skip', 'error'
        """
        # 在Flask应用上下文中执行
        with self.app.app_context():
            # 每个线程单独查询数据库
            with self.db_lock:
                video = db.session.query(Video).filter_by(id=video_id).first()
                if not video:
                    return 'error'
                
                # 验证本地化状态，检查文件是否真实存在
                if video.is_localized and video.local_pic:
                    file_path = os.path.join(self.upload_folder, video.local_pic)
                    if os.path.exists(file_path):
                        # 文件存在，跳过
                        with self.count_lock:
                            self.skip_count += 1
                        return 'skip'
                    else:
                        # 文件不存在，重置标记
                        video.is_localized = False
                        video.local_pic = ''
                        db.session.commit()
                
                # 检查是否有有效的图片URL
                if not video.vod_pic or not video.vod_pic.startswith('http'):
                    with self.count_lock:
                        self.skip_count += 1
                    return 'skip'
                
                # 获取必要的信息
                vod_name = video.vod_name
                vod_pic = video.vod_pic
            
            try:
                # 设置当前处理的视频名称
                with self.count_lock:
                    self.current_video = vod_name
                
                # 生成文件名和保存路径
                filename = self._generate_filename(vod_pic, video_id)
                save_path = os.path.join(self.upload_folder, filename)
                
                # 如果文件已存在，只更新数据库
                if os.path.exists(save_path):
                    with self.db_lock:
                        video = db.session.query(Video).filter_by(id=video_id).first()
                        if video:
                            video.local_pic = filename
                            video.is_localized = True
                            db.session.commit()
                    with self.count_lock:
                        self.success_count += 1
                    return 'success'
                
                # 下载图片
                if self.download_image(vod_pic, save_path):
                    # 更新数据库中的本地化字段
                    with self.db_lock:
                        video = db.session.query(Video).filter_by(id=video_id).first()
                        if video:
                            video.local_pic = filename
                            video.is_localized = True
                            db.session.commit()
                    
                    with self.count_lock:
                        self.success_count += 1
                    return 'success'
                else:
                    with self.count_lock:
                        self.failed_count += 1
                    # 记录下载失败日志
                    with self.db_lock:
                        SystemLog.log(
                            log_type='download',
                            level='warning',
                            module='ImageDownloader',
                            message=f'图片下载失败: {vod_name} (ID: {video_id})',
                            details=vod_pic
                        )
                    return 'error'
                    
            except Exception as e:
                with self.db_lock:
                    db.session.rollback()
                    error_msg = f"处理视频失败 (ID: {video_id}): {str(e)}"
                    SystemLog.log(
                        log_type='download',
                        level='error',
                        module='ImageDownloader',
                        message=error_msg,
                        details=str(e)
                    )
                
                with self.count_lock:
                    self.errors.append(error_msg)
                    self.failed_count += 1
                
                return 'error'
    
    def stop(self):
        """停止下载任务"""
        self.should_stop = True
    
    def verify_all_localized(self):
        """
        验证所有已标记为本地化的视频，检查文件是否真实存在
        
        Returns:
            dict: 验证结果统计
        """
        print("开始验证本地化图片:")
        print(f"  - 图片目录: {self.upload_folder}")
        print("-" * 60)
        
        # 获取所有标记为已本地化的视频
        localized_videos = Video.query.filter_by(is_localized=True).all()
        total = len(localized_videos)
        fixed_count = 0
        valid_count = 0
        
        print(f"找到 {total} 个标记为已本地化的视频")
        
        for video in localized_videos:
            if video.local_pic:
                file_path = os.path.join(self.upload_folder, video.local_pic)
                
                if os.path.exists(file_path):
                    valid_count += 1
                else:
                    # 文件不存在，重置本地化标记
                    try:
                        print(f"修复: {video.vod_name} (ID: {video.id}) - 文件不存在: {video.local_pic}")
                        video.is_localized = False
                        video.local_pic = ''
                        db.session.commit()
                        fixed_count += 1
                    except Exception as e:
                        db.session.rollback()
                        print(f"  错误: {str(e)}")
        
        print("-" * 60)
        print(f"验证完成！")
        print(f"  - 有效: {valid_count}")
        print(f"  - 修复: {fixed_count}")
        
        # 记录验证结果日志
        SystemLog.log(
            log_type='download',
            level='info',
            module='ImageDownloader',
            message=f'本地化验证完成: 总计{total}, 有效{valid_count}, 修复{fixed_count}'
        )
        
        return {
            'total': total,
            'valid': valid_count,
            'fixed': fixed_count
        }
    
    def download_all(self):
        """
        下载所有视频的图片（多线程）
        
        Returns:
            dict: 下载结果统计
        """
        # 重置计数器和状态
        self.success_count = 0
        self.failed_count = 0
        self.skip_count = 0
        self.errors = []
        self.is_running = True
        self.should_stop = False
        self.processed_count = 0
        
        try:
            print("开始下载视频图片:")
            print(f"  - 保存路径: {self.upload_folder}")
            print(f"  - 超时时间: {self.timeout}秒")
            print(f"  - 最大重试: {self.max_retries}次")
            print(f"  - 线程数: {self.max_workers}")
            print("-" * 60)
            
            # 获取所有需要下载图片的视频ID
            videos = Video.query.filter(
                Video.vod_pic.isnot(None),
                Video.vod_pic != ''
            ).with_entities(Video.id).all()
            
            video_ids = [v.id for v in videos]
            self.total_videos = len(video_ids)
            print(f"找到 {self.total_videos} 个视频需要处理")
            
            # 使用线程池处理视频
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_video = {executor.submit(self.process_video, video_id): video_id 
                                   for video_id in video_ids}
                
                # 处理完成的任务
                for future in as_completed(future_to_video):
                    if self.should_stop:
                        print("下载任务被手动停止")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    video_id = future_to_video[future]
                    try:
                        result = future.result()
                        with self.count_lock:
                            self.processed_count += 1
                            
                            if self.processed_count % 10 == 0:
                                print(f"进度: {self.processed_count}/{self.total_videos} - "
                                      f"成功: {self.success_count}, 失败: {self.failed_count}, 跳过: {self.skip_count}")
                    except Exception as e:
                        with self.count_lock:
                            self.processed_count += 1
                            self.failed_count += 1
                            self.errors.append(f"线程异常 (视频ID: {video_id}): {str(e)}")
            
            print("-" * 60)
            print(f"图片下载完成！")
            print(f"  - 成功: {self.success_count}")
            print(f"  - 失败: {self.failed_count}")
            print(f"  - 跳过: {self.skip_count}")
            
        finally:
            self.is_running = False
        
        return self.get_result()
    
    def get_result(self):
        """
        获取下载结果
        
        Returns:
            dict: 结果字典
        """
        return {
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skip_count': self.skip_count,
            'total_videos': self.total_videos,
            'processed_count': self.processed_count,
            'current_video': self.current_video,
            'is_running': self.is_running,
            'errors': self.errors[:50]  # 只返回前50个错误
        }
