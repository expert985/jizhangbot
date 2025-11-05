#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web后台管理系统 - 端口38888
管理员可以管理用户、授权会员、查看统计等
"""
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime, timedelta
import asyncio
import hashlib
import config
from database import db

app = Flask(__name__)
app.secret_key = hashlib.sha256(f"{config.WEB_ADMIN_PASSWORD}secret".encode()).hexdigest()

# 登录页面模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>后台管理登录</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 后台管理登录</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>用户名：</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>密码：</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">登录</button>
        </form>
    </div>
</body>
</html>
"""

# 管理后台主页模板
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>后台管理系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            font-size: 24px;
        }
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #888;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .stat-card p {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .tabs {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .tab-buttons {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #eee;
        }
        .tab-button {
            flex: 1;
            padding: 15px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            color: #666;
            transition: all 0.3s;
        }
        .tab-button.active {
            background: white;
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }
        .tab-content {
            display: none;
            padding: 30px;
        }
        .tab-content.active {
            display: block;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-active {
            background: #d4edda;
            color: #155724;
        }
        .badge-expired {
            background: #f8d7da;
            color: #721c24;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎛️ 记账机器人管理后台</h1>
        <a href="/logout" class="logout-btn">退出登录</a>
    </div>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>总用户数</h3>
                <p id="totalUsers">-</p>
            </div>
            <div class="stat-card">
                <h3>活跃会员</h3>
                <p id="activeMembers">-</p>
            </div>
            <div class="stat-card">
                <h3>总群组数</h3>
                <p id="totalGroups">-</p>
            </div>
            <div class="stat-card">
                <h3>今日记账数</h3>
                <p id="todayRecords">-</p>
            </div>
        </div>

        <div class="tabs">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="switchTab('users')">用户管理</button>
                <button class="tab-button" onclick="switchTab('authorize')">授权会员</button>
                <button class="tab-button" onclick="switchTab('groups')">群组管理</button>
                <button class="tab-button" onclick="switchTab('settings')">套餐设置</button>
            </div>

            <div id="users" class="tab-content active">
                <h2>用户列表</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>用户名</th>
                            <th>姓名</th>
                            <th>会员状态</th>
                            <th>到期时间</th>
                            <th>剩余天数</th>
                        </tr>
                    </thead>
                    <tbody id="usersTable">
                        <tr><td colspan="6" style="text-align:center;">加载中...</td></tr>
                    </tbody>
                </table>
            </div>

            <div id="authorize" class="tab-content">
                <h2>授权会员</h2>
                <div id="authorizeMessage"></div>
                <form onsubmit="authorizeUser(event)">
                    <div class="form-group">
                        <label>用户标识（@用户名 或 用户ID）：</label>
                        <input type="text" id="authUserIdentifier" required placeholder="@username 或 123456789">
                    </div>
                    <div class="form-group">
                        <label>授权天数：</label>
                        <input type="number" id="authDays" required min="1" value="30">
                    </div>
                    <button type="submit" class="btn">授权</button>
                </form>
            </div>

            <div id="groups" class="tab-content">
                <h2>群组列表</h2>
                <table>
                    <thead>
                        <tr>
                            <th>群组ID</th>
                            <th>群组名称</th>
                            <th>记账数</th>
                            <th>创建时间</th>
                        </tr>
                    </thead>
                    <tbody id="groupsTable">
                        <tr><td colspan="4" style="text-align:center;">加载中...</td></tr>
                    </tbody>
                </table>
            </div>

            <div id="settings" class="tab-content">
                <h2>会员套餐价格设置</h2>
                <p style="color:#666; margin-bottom:20px;">当前套餐价格（配置在.env文件中）：</p>
                <div class="stat-card" style="margin-bottom:20px;">
                    <h3>30天会员</h3>
                    <p>{{ price_30 }} USDT</p>
                </div>
                <div class="stat-card" style="margin-bottom:20px;">
                    <h3>90天会员</h3>
                    <p>{{ price_90 }} USDT</p>
                </div>
                <div class="stat-card">
                    <h3>365天会员</h3>
                    <p>{{ price_365 }} USDT</p>
                </div>
                <p style="color:#999; margin-top:20px; font-size:14px;">
                    💡 提示：修改价格请编辑 .env 文件中的以下配置：<br>
                    MEMBERSHIP_PRICE_30_DAYS<br>
                    MEMBERSHIP_PRICE_90_DAYS<br>
                    MEMBERSHIP_PRICE_365_DAYS
                </p>
            </div>
        </div>
    </div>

    <script>
        // 切换标签页
        function switchTab(tabName) {
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }

        // 加载统计数据
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                if (data.success) {
                    document.getElementById('totalUsers').textContent = data.data.total_users;
                    document.getElementById('activeMembers').textContent = data.data.active_members;
                    document.getElementById('totalGroups').textContent = data.data.total_groups;
                    document.getElementById('todayRecords').textContent = data.data.today_records;
                }
            } catch (error) {
                console.error('加载统计失败', error);
            }
        }

        // 加载用户列表
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const data = await response.json();
                if (data.success) {
                    const tbody = document.getElementById('usersTable');
                    tbody.innerHTML = '';

                    if (data.data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#999;">暂无用户</td></tr>';
                        return;
                    }

                    data.data.forEach(user => {
                        const row = document.createElement('tr');
                        const status = user.is_member_active ?
                            '<span class="badge badge-active">有效</span>' :
                            '<span class="badge badge-expired">已过期</span>';

                        const expiresAt = user.membership_expires_at ?
                            new Date(user.membership_expires_at).toLocaleString('zh-CN') : '-';

                        const daysLeft = user.membership_expires_at ? user.days_left : 0;

                        row.innerHTML = `
                            <td>${user.telegram_id}</td>
                            <td>@${user.username || '-'}</td>
                            <td>${user.first_name || ''} ${user.last_name || ''}</td>
                            <td>${status}</td>
                            <td>${expiresAt}</td>
                            <td>${daysLeft}天</td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载用户失败', error);
            }
        }

        // 加载群组列表
        async function loadGroups() {
            try {
                const response = await fetch('/api/groups');
                const data = await response.json();
                if (data.success) {
                    const tbody = document.getElementById('groupsTable');
                    tbody.innerHTML = '';

                    if (data.data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#999;">暂无群组</td></tr>';
                        return;
                    }

                    data.data.forEach(group => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${group.telegram_id}</td>
                            <td>${group.title || '-'}</td>
                            <td>${group.record_count}</td>
                            <td>${new Date(group.created_at).toLocaleString('zh-CN')}</td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载群组失败', error);
            }
        }

        // 授权用户
        async function authorizeUser(event) {
            event.preventDefault();

            const identifier = document.getElementById('authUserIdentifier').value;
            const days = document.getElementById('authDays').value;

            try {
                const response = await fetch('/api/authorize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({identifier, days: parseInt(days)})
                });

                const data = await response.json();
                const msgDiv = document.getElementById('authorizeMessage');

                if (data.success) {
                    msgDiv.innerHTML = '<div class="success">✅ ' + data.message + '</div>';
                    document.getElementById('authUserIdentifier').value = '';
                    document.getElementById('authDays').value = '30';
                    loadUsers();
                } else {
                    msgDiv.innerHTML = '<div class="error">❌ ' + data.message + '</div>';
                }

                setTimeout(() => {
                    msgDiv.innerHTML = '';
                }, 5000);
            } catch (error) {
                document.getElementById('authorizeMessage').innerHTML =
                    '<div class="error">❌ 网络错误：' + error.message + '</div>';
            }
        }

        // 页面加载时初始化
        window.onload = function() {
            loadStats();
            loadUsers();
            loadGroups();

            // 每30秒刷新一次统计
            setInterval(loadStats, 30000);
        };
    </script>
</body>
</html>
"""


def async_route(f):
    """装饰器：将异步函数转换为同步Flask路由"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapped


def login_required(f):
    """装饰器：检查登录状态"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


@app.route('/')
@login_required
def index():
    """管理后台主页"""
    return render_template_string(
        ADMIN_TEMPLATE,
        price_30=config.MEMBERSHIP_PRICE_30_DAYS,
        price_90=config.MEMBERSHIP_PRICE_90_DAYS,
        price_365=config.MEMBERSHIP_PRICE_365_DAYS
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == config.WEB_ADMIN_USERNAME and password == config.WEB_ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error='用户名或密码错误')

    return render_template_string(LOGIN_TEMPLATE, error=None)


@app.route('/logout')
def logout():
    """退出登录"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/api/stats')
@login_required
@async_route
async def get_stats():
    """获取统计数据"""
    try:
        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import User, GroupChat, BookkeepingRecord

            # 总用户数
            result = await session.execute(select(func.count(User.id)))
            total_users = result.scalar()

            # 活跃会员数
            now = datetime.now()
            result = await session.execute(
                select(func.count(User.id)).where(User.membership_expires_at > now)
            )
            active_members = result.scalar()

            # 总群组数
            result = await session.execute(select(func.count(GroupChat.id)))
            total_groups = result.scalar()

            # 今日记账数
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await session.execute(
                select(func.count(BookkeepingRecord.id)).where(
                    BookkeepingRecord.created_at >= today_start
                )
            )
            today_records = result.scalar()

            return jsonify({
                'success': True,
                'data': {
                    'total_users': total_users,
                    'active_members': active_members,
                    'total_groups': total_groups,
                    'today_records': today_records
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users')
@login_required
@async_route
async def get_users():
    """获取用户列表"""
    try:
        async with db.async_session() as session:
            from sqlalchemy.future import select
            from database import User

            result = await session.execute(
                select(User).order_by(User.id.desc())
            )
            users = result.scalars().all()

            user_list = []
            for user in users:
                user_list.append({
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_member_active': user.is_member_active(),
                    'membership_expires_at': user.membership_expires_at.isoformat() if user.membership_expires_at else None,
                    'days_left': user.get_membership_days_left()
                })

            return jsonify({'success': True, 'data': user_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/groups')
@login_required
@async_route
async def get_groups():
    """获取群组列表"""
    try:
        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import GroupChat, BookkeepingRecord

            result = await session.execute(
                select(GroupChat).order_by(GroupChat.id.desc())
            )
            groups = result.scalars().all()

            group_list = []
            for group in groups:
                # 获取记账数量
                result = await session.execute(
                    select(func.count(BookkeepingRecord.id)).where(
                        BookkeepingRecord.group_id == group.id
                    )
                )
                record_count = result.scalar()

                group_list.append({
                    'id': group.id,
                    'telegram_id': group.telegram_id,
                    'title': group.title,
                    'record_count': record_count,
                    'created_at': group.created_at.isoformat()
                })

            return jsonify({'success': True, 'data': group_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/authorize', methods=['POST'])
@login_required
@async_route
async def authorize_user():
    """授权用户"""
    try:
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        days = data.get('days', 30)

        if not identifier:
            return jsonify({'success': False, 'message': '请输入用户标识'})

        # 查找用户
        if identifier.startswith('@'):
            user = await db.get_user_by_username(identifier[1:])
        else:
            try:
                user_id = int(identifier)
                user = await db.get_user_by_telegram_id(user_id)
            except ValueError:
                user = await db.get_user_by_username(identifier)

        if not user:
            return jsonify({'success': False, 'message': '未找到该用户，用户需要先启动机器人'})

        # 延长会员
        await db.extend_membership(user.id, days)

        # 重新获取用户信息
        user = await db.get_user_by_telegram_id(user.telegram_id)
        expires_str = user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'message': f'已成功授权用户 @{user.username or user.telegram_id} {days}天，到期时间：{expires_str}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    # 初始化数据库
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(db.init_db())
    loop.close()

    print(f"🎛️ Web后台管理系统启动中...")
    print(f"📍 访问地址: http://localhost:{config.WEB_ADMIN_PORT}")
    print(f"👤 默认用户名: {config.WEB_ADMIN_USERNAME}")
    print(f"🔑 默认密码: {config.WEB_ADMIN_PASSWORD}")

    app.run(
        host=config.WEB_ADMIN_HOST,
        port=config.WEB_ADMIN_PORT,
        debug=False
    )
