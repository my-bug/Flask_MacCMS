"""
视频数据模型

定义了视频信息的数据库表结构，包含90+个字段
支持完整的视频信息存储和管理
"""

from app import db
from datetime import datetime

class Video(db.Model):
    """
    视频信息模型
    
    存储从采集API获取的视频详细信息，包括：
    - 基本信息：名称、分类、年份、地区、语言等
    - 媒体信息：封面图、播放地址、下载地址等
    - 详情信息：导演、演员、剧情、评分等
    - 统计信息：点击量、评分数等
    """
    
    __tablename__ = 'videos'
    
    # 主键和唯一标识
    id = db.Column(db.Integer, primary_key=True, comment='自增主键')
    vod_id = db.Column(db.Integer, unique=True, nullable=False, comment='视频源ID，来自采集API')
    type_id = db.Column(db.Integer, default=0)
    type_id_1 = db.Column(db.Integer, default=0)
    group_id = db.Column(db.Integer, default=0)
    vod_name = db.Column(db.String(200), nullable=False)
    vod_sub = db.Column(db.String(200), default='')
    vod_en = db.Column(db.String(200), default='')
    vod_status = db.Column(db.Integer, default=1)
    vod_letter = db.Column(db.String(10), default='')
    vod_color = db.Column(db.String(20), default='')
    vod_tag = db.Column(db.String(100), default='')
    vod_class = db.Column(db.String(100), default='')
    vod_pic = db.Column(db.String(500), default='')
    vod_pic_thumb = db.Column(db.String(500), default='')
    vod_pic_slide = db.Column(db.String(500), default='')
    vod_actor = db.Column(db.String(200), default='')
    vod_director = db.Column(db.String(200), default='')
    vod_writer = db.Column(db.String(200), default='')
    vod_behind = db.Column(db.String(200), default='')
    vod_blurb = db.Column(db.Text, default='')
    vod_remarks = db.Column(db.String(100), default='')
    vod_pubdate = db.Column(db.String(20), default='')
    vod_total = db.Column(db.Integer, default=0)
    vod_serial = db.Column(db.String(20), default='0')
    vod_tv = db.Column(db.String(50), default='')
    vod_weekday = db.Column(db.String(20), default='')
    vod_area = db.Column(db.String(50), default='')
    vod_lang = db.Column(db.String(50), default='')
    vod_year = db.Column(db.String(10), default='')
    vod_version = db.Column(db.String(50), default='')
    vod_state = db.Column(db.String(50), default='')
    vod_author = db.Column(db.String(100), default='')
    vod_jumpurl = db.Column(db.String(500), default='')
    vod_tpl = db.Column(db.String(50), default='')
    vod_tpl_play = db.Column(db.String(50), default='')
    vod_tpl_down = db.Column(db.String(50), default='')
    vod_isend = db.Column(db.Integer, default=0)
    vod_lock = db.Column(db.Integer, default=0)
    vod_level = db.Column(db.Integer, default=0)
    vod_points_play = db.Column(db.Integer, default=0)
    vod_points_down = db.Column(db.Integer, default=0)
    vod_hits = db.Column(db.Integer, default=0)
    vod_hits_day = db.Column(db.Integer, default=0)
    vod_hits_week = db.Column(db.Integer, default=0)
    vod_hits_month = db.Column(db.Integer, default=0)
    vod_duration = db.Column(db.String(20), default='')
    vod_up = db.Column(db.Integer, default=0)
    vod_down = db.Column(db.Integer, default=0)
    vod_score = db.Column(db.String(10), default='0.0')
    vod_score_all = db.Column(db.Integer, default=0)
    vod_score_num = db.Column(db.Integer, default=0)
    vod_time = db.Column(db.String(50), default='')
    vod_time_add = db.Column(db.Integer, default=0)
    vod_time_hits = db.Column(db.Integer, default=0)
    vod_time_make = db.Column(db.Integer, default=0)
    vod_trysee = db.Column(db.Integer, default=0)
    vod_douban_id = db.Column(db.Integer, default=0)
    vod_douban_score = db.Column(db.String(10), default='0.0')
    vod_reurl = db.Column(db.String(500), default='')
    vod_rel_vod = db.Column(db.String(200), default='')
    vod_rel_art = db.Column(db.String(200), default='')
    vod_content = db.Column(db.Text, default='')
    vod_play_from = db.Column(db.String(50), default='')
    vod_play_server = db.Column(db.String(50), default='')
    vod_play_note = db.Column(db.String(200), default='')
    vod_play_url = db.Column(db.String(1000), default='')
    vod_down_from = db.Column(db.String(50), default='')
    vod_down_server = db.Column(db.String(50), default='')
    vod_down_note = db.Column(db.String(200), default='')
    vod_down_url = db.Column(db.String(1000), default='')
    vod_pwd = db.Column(db.String(50), default='')
    vod_pwd_url = db.Column(db.String(500), default='')
    vod_pwd_play = db.Column(db.String(50), default='')
    vod_pwd_play_url = db.Column(db.String(500), default='')
    vod_pwd_down = db.Column(db.String(50), default='')
    vod_pwd_down_url = db.Column(db.String(500), default='')
    vod_copyright = db.Column(db.Integer, default=0)
    vod_points = db.Column(db.Integer, default=0)
    vod_plot = db.Column(db.Integer, default=0)
    vod_plot_name = db.Column(db.String(100), default='')
    vod_plot_detail = db.Column(db.Text, default='')
    type_name = db.Column(db.String(100), default='')
    
    # 图片本地化字段
    local_pic = db.Column(db.String(200), default='', comment='本地化图片文件名')
    is_localized = db.Column(db.Boolean, default=False, comment='图片是否已本地化')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """
        模型的字符串表示形式
        
        Returns:
            str: 返回包含视频名称的字符串
        """
        return f'<Video {self.vod_name}>'
    
    def get_picture_url(self):
        """
        获取图片URL，优先返回本地化图片
        
        Returns:
            str: 图片URL路径
        """
        if self.is_localized and self.local_pic:
            return f'/static/uploads/posters/{self.local_pic}'
        return self.vod_pic or 'https://via.placeholder.com/300x400'
    
    def delete_local_image(self):
        """
        删除本地化的图片文件
        
        在删除视频记录时调用，清理本地存储的图片文件
        """
        import os
        if self.is_localized and self.local_pic:
            upload_folder = 'app/static/uploads/posters'
            file_path = os.path.join(upload_folder, self.local_pic)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    return True
                except Exception as e:
                    print(f'删除图片文件失败: {file_path}, 错误: {str(e)}')
                    return False
        return False
    
    def to_dict(self):
        """
        将视频对象转换为字典格式
        
        用于API响应和JSON序列化，只返回常用字段
        
        Returns:
            dict: 包含视频基本信息的字典
        """
        return {
            'vod_id': self.vod_id,  # 视频ID
            'vod_name': self.vod_name,  # 视频名称
            'vod_pic': self.get_picture_url(),  # 封面图片URL（优先本地化）
            'vod_class': self.vod_class,  # 分类标签
            'vod_year': self.vod_year,  # 发行年份
            'vod_score': self.vod_score,  # 评分
            'vod_hits': self.vod_hits,  # 总点击量
            'vod_play_url': self.vod_play_url,  # 播放地址
            'type_name': self.type_name  # 分类名称
        }
