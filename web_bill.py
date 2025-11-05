#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web账单查询系统 - 端口52000
参考专业记账系统设计，提供详细的账单查询和统计功能
"""
from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import io
import config
from database import db

app = Flask(__name__)

# 专业账单网页模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能记账单查询系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes shimmer {
            0%, 100% { color: #ffd700; text-shadow: 0 0 10px #ffd700; }
            50% { color: #ffed4e; text-shadow: 0 0 20px #ffd700, 0 0 30px #ffd700; }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        @keyframes countUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            min-height: 100vh;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* 粒子背景 */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }

        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: rgba(255, 215, 0, 0.5);
            border-radius: 50%;
            animation: float 3s infinite ease-in-out;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        h1 {
            text-align: center;
            font-size: 42px;
            font-weight: bold;
            background: linear-gradient(45deg, #ffd700, #ffed4e, #ffd700);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 3s ease-in-out infinite;
            margin-bottom: 30px;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
        }

        /* 查询面板 */
        .query-panel {
            background: rgba(30, 30, 50, 0.9);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 215, 0, 0.3);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: #ffd700;
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 16px;
        }

        input, select {
            width: 100%;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 215, 0, 0.3);
            border-radius: 10px;
            color: white;
            font-size: 16px;
            transition: all 0.3s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #ffd700;
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        }

        input::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }

        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            border: none;
            border-radius: 10px;
            color: #1a1a2e;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.5);
        }

        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, rgba(30, 30, 50, 0.9) 0%, rgba(40, 40, 70, 0.9) 100%);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 215, 0, 0.3);
            border-radius: 20px;
            padding: 25px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: #ffd700;
            box-shadow: 0 15px 40px rgba(255, 215, 0, 0.3);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(180deg, #ffd700 0%, #ff6b35 100%);
        }

        .stat-card h3 {
            color: #ffd700;
            font-size: 18px;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: white;
            margin-bottom: 10px;
            animation: countUp 0.5s ease-out;
        }

        .stat-value.income {
            color: #4ade80;
        }

        .stat-value.expense {
            color: #ff6b35;
        }

        .stat-value.warning {
            color: #ff6b35;
            animation: shimmer 2s ease-in-out infinite;
        }

        .stat-sub {
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
        }

        /* 交易列表 */
        .transactions-section {
            background: rgba(30, 30, 50, 0.9);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 215, 0, 0.3);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
        }

        .section-title {
            color: #ffd700;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 215, 0, 0.3);
        }

        .transaction-list {
            max-height: 600px;
            overflow-y: auto;
            padding-right: 10px;
        }

        .transaction-list::-webkit-scrollbar {
            width: 8px;
        }

        .transaction-list::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .transaction-list::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #ffd700 0%, #ff6b35 100%);
            border-radius: 10px;
        }

        .transaction-item {
            background: linear-gradient(135deg, rgba(40, 40, 60, 0.8) 0%, rgba(50, 50, 80, 0.8) 100%);
            border-left: 4px solid #ffd700;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            position: relative;
            transition: all 0.3s;
        }

        .transaction-item:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(255, 215, 0, 0.2);
        }

        .transaction-item.income {
            border-left-color: #4ade80;
        }

        .transaction-item.expense {
            border-left-color: #ff6b35;
        }

        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .transaction-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }

        .transaction-badge.income {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }

        .transaction-badge.expense {
            background: rgba(255, 107, 53, 0.2);
            color: #ff6b35;
        }

        .transaction-badge.balance {
            background: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
        }

        .transaction-amount {
            font-size: 28px;
            font-weight: bold;
            color: white;
        }

        .transaction-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 215, 0, 0.1);
        }

        .transaction-detail {
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
        }

        .transaction-detail strong {
            color: #ffd700;
            display: block;
            margin-bottom: 5px;
        }

        /* 悬浮按钮 */
        .float-buttons {
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }

        .float-btn {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #1a1a2e;
            padding: 12px 20px;
            border: none;
            border-radius: 30px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3);
        }

        .float-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(255, 215, 0, 0.5);
        }

        /* 未下发弹窗 */
        .alert-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(255, 107, 53, 0.95) 0%, rgba(255, 59, 48, 0.95) 100%);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            z-index: 2000;
            display: none;
            animation: countUp 0.5s ease-out;
        }

        .alert-modal.show {
            display: block;
        }

        .alert-modal h2 {
            color: white;
            font-size: 28px;
            margin-bottom: 20px;
        }

        .alert-modal .amount {
            font-size: 48px;
            font-weight: bold;
            color: white;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
        }

        .loading {
            text-align: center;
            padding: 60px;
            color: #ffd700;
            font-size: 20px;
        }

        .loading::after {
            content: '...';
            animation: shimmer 1.5s infinite;
        }

        .error {
            background: rgba(255, 107, 53, 0.2);
            border: 2px solid #ff6b35;
            color: #ff6b35;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }

        .empty {
            text-align: center;
            padding: 60px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 18px;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 28px;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .transaction-amount {
                font-size: 22px;
            }

            .float-buttons {
                top: auto;
                bottom: 20px;
                right: 20px;
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <!-- 粒子背景 -->
    <div class="particles" id="particles"></div>

    <!-- 悬浮按钮 -->
    <div class="float-buttons">
        <button class="float-btn" onclick="checkApiStatus()">📡 API状态</button>
        <button class="float-btn" onclick="exportToExcel()">📊 导出表格</button>
    </div>

    <!-- 未下发弹窗 -->
    <div class="alert-modal" id="alertModal">
        <h2>⚠️ 注意：有未下发金额</h2>
        <div class="amount" id="alertAmount">0</div>
        <p style="color: white; margin-top: 20px;">5秒后自动关闭</p>
    </div>

    <div class="container">
        <h1>💎 智能记账单查询系统</h1>

        <!-- 查询面板 -->
        <div class="query-panel">
            <div class="form-group">
                <label>🔍 群组ID：</label>
                <input type="text" id="groupId" placeholder="请输入Telegram群组ID（例如：-1001234567890）">
            </div>
            <div class="form-group">
                <label>📅 日期范围：</label>
                <select id="dateRange">
                    <option value="today">今天</option>
                    <option value="yesterday">昨天</option>
                    <option value="week">最近7天</option>
                    <option value="month">最近30天</option>
                    <option value="all">全部记录</option>
                </select>
            </div>
            <button class="btn" onclick="searchRecords()">🔎 查询账单</button>
        </div>

        <!-- 统计卡片 -->
        <div id="statsSection" style="display:none;">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>💰 入款明细</h3>
                    <div class="stat-value income" id="incomeTotal">0</div>
                    <div class="stat-sub">
                        <div>入款笔数：<span id="incomeCount">0</span> 笔</div>
                        <div>手续费率：<span id="feeRate">0</span>%</div>
                        <div>汇率：<span id="exchangeRate">0</span></div>
                    </div>
                </div>

                <div class="stat-card">
                    <h3>💸 出款明细</h3>
                    <div class="stat-value expense" id="expenseTotal">0</div>
                    <div class="stat-sub">
                        <div>出款笔数：<span id="expenseCount">0</span> 笔</div>
                        <div style="margin-top: 10px;">
                            <strong style="color: #ff6b35;">未下发金额：</strong>
                            <span class="stat-value warning" id="undelivered" style="font-size: 24px;">0</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <h3>🔄 余额调整</h3>
                    <div class="stat-value" id="balanceAdjust">0</div>
                    <div class="stat-sub">
                        <div>当前余额：<span id="currentBalance">0</span></div>
                        <div>币种：<span id="currency">CNY</span></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 交易列表 -->
        <div id="transactionsSection" style="display:none;">
            <div class="transactions-section">
                <div class="section-title">📋 入款记录</div>
                <div class="transaction-list" id="incomeList"></div>
            </div>

            <div class="transactions-section">
                <div class="section-title">📋 出款记录</div>
                <div class="transaction-list" id="expenseList"></div>
            </div>

            <div class="transactions-section" id="balanceSection" style="display:none;">
                <div class="section-title">📋 余额调整记录</div>
                <div class="transaction-list" id="balanceList"></div>
            </div>
        </div>

        <div id="loading" class="loading" style="display:none;">
            正在加载数据
        </div>

        <div id="error" class="error" style="display:none;"></div>
    </div>

    <script>
        // 创建粒子背景
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 3 + 's';
                particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
                container.appendChild(particle);
            }
        }

        // 检查URL参数
        window.onload = function() {
            createParticles();

            const urlParams = new URLSearchParams(window.location.search);
            const groupId = urlParams.get('group');
            if (groupId) {
                document.getElementById('groupId').value = groupId;
                searchRecords();
            }
        };

        // 查询记账记录
        async function searchRecords() {
            const groupId = document.getElementById('groupId').value;
            const dateRange = document.getElementById('dateRange').value;

            if (!groupId) {
                showError('请输入群组ID');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('statsSection').style.display = 'none';
            document.getElementById('transactionsSection').style.display = 'none';
            document.getElementById('error').style.display = 'none';

            try {
                const response = await fetch(`/api/records?group_id=${groupId}&date_range=${dateRange}`);
                const data = await response.json();

                if (data.success) {
                    displayRecords(data.data);
                } else {
                    showError(data.message || '查询失败');
                }
            } catch (error) {
                showError('网络错误：' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        // 显示记账数据
        function displayRecords(data) {
            document.getElementById('statsSection').style.display = 'block';
            document.getElementById('transactionsSection').style.display = 'block';

            // 更新统计数据
            animateNumber('incomeTotal', data.income_total);
            animateNumber('expenseTotal', data.expense_total);
            animateNumber('balanceAdjust', data.balance_adjustments);
            animateNumber('currentBalance', data.balance);
            animateNumber('undelivered', data.undelivered);

            document.getElementById('incomeCount').textContent = data.income_count;
            document.getElementById('expenseCount').textContent = data.expense_count;
            document.getElementById('feeRate').textContent = (data.fee_rate * 100).toFixed(2);
            document.getElementById('exchangeRate').textContent = data.exchange_rate;
            document.getElementById('currency').textContent = data.currency;

            // 如果有未下发金额，显示警告弹窗
            if (data.undelivered > 0) {
                showAlert(data.undelivered);
            }

            // 显示交易列表
            displayTransactionList('incomeList', data.income_records, 'income');
            displayTransactionList('expenseList', data.expense_records, 'expense');

            if (data.balance_records.length > 0) {
                document.getElementById('balanceSection').style.display = 'block';
                displayTransactionList('balanceList', data.balance_records, 'balance');
            }
        }

        // 显示交易列表
        function displayTransactionList(containerId, records, type) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';

            if (records.length === 0) {
                container.innerHTML = '<div class="empty">暂无记录</div>';
                return;
            }

            records.forEach((record, index) => {
                const item = document.createElement('div');
                item.className = `transaction-item ${type}`;

                let badgeText = '入款';
                let badgeClass = 'income';
                if (type === 'expense') {
                    badgeText = '出款';
                    badgeClass = 'expense';
                } else if (type === 'balance') {
                    badgeText = '余额调整';
                    badgeClass = 'balance';
                }

                const typePrefix = type === 'income' ? '入' : (type === 'expense' ? '出' : '调');

                item.innerHTML = `
                    <div class="transaction-header">
                        <span class="transaction-badge ${badgeClass}">${typePrefix}${index + 1} - ${badgeText}</span>
                        <span class="transaction-amount">${record.amount.toFixed(2)} ${record.currency}</span>
                    </div>
                    <div class="transaction-details">
                        <div class="transaction-detail">
                            <strong>📅 时间</strong>
                            ${new Date(record.created_at).toLocaleString('zh-CN')}
                        </div>
                        <div class="transaction-detail">
                            <strong>👤 操作员</strong>
                            ${record.username ? '@' + record.username : 'ID:' + record.user_id}
                        </div>
                        ${record.is_usdt ? '<div class="transaction-detail"><strong>💵 类型</strong>USDT记账</div>' : ''}
                        ${record.description ? '<div class="transaction-detail"><strong>📝 备注</strong>' + record.description + '</div>' : ''}
                    </div>
                `;

                container.appendChild(item);
            });
        }

        // 数字动画
        function animateNumber(elementId, endValue) {
            const element = document.getElementById(elementId);
            const startValue = 0;
            const duration = 1000;
            const startTime = performance.now();

            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                const currentValue = startValue + (endValue - startValue) * progress;
                element.textContent = currentValue.toFixed(2);

                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            }

            requestAnimationFrame(update);
        }

        // 显示警告弹窗
        function showAlert(amount) {
            const modal = document.getElementById('alertModal');
            document.getElementById('alertAmount').textContent = amount.toFixed(2);
            modal.classList.add('show');

            setTimeout(() => {
                modal.classList.remove('show');
            }, 5000);
        }

        // 显示错误
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }

        // 检查API状态
        async function checkApiStatus() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                alert(data.status === 'ok' ? '✅ API连接正常' : '❌ API连接异常');
            } catch (error) {
                alert('❌ API连接失败：' + error.message);
            }
        }

        // 导出Excel
        async function exportToExcel() {
            const groupId = document.getElementById('groupId').value;
            const dateRange = document.getElementById('dateRange').value;

            if (!groupId) {
                alert('请先查询记账记录');
                return;
            }

            window.location.href = `/api/export?group_id=${groupId}&date_range=${dateRange}`;
        }

        // 支持回车键查询
        document.getElementById('groupId').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchRecords();
            }
        });
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


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


@app.route('/api/records')
@async_route
async def get_records():
    """获取记账记录API"""
    try:
        group_id = request.args.get('group_id', type=int)
        date_range = request.args.get('date_range', 'today')

        # 处理负数群组ID（移除前面的-号）
        if group_id and str(group_id).startswith('-'):
            group_id = abs(group_id)

        if not group_id:
            return jsonify({'success': False, 'message': '缺少群组ID'})

        # 获取群组
        async with db.async_session() as session:
            from sqlalchemy.future import select
            from database import GroupChat, User, GroupSettings

            # 尝试正负数查询
            result = await session.execute(
                select(GroupChat).where(
                    (GroupChat.telegram_id == group_id) | (GroupChat.telegram_id == -group_id)
                )
            )
            group = result.scalar_one_or_none()

            if not group:
                return jsonify({'success': False, 'message': '群组不存在或未使用过机器人'})

            # 计算日期范围
            start_date = None
            end_date = None
            if date_range == 'today':
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == 'yesterday':
                yesterday = datetime.now() - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif date_range == 'month':
                start_date = datetime.now() - timedelta(days=30)

            # 获取记账汇总
            summary = await db.get_records_summary(group.id, start_date=start_date, end_date=end_date)

            # 获取群组设置
            settings = await db.get_group_settings(group.id)

            # 分类记录
            income_records = []
            expense_records = []
            balance_records = []

            for record in summary['records']:
                # 获取用户信息
                result = await session.execute(
                    select(User).where(User.id == record.user_id)
                )
                user = result.scalar_one_or_none()

                record_data = {
                    'id': record.id,
                    'record_type': record.record_type,
                    'amount': record.amount,
                    'currency': record.currency,
                    'is_usdt': record.is_usdt,
                    'description': record.description,
                    'created_at': record.created_at.isoformat(),
                    'user_id': record.user_id,
                    'username': user.username if user else None
                }

                if record.record_type == 'income':
                    income_records.append(record_data)
                elif record.record_type == 'expense':
                    expense_records.append(record_data)
                elif record.record_type == 'balance':
                    balance_records.append(record_data)

            # 计算未下发金额
            undelivered = summary['income_total'] - summary['expense_total']

            return jsonify({
                'success': True,
                'data': {
                    'income_total': summary['income_total'],
                    'expense_total': summary['expense_total'],
                    'balance_adjustments': summary['balance_adjustments'],
                    'balance': summary['balance'],
                    'undelivered': undelivered,
                    'income_count': len(income_records),
                    'expense_count': len(expense_records),
                    'fee_rate': settings.fee_rate if settings else 0.01,
                    'exchange_rate': settings.exchange_rate if settings else 7.2,
                    'currency': settings.currency if settings else 'CNY',
                    'income_records': income_records,
                    'expense_records': expense_records,
                    'balance_records': balance_records
                }
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/export')
@async_route
async def export_excel():
    """导出Excel"""
    try:
        group_id = request.args.get('group_id', type=int)
        date_range = request.args.get('date_range', 'today')

        if not group_id:
            return jsonify({'success': False, 'message': '缺少群组ID'})

        # 这里简化实现，返回CSV格式
        # 实际项目中可以使用 openpyxl 或 xlsxwriter 生成真正的Excel

        # 获取数据
        response = await get_records()
        data = response.json

        if not data.get('success'):
            return jsonify({'success': False, 'message': '获取数据失败'})

        records_data = data['data']

        # 生成CSV内容
        csv_content = "记账类型,金额,币种,时间,操作员,备注\n"

        for record in records_data['income_records']:
            csv_content += f"入款,{record['amount']},{record['currency']},{record['created_at']},{record['username'] or record['user_id']},{record['description'] or ''}\n"

        for record in records_data['expense_records']:
            csv_content += f"出款,{record['amount']},{record['currency']},{record['created_at']},{record['username'] or record['user_id']},{record['description'] or ''}\n"

        for record in records_data['balance_records']:
            csv_content += f"余额调整,{record['amount']},{record['currency']},{record['created_at']},{record['username'] or record['user_id']},{record['description'] or ''}\n"

        # 返回CSV文件
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8-sig'))  # 使用UTF-8 BOM以便Excel正确识别中文
        output.seek(0)

        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'账单_{group_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    # 初始化数据库
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(db.init_db())
    loop.close()

    print(f"🌐 Web账单系统启动中...")
    print(f"📍 访问地址: http://localhost:{config.WEB_BILL_PORT}")
    print(f"💡 提示：URL支持 ?group=群组ID 参数自动查询")

    app.run(
        host=config.WEB_BILL_HOST,
        port=config.WEB_BILL_PORT,
        debug=False
    )
