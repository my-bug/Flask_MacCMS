from flask import render_template, request, redirect, url_for
from app.blueprints.frontend import frontend_bp
from app.models.video import Video
from app import db
from sqlalchemy import func

@frontend_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    
    query = Video.query
    
    if search:
        query = query.filter(Video.vod_name.like(f'%{search}%'))
    
    if category:
        query = query.filter(Video.type_name == category)
    
    # 按最新更新日期排序：优先使用vod_time（更新时间），其次是vod_time_add（添加时间）
    pagination = query.order_by(
        db.case(
            (Video.vod_time > 0, Video.vod_time),
            else_=Video.vod_time_add
        ).desc()
    ).paginate(page=page, per_page=12, error_out=False)
    
    videos = pagination.items
    
    # 获取所有分类
    categories = db.session.query(Video.type_name, func.count(Video.id)).\
        filter(Video.type_name != None).\
        filter(Video.type_name != '').\
        group_by(Video.type_name).\
        order_by(func.count(Video.id).desc()).\
        all()
    
    return render_template('frontend/index.html', 
                         videos=videos, 
                         pagination=pagination,
                         search=search,
                         category=category,
                         categories=categories)

@frontend_bp.route('/video/<int:vod_id>')
def video_detail(vod_id):
    video = Video.query.filter_by(vod_id=vod_id).first_or_404()
    
    # 增加播放次数
    video.vod_hits += 1
    db.session.commit()
    
    return render_template('frontend/video_detail.html', video=video)

@frontend_bp.route('/category/<category>')
def category(category):
    page = request.args.get('page', 1, type=int)
    
    pagination = Video.query.filter_by(type_name=category).order_by(
        Video.vod_time_add.desc()
    ).paginate(page=page, per_page=12, error_out=False)
    
    videos = pagination.items
    
    return render_template('frontend/category.html', 
                         videos=videos, 
                         pagination=pagination,
                         category=category)
