"""
MacCMS10 通用采集器

完全兼容 MacCMS10 标准采集接口的采集器
支持 JSON 和 XML 两种格式
"""

import requests
import json
import time
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models.video import Video
from app.models.system_log import SystemLog
from app import db
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import current_app
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MacCMSCollector:
    """
    MacCMS10 通用采集器
    
    支持标准 MacCMS10 采集接口:
    - ac=list: 获取分类列表
    - ac=detail/videolist: 获取详细数据
    - 支持 JSON 和 XML 格式
    - 支持分页、分类、搜索、时间筛选等参数
    """
    
    def __init__(self, url, timeout=30, max_retries=3, params=None, max_workers=3, app=None):
        """
        初始化采集器
        
        Args:
            url: 采集接口URL (如: http://api.example.com/api.php/provide/vod/)
            timeout: 超时时间(秒)
            max_retries: 最大重试次数
            params: 采集参数字典 {
                'ac': 'list' | 'detail' | 'videolist',  # 操作类型
                'at': 'json' | 'xml',  # 返回格式，默认json
                't': '',  # 分类ID
                'pg': 1,  # 页码
                'ids': '',  # 视频ID列表，逗号分隔
                'wd': '',  # 搜索关键词
                'h': '',  # 最近N小时内的数据
                'start': 1,  # 起始页
                'end': None,  # 结束页，None表示采集到最后
            }
            max_workers: 并发线程数
            app: Flask应用实例
        """
        self.base_url = url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.app = app
        
        # 采集参数
        self.params = params or {}
        self.ac = self.params.get('ac', 'videolist')  # 默认获取详情
        self.at = self.params.get('at', 'json')  # 默认JSON格式
        self.type_id = self.params.get('t', '')
        self.start_page = int(self.params.get('start', 1))
        self.end_page = self.params.get('end', None)
        self.ids = self.params.get('ids', '')
        self.wd = self.params.get('wd', '')
        self.hours = self.params.get('h', '')
        
        # 统计信息
        self.success_count = 0
        self.failed_count = 0
        self.skip_count = 0
        self.errors = []
        self.is_running = False
        self.should_stop = False
        self.consecutive_duplicates = 0
        self.max_consecutive_duplicates = 20
        self.current_page = self.start_page
        
        # 线程锁
        self.count_lock = threading.Lock()
        self.db_lock = threading.Lock()
        
        # 创建session
        self.session = self._create_session()
        
        # 分类绑定关系
        self.type_bind = {}  # {远程分类ID: 本地分类ID}
    
    def _create_session(self):
        """创建带重试机制的session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'MacCMS10/Python Collector',
            'Accept': 'application/json, text/xml',
        })
        return session
    
    def build_url(self, **kwargs):
        """
        构建请求URL
        
        Args:
            **kwargs: URL参数，会覆盖初始化时的参数
        """
        url_params = {
            'ac': kwargs.get('ac', self.ac),
        }
        
        # 添加格式参数
        if self.at == 'xml':
            url_params['at'] = 'xml'
        
        # 添加其他参数
        if kwargs.get('t') or self.type_id:
            url_params['t'] = kwargs.get('t', self.type_id)
        
        if kwargs.get('pg'):
            url_params['pg'] = kwargs['pg']
        
        if kwargs.get('ids') or self.ids:
            url_params['ids'] = kwargs.get('ids', self.ids)
        
        if kwargs.get('wd') or self.wd:
            url_params['wd'] = kwargs.get('wd', self.wd)
        
        if kwargs.get('h') or self.hours:
            url_params['h'] = kwargs.get('h', self.hours)
        
        # 构建完整URL
        param_str = '&'.join([f"{k}={v}" for k, v in url_params.items() if v])
        separator = '&' if '?' in self.base_url else '?'
        return f"{self.base_url}{separator}{param_str}"
    
    def fetch_data(self, **kwargs):
        """
        获取数据
        
        Args:
            **kwargs: URL参数
            
        Returns:
            dict: 标准化后的数据 {
                'code': 1,  # 1成功，其他失败
                'msg': '',
                'page': 1,
                'pagecount': 10,
                'limit': 20,
                'total': 200,
                'list': [],
                'class': []  # 仅在ac=list时返回
            }
        """
        url = self.build_url(**kwargs)
        
        # 调试日志：输出请求URL和参数
        print(f"[采集器调试] 请求URL: {url}")
        print(f"[采集器调试] 请求参数: {kwargs}")
        if self.wd:
            print(f"[采集器调试] 搜索关键词(wd): {self.wd}")
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, verify=False)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                # 调试日志：输出响应状态和内容长度
                print(f"[采集器调试] 响应状态码: {response.status_code}")
                print(f"[采集器调试] 响应内容长度: {len(response.text)} 字符")
                print(f"[采集器调试] 响应前200字符: {response.text[:200]}")
                
                # 根据格式解析
                if self.at == 'xml':
                    return self._parse_xml(response.text, url)
                else:
                    return self._parse_json(response.text, url)
                    
            except Exception as e:
                error_msg = f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                print(error_msg)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.errors.append(f"请求失败: {url}, 错误: {str(e)}")
                    return {'code': 0, 'msg': str(e)}
        
        return {'code': 0, 'msg': '请求失败'}
    
    def _parse_json(self, text, url):
        """解析JSON响应"""
        try:
            # 调试日志：检查JSON内容
            if not text or not text.strip():
                print(f"[采集器调试] 警告：收到空响应！")
                return {'code': 0, 'msg': '响应内容为空'}
            
            data = json.loads(text)
            
            # 调试日志：输出解析后的数据结构
            print(f"[采集器调试] JSON解析成功")
            print(f"[采集器调试] 返回code: {data.get('code')}")
            print(f"[采集器调试] 视频数量: {len(data.get('list', []))}")
            print(f"[采集器调试] 总数: {data.get('total', 0)}")
            
            # MacCMS10 JSON 格式标准化
            result = {
                'code': data.get('code', 1),
                'msg': data.get('msg', ''),
                'page': int(data.get('page', 1)),
                'pagecount': int(data.get('pagecount', 1)),
                'limit': int(data.get('limit', 20)),
                'total': int(data.get('total', 0)),
                'list': data.get('list', []),
                'class': data.get('class', []),
                'url': url
            }
            
            # 处理播放数据格式
            for video in result['list']:
                # 处理vod_play_url字段（可能是字典格式）
                if 'vod_play_url' in video and isinstance(video['vod_play_url'], dict):
                    # 转换为标准格式: 线路1$$$线路2
                    play_from = []
                    play_url = []
                    for source, urls in video['vod_play_url'].items():
                        play_from.append(source)
                        play_url.append(urls)
                    video['vod_play_from'] = '$$$'.join(play_from)
                    video['vod_play_url'] = '$$$'.join(play_url)
            
            return result
            
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON解析失败: {url}, 错误: {str(e)}")
            return {'code': 0, 'msg': f'JSON解析失败: {str(e)}'}
    
    def _parse_xml(self, text, url):
        """解析XML响应"""
        try:
            root = ET.fromstring(text)
            
            # 解析分页信息
            list_elem = root.find('list')
            page_info = {
                'page': int(list_elem.get('page', 1)),
                'pagecount': int(list_elem.get('pagecount', 1)),
                'pagesize': int(list_elem.get('pagesize', 20)),
                'recordcount': int(list_elem.get('recordcount', 0)),
            }
            
            # 解析视频列表
            videos = []
            for video_elem in list_elem.findall('video'):
                video = {}
                
                # 基本字段
                video['vod_id'] = self._get_xml_text(video_elem, 'id')
                video['type_id'] = self._get_xml_text(video_elem, 'tid')
                video['vod_name'] = self._get_xml_text(video_elem, 'name')
                video['type_name'] = self._get_xml_text(video_elem, 'type')
                video['vod_pic'] = self._get_xml_text(video_elem, 'pic')
                video['vod_lang'] = self._get_xml_text(video_elem, 'lang')
                video['vod_area'] = self._get_xml_text(video_elem, 'area')
                video['vod_year'] = self._get_xml_text(video_elem, 'year')
                video['vod_remarks'] = self._get_xml_text(video_elem, 'note')
                video['vod_actor'] = self._get_xml_text(video_elem, 'actor')
                video['vod_director'] = self._get_xml_text(video_elem, 'director')
                video['vod_content'] = self._get_xml_text(video_elem, 'des')
                video['vod_time'] = self._get_xml_text(video_elem, 'last')
                
                # 解析播放数据
                dl_elem = video_elem.find('dl')
                if dl_elem is not None:
                    play_from = []
                    play_url = []
                    for dd in dl_elem.findall('dd'):
                        flag = dd.get('flag', '')
                        urls = dd.text or ''
                        play_from.append(flag)
                        play_url.append(urls)
                    
                    video['vod_play_from'] = '$$$'.join(play_from)
                    video['vod_play_url'] = '$$$'.join(play_url)
                
                videos.append(video)
            
            # 解析分类列表
            classes = []
            class_elem = root.find('class')
            if class_elem is not None:
                for ty in class_elem.findall('ty'):
                    classes.append({
                        'type_id': ty.get('id', ''),
                        'type_name': ty.text or ''
                    })
            
            return {
                'code': 1,
                'msg': 'xml',
                'page': page_info['page'],
                'pagecount': page_info['pagecount'],
                'limit': page_info['pagesize'],
                'total': page_info['recordcount'],
                'list': videos,
                'class': classes,
                'url': url
            }
            
        except ET.ParseError as e:
            self.errors.append(f"XML解析失败: {url}, 错误: {str(e)}")
            return {'code': 0, 'msg': f'XML解析失败: {str(e)}'}
    
    def _get_xml_text(self, element, tag):
        """安全获取XML元素文本"""
        elem = element.find(tag)
        if elem is not None:
            return elem.text or ''
        return ''
    
    def get_categories(self):
        """
        获取分类列表
        
        Returns:
            list: 分类列表 [{'type_id': '', 'type_name': ''}, ...]
        """
        result = self.fetch_data(ac='list', pg=1)
        if result['code'] == 1:
            return result.get('class', [])
        return []
    
    def save_video(self, video_data, update_existing=True):
        """
        保存视频到数据库
        
        Args:
            video_data: 视频数据字典
            update_existing: 是否更新已存在的视频
            
        Returns:
            tuple: (status, message)
                status: 'success', 'skip', 'failed'
                message: 状态说明
        """
        try:
            with self.db_lock:
                # 根据vod_name查找
                vod_name = video_data.get('vod_name', '').strip()
                if not vod_name:
                    SystemLog.log(
                        log_type='collect',
                        level='error',
                        module='maccms_collector',
                        message='采集失败: 视频名称为空',
                        details=json.dumps({
                            'vod_name': vod_name,
                            'vod_id': video_data.get('vod_id', ''),
                            'type_id': video_data.get('type_id', ''),
                            'type_name': video_data.get('type_name', ''),
                            'page': getattr(self, 'current_page', None)
                        }, ensure_ascii=False)
                    )
                    return 'failed', '视频名称为空'
                existing = Video.query.filter_by(vod_name=vod_name).first()
                # 处理vod_id字段（Video模型要求必填）
                if 'vod_id' not in video_data or not video_data['vod_id']:
                    # 如果没有vod_id，使用名称hash值作为vod_id
                    video_data['vod_id'] = abs(hash(vod_name)) % (10 ** 8)
                # 处理分类ID绑定
                remote_type_id = str(video_data.get('type_id', ''))
                local_type_id = self.type_bind.get(remote_type_id, remote_type_id)
                if local_type_id:
                    video_data['type_id'] = local_type_id
                # 处理分类名称（Video模型使用type_name字段显示分类）
                # 优先使用API返回的type_name，如果没有则保持原样
                if 'type_name' in video_data and video_data['type_name']:
                    pass
                elif 'type_id' in video_data:
                    video_data['type_name'] = video_data.get('type_name', '未分类')
                # 清理播放URL（保留纯URL）
                if 'vod_play_url' in video_data:
                    video_data['vod_play_url'] = self._clean_play_urls(video_data['vod_play_url'])
                # 过滤掉Video模型不存在的字段
                valid_fields = {
                    'vod_id', 'type_id', 'type_id_1', 'group_id', 'type_name', 'vod_name', 'vod_sub', 'vod_en',
                    'vod_status', 'vod_letter', 'vod_color', 'vod_tag', 'vod_class', 'vod_pic',
                    'vod_pic_thumb', 'vod_pic_slide', 'vod_actor', 'vod_director', 'vod_writer',
                    'vod_behind', 'vod_blurb', 'vod_remarks', 'vod_pubdate', 'vod_total', 'vod_serial',
                    'vod_tv', 'vod_weekday', 'vod_area', 'vod_lang', 'vod_year', 'vod_version',
                    'vod_state', 'vod_author', 'vod_jumpurl', 'vod_tpl', 'vod_tpl_play', 'vod_tpl_down',
                    'vod_isend', 'vod_lock', 'vod_level', 'vod_points_play', 'vod_points_down',
                    'vod_hits', 'vod_hits_day', 'vod_hits_week', 'vod_hits_month', 'vod_duration',
                    'vod_up', 'vod_down', 'vod_score', 'vod_score_all', 'vod_score_num',
                    'vod_time', 'vod_time_add', 'vod_time_hits', 'vod_time_make', 'vod_trysee',
                    'vod_douban_id', 'vod_douban_score', 'vod_reurl', 'vod_rel_vod', 'vod_rel_art',
                    'vod_content', 'vod_play_from', 'vod_play_server', 'vod_play_note', 'vod_play_url',
                    'vod_down_from', 'vod_down_server', 'vod_down_note', 'vod_down_url',
                    'vod_pwd', 'vod_pwd_url', 'vod_pwd_play', 'vod_pwd_play_url', 'vod_pwd_down'
                }
                filtered_data = {k: v for k, v in video_data.items() if k in valid_fields}
                if existing:
                    if update_existing:
                        # 更新现有视频
                        for key, value in filtered_data.items():
                            if key != 'vod_id' and hasattr(existing, key) and value:
                                setattr(existing, key, value)
                        db.session.commit()
                        with self.count_lock:
                            self.skip_count += 1
                            self.consecutive_duplicates += 1
                        SystemLog.log(
                            log_type='collect',
                            level='info',
                            module='maccms_collector',
                            message='更新已存在视频',
                            details=json.dumps({
                                'vod_name': vod_name,
                                'vod_id': video_data.get('vod_id', ''),
                                'type_id': video_data.get('type_id', ''),
                                'type_name': video_data.get('type_name', ''),
                                'result': 'skip-update',
                                'page': getattr(self, 'current_page', None)
                            }, ensure_ascii=False)
                        )
                        return 'skip', f'更新视频: {vod_name}'
                    else:
                        with self.count_lock:
                            self.skip_count += 1
                            self.consecutive_duplicates += 1
                        SystemLog.log(
                            log_type='collect',
                            level='info',
                            module='maccms_collector',
                            message='跳过已存在视频',
                            details=json.dumps({
                                'vod_name': vod_name,
                                'vod_id': video_data.get('vod_id', ''),
                                'type_id': video_data.get('type_id', ''),
                                'type_name': video_data.get('type_name', ''),
                                'result': 'skip',
                                'page': getattr(self, 'current_page', None)
                            }, ensure_ascii=False)
                        )
                        return 'skip', f'跳过已存在视频: {vod_name}'
                else:
                    # 创建新视频
                    video = Video(**filtered_data)
                    db.session.add(video)
                    db.session.commit()
                    with self.count_lock:
                        self.success_count += 1
                        self.consecutive_duplicates = 0  # 重置连续重复计数
                    # 只在控制台打印前3个，但日志记录所有
                    if self.success_count <= 3:
                        print(f"新增视频成功: {vod_name}, 分类: {filtered_data.get('type_name', '无')}")
                    SystemLog.log(
                        log_type='collect',
                        level='info',
                        module='maccms_collector',
                        message='新增视频成功',
                        details=json.dumps({
                            'vod_name': vod_name,
                            'vod_id': video_data.get('vod_id', ''),
                            'type_id': video_data.get('type_id', ''),
                            'type_name': video_data.get('type_name', ''),
                            'result': 'success',
                            'page': getattr(self, 'current_page', None)
                        }, ensure_ascii=False)
                    )
                    return 'success', f'新增视频: {vod_name}'
        except Exception as e:
            import traceback
            db.session.rollback()
            with self.count_lock:
                self.failed_count += 1
            error_msg = f'保存失败 [{vod_name}]: {str(e)}'
            error_detail = traceback.format_exc()
            self.errors.append(error_msg)
            if self.failed_count <= 3:
                print(f"保存视频失败: {error_msg}")
                print(f"详细错误:\n{error_detail}")
                print(f"视频数据字段: {list(video_data.keys())}")
                print(f"type_name: {video_data.get('type_name', 'NOT SET')}, type_id: {video_data.get('type_id', 'NOT SET')}")
                SystemLog.log(
                    log_type='collect',
                    level='error',
                    module='maccms_collector',
                    message='保存视频失败',
                    details=json.dumps({
                        'vod_name': vod_name,
                        'vod_id': video_data.get('vod_id', ''),
                        'type_id': video_data.get('type_id', ''),
                        'type_name': video_data.get('type_name', ''),
                        'result': 'failed',
                        'error': str(e),
                        'page': getattr(self, 'current_page', None)
                    }, ensure_ascii=False)
                )
                return 'failed', error_msg
            SystemLog.log(
                log_type='collect',
                level='error',
                module='maccms_collector',
                message='保存视频失败',
                details=json.dumps({
                    'vod_name': vod_name,
                    'vod_id': video_data.get('vod_id', ''),
                    'type_id': video_data.get('type_id', ''),
                    'type_name': video_data.get('type_name', ''),
                    'result': 'failed',
                    'error': str(e),
                    'page': getattr(self, 'current_page', None)
                }, ensure_ascii=False)
            )
            return 'failed', error_msg
    
    def _clean_play_urls(self, play_url):
        """
        清理播放URL，只保留纯URL
        
        Args:
            play_url: 播放URL字符串，格式如 "第1集$url1#第2集$url2$$$线路2..."
            
        Returns:
            清理后的URL字符串
        """
        if not play_url:
            return play_url
        
        # 按 $$$ 分割不同播放源
        sources = play_url.split('$$$')
        cleaned_sources = []
        
        for source in sources:
            # 按 # 分割多个剧集
            episodes = source.split('#')
            cleaned_episodes = []
            
            for episode in episodes:
                if not episode.strip():
                    continue
                
                # 如果包含 $，只保留URL部分
                if '$' in episode:
                    parts = episode.split('$', 1)
                    if len(parts) == 2:
                        url = parts[1].replace('\\/', '/')
                        cleaned_episodes.append(url)
                else:
                    url = episode.replace('\\/', '/')
                    cleaned_episodes.append(url)
            
            if cleaned_episodes:
                cleaned_sources.append('#'.join(cleaned_episodes))
        
        return '$$$'.join(cleaned_sources)
    
    def collect_page(self, page, update_existing=True):
        """
        采集单页数据
        
        Args:
            page: 页码
            update_existing: 是否更新已存在的视频
            
        Returns:
            dict: {'success': 0, 'failed': 0, 'skip': 0, 'should_stop': False}
        """
        self.current_page = page
        if self.should_stop:
            return {'success': 0, 'failed': 0, 'skip': 0, 'should_stop': True}
        
        # 获取数据
        result = self.fetch_data(pg=page)
        
        if result['code'] != 1:
            return {'success': 0, 'failed': 1, 'skip': 0, 'should_stop': False}
        
        videos = result.get('list', [])
        page_success = 0
        page_failed = 0
        page_skip = 0
        
        # 在采集前检查是否应该停止
        with self.count_lock:
            if self.consecutive_duplicates >= self.max_consecutive_duplicates:
                return {'success': 0, 'failed': 0, 'skip': 0, 'should_stop': True}
        
        # 保存视频
        for video_data in videos:
            if self.should_stop:
                break
            
            status, msg = self.save_video(video_data, update_existing)
            
            if status == 'success':
                page_success += 1
            elif status == 'skip':
                page_skip += 1
            else:
                page_failed += 1
        
        # 检查是否达到连续重复阈值
        should_stop = False
        with self.count_lock:
            if self.consecutive_duplicates >= self.max_consecutive_duplicates:
                should_stop = True
        
        return {
            'success': page_success,
            'failed': page_failed,
            'skip': page_skip,
            'should_stop': should_stop
        }
    
    def _collect_page_with_context(self, page, update_existing):
        """在Flask应用上下文中采集单页"""
        if self.app:
            with self.app.app_context():
                return self.collect_page(page, update_existing)
        return self.collect_page(page, update_existing)
    
    def collect(self, update_existing=True):
        """
        开始采集
        
        Args:
            update_existing: 是否更新已存在的视频
            
        Returns:
            dict: 采集结果统计
        """
        self.is_running = True
        self.should_stop = False
        
        # 记录开始日志
        SystemLog.log(
            log_type='collect',
            level='info',
            module='maccms_collector',
            message='开始MacCMS10采集',
            details=json.dumps({
                'url': self.base_url,
                'ac': self.ac,
                'at': self.at,
                'type_id': self.type_id,
                'start_page': self.start_page,
                'end_page': self.end_page,
                'ids': self.ids,
                'wd': self.wd,
                'hours': self.hours,
                'max_workers': self.max_workers,
                'timeout': self.timeout,
                'max_retries': self.max_retries
            }, ensure_ascii=False)
        )
        
        try:
            # 第一页先单独采集，获取总页数
            print(f"开始采集第 {self.start_page} 页...")
            first_result = self.fetch_data(pg=self.start_page)
            
            if first_result['code'] != 1:
                error_msg = f"获取第一页数据失败: {first_result.get('msg', '未知错误')}"
                print(error_msg)
                self.errors.append(error_msg)
                self.is_running = False
                return self._build_result()
            
            # 获取总页数
            total_pages = first_result['pagecount']
            print(f"总页数: {total_pages}")
            
            # 确定结束页码
            if self.end_page is None or self.end_page > total_pages:
                self.end_page = total_pages
            
            # 处理第一页数据
            page_success = 0
            page_skip = 0
            page_failed = 0
            
            for video_data in first_result.get('list', []):
                if self.should_stop:
                    break
                result, _ = self.save_video(video_data, update_existing)
                if result == 'success':
                    page_success += 1
                elif result == 'skip':
                    page_skip += 1
                else:
                    page_failed += 1
            
            # 输出第一页结果
            print(f"第 {self.start_page} 页完成: 成功={page_success}, 跳过={page_skip}, 失败={page_failed}")
            SystemLog.log(
                log_type='collect',
                level='info',
                module='maccms_collector',
                message=f'第{self.start_page}页采集完成',
                details=json.dumps({
                    'page': self.start_page,
                    'success': page_success,
                    'skip': page_skip,
                    'failed': page_failed
                }, ensure_ascii=False)
            )
            
            # 检查是否需要继续
            with self.count_lock:
                if self.consecutive_duplicates >= self.max_consecutive_duplicates:
                    print(f"连续 {self.consecutive_duplicates} 个重复，自动停止采集")
                    SystemLog.log(
                        log_type='collect',
                        level='info',
                        module='maccms_collector',
                        message='采集自动停止',
                        details=json.dumps({
                            'reason': 'consecutive_duplicates',
                            'count': self.consecutive_duplicates,
                            'threshold': self.max_consecutive_duplicates
                        }, ensure_ascii=False)
                    )
                    self.is_running = False
                    return self._build_result()
            
            # 如果只有一页或起始页就是结束页
            if total_pages == 1 or self.start_page >= self.end_page:
                print("采集完成")
                self.is_running = False
                result = self._build_result()
                SystemLog.log(
                    log_type='collect',
                    level='info',
                    module='maccms_collector',
                    message='采集任务完成',
                    details=json.dumps({
                        'total_pages': total_pages,
                        'success': self.success_count,
                        'skip': self.skip_count,
                        'failed': self.failed_count
                    }, ensure_ascii=False)
                )
                return result
            
            # 多线程采集剩余页面
            pages_to_collect = list(range(self.start_page + 1, self.end_page + 1))
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._collect_page_with_context, page, update_existing): page
                    for page in pages_to_collect
                }
                
                for future in as_completed(futures):
                    page = futures[future]
                    
                    try:
                        page_result = future.result()
                        print(f"第 {page} 页完成: 成功={page_result['success']}, "
                              f"跳过={page_result['skip']}, 失败={page_result['failed']}")
                        
                        # 记录每页日志
                        SystemLog.log(
                            log_type='collect',
                            level='info',
                            module='maccms_collector',
                            message=f'第{page}页采集完成',
                            details=json.dumps({
                                'page': page,
                                'success': page_result['success'],
                                'skip': page_result['skip'],
                                'failed': page_result['failed']
                            }, ensure_ascii=False)
                        )
                        
                        # 检查是否需要停止
                        if page_result['should_stop'] or self.should_stop:
                            print("检测到停止信号，关闭线程池...")
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                            
                    except Exception as e:
                        error_msg = f"第 {page} 页采集异常: {str(e)}"
                        print(error_msg)
                        self.errors.append(error_msg)
                        SystemLog.log(
                            log_type='collect',
                            level='error',
                            module='maccms_collector',
                            message=f'第{page}页采集异常',
                            details=json.dumps({
                                'page': page,
                                'error': str(e)
                            }, ensure_ascii=False)
                        )
            
            # 所有页面采集完成，设置状态
            print("采集完成")
            self.is_running = False
            SystemLog.log(
                log_type='collect',
                level='info',
                module='maccms_collector',
                message='采集任务完成',
                details=json.dumps({
                    'total_pages': self.end_page - self.start_page + 1,
                    'success': self.success_count,
                    'skip': self.skip_count,
                    'failed': self.failed_count
                }, ensure_ascii=False)
            )
        
        except Exception as e:
            import traceback
            error_msg = f"采集过程异常: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.errors.append(error_msg)
            SystemLog.log(
                log_type='collect',
                level='error',
                module='maccms_collector',
                message='采集过程异常',
                details=json.dumps({
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }, ensure_ascii=False)
            )
        
        finally:
            self.is_running = False
            
            # 记录完成日志
            SystemLog.log(
                log_type='collect',
                level='info',
                module='maccms_collector',
                message='MacCMS10采集完成',
                details=json.dumps({
                    'success_count': self.success_count,
                    'failed_count': self.failed_count,
                    'skip_count': self.skip_count,
                    'consecutive_duplicates': self.consecutive_duplicates,
                    'errors': self.errors[:5] if self.errors else []
                }, ensure_ascii=False)
            )
        
        return self._build_result()
    
    def _build_result(self):
        """构建采集结果"""
        return {
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skip_count': self.skip_count,
            'errors': self.errors,
            'consecutive_duplicates': self.consecutive_duplicates,
            'is_stopped': self.should_stop or (self.consecutive_duplicates >= self.max_consecutive_duplicates)
        }
    
    def stop(self):
        """停止采集"""
        self.should_stop = True
        SystemLog.log(
            log_type='collect',
            level='warning',
            module='maccms_collector',
            message='手动停止采集',
            details=json.dumps({
                'current_success': self.success_count,
                'current_skip': self.skip_count,
                'current_failed': self.failed_count
            }, ensure_ascii=False)
        )
    
    def set_type_bind(self, bind_dict):
        """
        设置分类绑定关系
        
        Args:
            bind_dict: {远程分类ID: 本地分类ID}
        """
        self.type_bind = bind_dict
    
    def get_status(self):
        """获取当前采集状态"""
        return {
            'is_running': self.is_running,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skip_count': self.skip_count,
            'consecutive_duplicates': self.consecutive_duplicates,
            'current_page': self.current_page,
            'errors': self.errors[-5:] if self.errors else []
        }
    
    def search(self, wd=None, page=1, type_id=None):
        """
        搜索视频（采集源API）
        
        Args:
            wd: 搜索关键词
            page: 页码
            type_id: 分类ID（可选）
        
        Returns:
            dict: 标准化后的数据
        """
        print(f"[采集器调试] 调用search方法 - 关键词: {wd}, 页码: {page}, 分类ID: {type_id}")
        params = {'ac': 'videolist', 'pg': page}
        if wd:
            params['wd'] = wd
            print(f"[采集器调试] 添加搜索参数 wd={wd}")
        if type_id:
            params['t'] = type_id
            print(f"[采集器调试] 添加分类参数 t={type_id}")
        result = self.fetch_data(**params)
        print(f"[采集器调试] 搜索结果: code={result.get('code')}, 视频数={len(result.get('list', []))}")
        return result
