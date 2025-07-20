"""
Web管理界面 - Flask应用主文件
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import secrets
import time

# 导入项目模块
import sys
sys.path.append('..')
from config.settings import Settings
from config.database import Database
from web.auth import AuthManager
from utils.logger import get_recent_logs, get_log_stats


class WebApp:
    """Web应用管理器"""
    
    def __init__(self, settings, database):
        self.settings = settings
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # 创建Flask应用
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('WEB_SECRET_KEY', secrets.token_hex(32))
        
        # 配置SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 认证管理器
        self.auth_manager = AuthManager(settings)
        
        # 注册路由
        self._register_routes()
        self._register_socketio_events()
        
        # Web配置
        self.app.config.update({
            'SECRET_KEY': self.app.secret_key,
            'SESSION_TIMEOUT': 3600,  # 1小时
            'WEB_HOST': os.getenv('WEB_HOST', '0.0.0.0'),
            'WEB_PORT': int(os.getenv('WEB_PORT', 8080)),
            'WEB_DEBUG': os.getenv('WEB_DEBUG', 'False').lower() == 'true'
        })

    def _register_routes(self):
        """注册Web路由"""
        
        @self.app.route('/')
        def index():
            """首页 - 重定向到仪表板"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            return redirect(url_for('dashboard'))

        @self.app.route('/login')
        def login():
            """登录页面"""
            return render_template('login.html')

        @self.app.route('/api/request-login-code', methods=['POST'])
        def request_login_code():
            """请求登录码"""
            try:
                login_code = self.auth_manager.generate_login_code()
                return jsonify({
                    'success': True,
                    'login_code': login_code,
                    'expires_in': 300,  # 5分钟
                    'message': f'登录码: {login_code}，请发送给Bot: /weblogin {login_code}'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})

        @self.app.route('/api/check-login/<login_code>')
        def check_login(login_code):
            """检查登录状态"""
            try:
                if self.auth_manager.verify_login_code(login_code):
                    # 设置session
                    session['authenticated'] = True
                    session['login_time'] = time.time()
                    session['admin_user'] = self.auth_manager.get_user_by_code(login_code)
                    
                    return jsonify({
                        'success': True,
                        'redirect': url_for('dashboard')
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '登录码无效或已过期'
                    })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})

        @self.app.route('/dashboard')
        def dashboard():
            """仪表板"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            
            return render_template('dashboard.html', 
                                 user=session.get('admin_user'),
                                 page_title='仪表板')

        @self.app.route('/groups')
        def groups():
            """搬运组管理"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            
            return render_template('groups.html',
                                 user=session.get('admin_user'),
                                 page_title='搬运组管理')

        @self.app.route('/accounts')
        def accounts():
            """账号管理"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            
            return render_template('accounts.html',
                                 user=session.get('admin_user'),
                                 page_title='账号管理')

        @self.app.route('/settings')
        def settings():
            """系统设置"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            
            return render_template('settings.html',
                                 user=session.get('admin_user'),
                                 page_title='系统设置')

        @self.app.route('/logs')
        def logs():
            """日志查看"""
            if not self._is_authenticated():
                return redirect(url_for('login'))
            
            return render_template('logs.html',
                                 user=session.get('admin_user'),
                                 page_title='系统日志')

        @self.app.route('/logout')
        def logout():
            """退出登录"""
            session.clear()
            flash('已退出登录', 'info')
            return redirect(url_for('login'))

        # API路由
        self._register_api_routes()

    def _register_api_routes(self):
        """注册API路由"""
        
        @self.app.route('/api/status')
        def api_status():
            """获取系统状态"""
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                # 这里需要调用管理器获取状态
                # 由于是异步调用，需要特殊处理
                status = {
                    'system': {
                        'running': True,
                        'uptime': '2小时30分钟',
                        'memory_usage': '85.2MB',
                        'cpu_usage': '12.5%'
                    },
                    'accounts': {
                        'total': 2,
                        'active': 2,
                        'error': 0
                    },
                    'groups': {
                        'total': 1,
                        'active': 1,
                        'processing': 0
                    },
                    'stats': {
                        'messages_today': 156,
                        'success_rate': 98.5,
                        'last_message': '2分钟前'
                    }
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/groups')
        def api_groups():
            """获取搬运组列表"""
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                # 模拟数据，实际应该从数据库获取
                groups = [
                    {
                        'id': 1,
                        'name': '新闻组',
                        'description': '搬运新闻内容',
                        'status': 'active',
                        'source_count': 2,
                        'target_count': 1,
                        'messages_today': 45,
                        'success_rate': 97.8,
                        'schedule': '09:00-23:00',
                        'filters': ['ad_detection', 'smart_filter']
                    }
                ]
                return jsonify(groups)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs')
        def api_logs():
            """获取系统日志"""
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                lines = request.args.get('lines', 50, type=int)
                level = request.args.get('level', 'ALL')
                
                logs = get_recent_logs(lines=lines)
                
                # 过滤日志级别
                if level != 'ALL':
                    logs = [log for log in logs if level in log]
                
                return jsonify({
                    'logs': logs,
                    'total': len(logs),
                    'stats': get_log_stats()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/accounts')
        def api_accounts():
            """获取账号列表"""
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                # 模拟账号数据
                accounts = [
                    {
                        'phone': '+86138****0000',
                        'username': 'user1',
                        'status': 'active',
                        'api_id': '11724860',
                        'last_active': '1分钟前',
                        'error_count': 0,
                        'messages_sent': 23
                    },
                    {
                        'phone': '+86139****0000', 
                        'username': 'user2',
                        'status': 'active',
                        'api_id': '11724860',
                        'last_active': '3分钟前',
                        'error_count': 0,
                        'messages_sent': 22
                    }
                ]
                return jsonify(accounts)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _register_socketio_events(self):
        """注册SocketIO事件"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接"""
            if not self._is_authenticated():
                return False
            
            emit('status', {'message': '连接成功'})
            self.logger.info(f"Web客户端连接: {request.sid}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开"""
            self.logger.info(f"Web客户端断开: {request.sid}")

        @self.socketio.on('request_status')
        def handle_status_request():
            """请求状态更新"""
            if not self._is_authenticated():
                return
            
            # 获取实时状态并发送
            status = self._get_real_time_status()
            emit('status_update', status)

    def _is_authenticated(self):
        """检查用户是否已认证"""
        if not session.get('authenticated'):
            return False
        
        # 检查session是否过期
        login_time = session.get('login_time', 0)
        if time.time() - login_time > self.app.config['SESSION_TIMEOUT']:
            session.clear()
            return False
        
        return True

    def _get_real_time_status(self):
        """获取实时状态"""
        try:
            # 这里应该调用实际的管理器获取状态
            return {
                'timestamp': datetime.now().isoformat(),
                'system_running': True,
                'active_accounts': 2,
                'active_groups': 1,
                'messages_processed': 156
            }
        except Exception as e:
            self.logger.error(f"获取实时状态失败: {e}")
            return {'error': str(e)}

    def run(self, host=None, port=None, debug=None):
        """启动Web应用"""
        host = host or self.app.config['WEB_HOST']
        port = port or self.app.config['WEB_PORT']
        debug = debug if debug is not None else self.app.config['WEB_DEBUG']
        
        self.logger.info(f"🌐 启动Web管理界面: http://{host}:{port}")
        
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )


# 全局变量，用于与Bot交互
web_app_instance = None

def get_web_app():
    """获取Web应用实例"""
    return web_app_instance

def set_web_app(app):
    """设置Web应用实例"""
    global web_app_instance
    web_app_instance = app