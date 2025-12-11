from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from app.blueprints.admin import admin_bp
from app.models.video import Video
from app.models.collect_source import CollectSource
from app.models.system_log import SystemLog
from app import db
from app.collectors.maccms_collector import MacCMSCollector
from app.collectors.maccms_manager import maccms_manager
from app.downloaders import download_manager
from functools import wraps
import requests
import json

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def index():
    """后台首页，已登录跳转到仪表板，否则跳转到登录页"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面，允许访问无需认证"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        from flask import current_app
        if username == current_app.config['ADMIN_USERNAME'] and \
           password == current_app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            flash('登录成功', 'success')
            
            # 记录登录日志
            SystemLog.log(
                log_type='system',
                level='info',
                module='admin',
                message=f'管理员登录成功',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            return redirect(url_for('admin.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
            
            # 记录登录失败日志
            SystemLog.log(
                log_type='system',
                level='warning',
                module='admin',
                message=f'登录失败: 用户名或密码错误',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('已退出登录', 'success')
    
    # 记录登出日志
    SystemLog.log(
        log_type='system',
        level='info',
        module='admin',
        message='管理员退出登录',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    
    query = Video.query
    
    if search:
        # 同时搜索视频名称和分类
        query = query.filter(
            db.or_(
                Video.vod_name.like(f'%{search}%'),
                Video.type_name.like(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Video.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    videos = pagination.items
    total_videos = Video.query.count()
    
    # 统计分类数量和获取分类列表
    from sqlalchemy import func
    category_count = db.session.query(func.count(func.distinct(Video.type_name))).scalar()
    
    # 获取所有分类及其视频数量
    categories = db.session.query(
        Video.type_name,
        func.count(Video.id).label('count')
    ).filter(Video.type_name != '', Video.type_name.isnot(None)).group_by(Video.type_name).order_by(func.count(Video.id).desc()).all()
    
    return render_template('admin/dashboard.html', 
                         videos=videos, 
                         pagination=pagination,
                         search=search,
                         total_videos=total_videos,
                         category_count=category_count,
                         categories=categories)

@admin_bp.route('/video/add', methods=['GET', 'POST'])
@login_required
def add_video():
    if request.method == 'POST':
        try:
            video = Video(
                vod_id=request.form.get('vod_id', type=int),
                vod_name=request.form.get('vod_name'),
                type_name=request.form.get('type_name', ''),
                vod_pic=request.form.get('vod_pic', ''),
                vod_play_url=request.form.get('vod_play_url', ''),
                vod_class=request.form.get('vod_class', ''),
                vod_year=request.form.get('vod_year', ''),
                vod_area=request.form.get('vod_area', ''),
                vod_lang=request.form.get('vod_lang', ''),
                vod_actor=request.form.get('vod_actor', ''),
                vod_director=request.form.get('vod_director', ''),
                vod_score=request.form.get('vod_score', '0.0'),
                vod_content=request.form.get('vod_content', ''),
                vod_time_add=request.form.get('vod_time_add', type=int, default=0)
            )
            
            db.session.add(video)
            db.session.commit()
            flash('视频添加成功', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'error')
    
    return render_template('admin/video_form.html', video=None, action='add')

@admin_bp.route('/video/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_video(id):
    video = Video.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            video.vod_id = request.form.get('vod_id', type=int)
            video.vod_name = request.form.get('vod_name')
            video.type_name = request.form.get('type_name', '')
            video.vod_pic = request.form.get('vod_pic', '')
            video.vod_play_url = request.form.get('vod_play_url', '')
            video.vod_class = request.form.get('vod_class', '')
            video.vod_year = request.form.get('vod_year', '')
            video.vod_area = request.form.get('vod_area', '')
            video.vod_lang = request.form.get('vod_lang', '')
            video.vod_actor = request.form.get('vod_actor', '')
            video.vod_director = request.form.get('vod_director', '')
            video.vod_score = request.form.get('vod_score', '0.0')
            video.vod_content = request.form.get('vod_content', '')
            
            db.session.commit()
            flash('视频更新成功', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'error')
    
    return render_template('admin/video_form.html', video=video, action='edit')

@admin_bp.route('/video/delete/<int:id>', methods=['POST'])
@login_required
def delete_video(id):
    try:
        video = Video.query.get_or_404(id)
        video_name = video.vod_name
        
        # 删除本地图片
        deleted_image = video.delete_local_image()
        
        db.session.delete(video)
        db.session.commit()
        
        # 记录日志
        SystemLog.log(
            log_type='system',
            level='info',
            module='Admin',
            message=f'删除视频: {video_name} (ID: {id}){"，已删除本地图片" if deleted_image else ""}'
        )
        
        flash('视频删除成功' + ('，已删除本地图片' if deleted_image else ''), 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/video/clear', methods=['POST'])
@login_required
def clear_all_videos():
    """清空所有视频"""
    try:
        # 获取所有视频并删除本地图片
        videos = Video.query.all()
        deleted_images = 0
        for video in videos:
            if video.delete_local_image():
                deleted_images += 1
        
        count = Video.query.count()
        Video.query.delete()
        db.session.commit()
        
        # 记录日志
        SystemLog.log(
            log_type='system',
            level='warning',
            module='Admin',
            message=f'清空所有视频: {count}个视频, {deleted_images}个本地图片'
        )
        
        flash(f'成功清空 {count} 个视频，删除 {deleted_images} 个本地图片', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'清空失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/video/clear_category', methods=['POST'])
@login_required
def clear_category_videos():
    """按分类清空视频"""
    category = request.form.get('category', '').strip()
    
    if not category:
        flash('请指定分类', 'error')
        return redirect(url_for('admin.dashboard'))
    
    try:
        # 获取该分类的所有视频并删除本地图片
        videos = Video.query.filter_by(type_name=category).all()
        deleted_images = 0
        for video in videos:
            if video.delete_local_image():
                deleted_images += 1
        
        count = len(videos)
        Video.query.filter_by(type_name=category).delete()
        db.session.commit()
        
        # 记录日志
        SystemLog.log(
            log_type='system',
            level='warning',
            module='Admin',
            message=f'清空分类视频: {category}, {count}个视频, {deleted_images}个本地图片'
        )
        
        flash(f'成功清空分类 [{category}] 的 {count} 个视频，删除 {deleted_images} 个本地图片', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'清空失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/collect', methods=['GET'])
@login_required
def collect():
    """MacCMS10采集页面"""
    # 获取所有任务状态
    all_status = maccms_manager.get_all_status()
    
    # 获取所有启用的采集源
    sources = CollectSource.query.filter_by(is_active=True).order_by(CollectSource.name).all()
    
    return render_template('admin/collect.html', 
                         all_status=all_status,
                         sources=sources)

@admin_bp.route('/collect/start', methods=['POST'])
@login_required
def start_collect():
    """启动MacCMS10采集任务"""
    try:
        # 获取表单数据
        source_id = request.form.get('source_id')
        ac = request.form.get('ac', 'videolist')
        at = request.form.get('at', 'json')
        type_id = request.form.get('type_id', '').strip()
        start_page = int(request.form.get('start_page', 1))
        end_page = request.form.get('end_page', '').strip()
        ids = request.form.get('ids', '').strip()
        wd = request.form.get('wd', '').strip()
        hours = request.form.get('hours', '').strip()
        update_existing = request.form.get('update_existing') == 'on'
        max_workers = int(request.form.get('max_workers', 3))
        
        if not source_id:
            return jsonify({'success': False, 'message': '请选择采集源'})
        
        # 从数据库获取采集源
        source = CollectSource.query.get(source_id)
        if not source:
            return jsonify({'success': False, 'message': '采集源不存在'})
        
        if not source.is_active:
            return jsonify({'success': False, 'message': '该采集源已禁用'})
        
        url = source.url
        
        # 构建采集参数
        params = {
            'ac': ac,
            'at': at,
            't': type_id,
            'start': start_page,
            'end': int(end_page) if end_page else None,
            'ids': ids,
            'wd': wd,
            'h': hours,
            'update_existing': update_existing
        }
        
        # 启动采集任务
        task_id = maccms_manager.start_collect(
            url=url,
            params=params,
            max_workers=max_workers,
            timeout=30,
            max_retries=3
        )
        
        # 记录日志
        SystemLog.log(
            log_type='collect',
            level='info',
            module='admin',
            message=f'启动MacCMS10采集任务 #{task_id} - {source.name}',
            details=json.dumps({
                'url': url,
                'params': params,
                'max_workers': max_workers
            }, ensure_ascii=False)
        )
        
        return jsonify({
            'success': True,
            'message': f'采集任务已启动，任务ID: {task_id}',
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动失败: {str(e)}'
        })

@admin_bp.route('/collect/stop/<int:task_id>', methods=['POST'])
@login_required
def stop_collect(task_id):
    """停止MacCMS10采集任务"""
    success = maccms_manager.stop_collect(task_id)
    
    if success:
        return jsonify({'success': True, 'message': '采集任务已停止'})
    else:
        return jsonify({'success': False, 'message': '任务不存在或已完成'})

@admin_bp.route('/collect/status/<int:task_id>', methods=['GET'])
@login_required
def collect_status(task_id):
    """获取MacCMS10采集任务状态"""
    status = maccms_manager.get_status(task_id)
    
    if status:
        return jsonify({'success': True, 'status': status})
    else:
        return jsonify({'success': False, 'message': '任务不存在'})

@admin_bp.route('/collect/test', methods=['POST'])
@login_required
def test_collect():
    """测试MacCMS10采集接口"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        at = data.get('at', 'json')
        
        if not url:
            return jsonify({'success': False, 'message': '请输入采集接口URL'})
        
        # 创建临时采集器测试
        collector = MacCMSCollector(
            url=url,
            params={'ac': 'list', 'at': at},
            timeout=15,
            max_retries=2
        )
        
        # 获取第一页数据
        result = collector.fetch_data(pg=1)
        
        if result['code'] == 1:
            # 获取分类列表
            categories = result.get('class', [])
            # 获取视频列表
            videos = result.get('list', [])
            
            return jsonify({
                'success': True,
                'message': '接口测试成功',
                'info': {
                    'total': result.get('total', 0),
                    'pagecount': result.get('pagecount', 0),
                    'limit': result.get('limit', 0),
                    'categories': categories[:10] if categories else [],
                    'sample_count': len(videos)
                },
                'videos': videos[:12] if videos else []
            })
        else:
            return jsonify({
                'success': False,
                'message': f'接口测试失败: {result.get("msg", "未知错误")}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        })


@admin_bp.route('/collect/categories', methods=['POST'])
@login_required
def get_categories():
    """获取MacCMS10采集源的分类列表和视频预览"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        at = data.get('at', 'json')
        
        if not url:
            return jsonify({'success': False, 'message': '请输入采集接口URL'})
        
        # 创建临时采集器
        collector = MacCMSCollector(
            url=url,
            params={'ac': 'list', 'at': at},
            timeout=15,
            max_retries=2
        )
        
        # 获取第一页数据（包含分类和视频列表）
        result = collector.fetch_data(ac='list', pg=1)
        
        if result['code'] == 1:
            categories = result.get('class', [])
            videos = result.get('list', [])
            
            return jsonify({
                'success': True,
                'categories': categories,
                'videos': videos,
                'total': result.get('total', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': '未获取到分类信息'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        })


@admin_bp.route('/collect/cleanup', methods=['POST'])
@login_required
def cleanup_tasks():
    """清理已完成的采集任务"""
    count = maccms_manager.cleanup_finished_tasks()
    return jsonify({
        'success': True,
        'message': f'已清理 {count} 个已完成的任务'
    })


# ==================== 采集源管理 ====================

@admin_bp.route('/sources')
@login_required
def sources_list():
    """采集源列表"""
    sources = CollectSource.query.order_by(CollectSource.sort_order.asc(), CollectSource.id.desc()).all()
    return render_template('admin/sources/list.html', sources=sources)


@admin_bp.route('/sources/add', methods=['GET', 'POST'])
@login_required
def source_add():
    """添加采集源"""
    if request.method == 'POST':
        try:
            source = CollectSource(
                name=request.form.get('name'),
                url=request.form.get('url'),
                api_type=request.form.get('api_type', 'json'),
                is_active=request.form.get('is_active') == 'on',
                sort_order=int(request.form.get('sort_order', 0)),
                note=request.form.get('note', '')
            )
            db.session.add(source)
            db.session.commit()
            flash('采集源添加成功', 'success')
            return redirect(url_for('admin.sources_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'error')
    
    return render_template('admin/sources/form.html', source=None)


@admin_bp.route('/sources/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def source_edit(id):
    """编辑采集源"""
    source = CollectSource.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            source.name = request.form.get('name')
            source.url = request.form.get('url')
            source.api_type = request.form.get('api_type', 'json')
            source.is_active = request.form.get('is_active') == 'on'
            source.sort_order = int(request.form.get('sort_order', 0))
            source.note = request.form.get('note', '')
            
            db.session.commit()
            flash('采集源更新成功', 'success')
            return redirect(url_for('admin.sources_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'error')
    
    return render_template('admin/sources/form.html', source=source)


@admin_bp.route('/sources/delete/<int:id>', methods=['POST'])
@login_required
def source_delete(id):
    """删除采集源"""
    try:
        source = CollectSource.query.get_or_404(id)
        db.session.delete(source)
        db.session.commit()
        flash('采集源删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.sources_list'))


# ==================== 图片下载管理 ====================

@admin_bp.route('/images/download')
@login_required
def images_download():
    """图片下载页面"""
    status = download_manager.get_status()
    result = download_manager.get_last_result()
    
    # 统计本地化信息
    total_count = Video.query.count()
    localized_count = Video.query.filter_by(is_localized=True).count()
    
    return render_template('admin/images/download.html', 
                         status=status, 
                         result=result,
                         total_count=total_count,
                         localized_count=localized_count)


@admin_bp.route('/images/download/start', methods=['POST'])
@login_required
def images_download_start():
    """启动图片下载任务"""
    success, message = download_manager.start_download(app=current_app._get_current_object())
    
    if not success:
        flash(message, 'error')
    
    return redirect(url_for('admin.images_download'))


@admin_bp.route('/images/download/stop', methods=['POST'])
@login_required
def images_download_stop():
    """停止图片下载任务"""
    success, message = download_manager.stop_download()
    
    if not success:
        flash(message, 'error')
    
    return redirect(url_for('admin.images_download'))


@admin_bp.route('/images/download/status')
@login_required
def images_download_status():
    """获取图片下载状态（API）"""
    status = download_manager.get_status()
    return jsonify(status)


@admin_bp.route('/images/verify', methods=['POST'])
@login_required
def images_verify():
    """验证本地化图片"""
    try:
        result = download_manager.verify_localization(app=current_app._get_current_object())
        flash(f'验证完成！有效: {result["valid"]}, 修复: {result["fixed"]}', 'success')
    except Exception as e:
        flash(f'验证失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.images_download'))

@admin_bp.route('/logs')
@login_required
def logs():
    """系统日志列表"""
    page = request.args.get('page', 1, type=int)
    log_type = request.args.get('log_type', '', type=str)
    level = request.args.get('level', '', type=str)
    keyword = request.args.get('keyword', '', type=str).strip()
    
    # 构建查询
    query = SystemLog.query
    
    # 按类型筛选
    if log_type:
        query = query.filter(SystemLog.log_type == log_type)
    
    # 按级别筛选
    if level:
        query = query.filter(SystemLog.level == level)
    
    # 关键词搜索
    if keyword:
        query = query.filter(SystemLog.message.like(f'%{keyword}%'))
    
    # 按时间倒序
    query = query.order_by(SystemLog.created_at.desc())
    
    # 分页
    per_page = 50
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    # 获取统计信息
    stats = SystemLog.get_stats()
    
    return render_template('admin/logs.html', 
                         logs=logs, 
                         pagination=pagination,
                         stats=stats)

@admin_bp.route('/logs/<int:log_id>')
@login_required
def log_detail(log_id):
    """日志详情API"""
    log = SystemLog.query.get_or_404(log_id)
    return jsonify(log.to_dict())

@admin_bp.route('/logs/clean', methods=['POST'])
@login_required
def logs_clean():
    """清理旧日志"""
    try:
        deleted_count = SystemLog.clean_old_logs(days=30)
        flash(f'成功清理 {deleted_count} 条日志', 'success')
        
        # 记录清理日志
        SystemLog.log(
            log_type='system',
            level='info',
            module='Admin',
            message=f'清理了{deleted_count}条30天前的日志'
        )
    except Exception as e:
        flash(f'清理失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.logs'))

@admin_bp.route('/logs/clear_all', methods=['POST'])
@login_required
def logs_clear_all():
    """清空所有日志"""
    try:
        total_count = SystemLog.query.count()
        SystemLog.query.delete()
        db.session.commit()
        flash(f'成功清空 {total_count} 条日志', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'清空失败: {str(e)}', 'error')
    
    return redirect(url_for('admin.logs'))

