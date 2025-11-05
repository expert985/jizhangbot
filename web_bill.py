"""
Web账单查询系统 - 端口52000
用户可以通过网页查看记账记录
"""
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import config
from database import db

app = Flask(__name__)

# 网页模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>记账账单查询</title>
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
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 32px;
        }
        .search-box {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
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
        input, select, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 {
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        .stat-card p {
            font-size: 24px;
            font-weight: bold;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
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
        .badge-income {
            background: #d4edda;
            color: #155724;
        }
        .badge-expense {
            background: #f8d7da;
            color: #721c24;
        }
        .badge-balance {
            background: #d1ecf1;
            color: #0c5460;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            h1 {
                font-size: 24px;
            }
            .stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 记账账单查询系统</h1>

        <div class="search-box">
            <div class="form-group">
                <label for="groupId">群组ID：</label>
                <input type="number" id="groupId" placeholder="请输入Telegram群组ID">
            </div>
            <div class="form-group">
                <label for="dateRange">日期范围：</label>
                <select id="dateRange">
                    <option value="today">今天</option>
                    <option value="yesterday">昨天</option>
                    <option value="week">最近7天</option>
                    <option value="month">最近30天</option>
                    <option value="all">全部</option>
                </select>
            </div>
            <button onclick="searchRecords()">🔍 查询账单</button>
        </div>

        <div id="result" style="display:none;">
            <div class="stats">
                <div class="stat-card">
                    <h3>💰 入款总额</h3>
                    <p id="incomeTotal">0</p>
                </div>
                <div class="stat-card">
                    <h3>💸 出款总额</h3>
                    <p id="expenseTotal">0</p>
                </div>
                <div class="stat-card">
                    <h3>🔄 余额调整</h3>
                    <p id="balanceAdjust">0</p>
                </div>
                <div class="stat-card">
                    <h3>💵 当前余额</h3>
                    <p id="currentBalance">0</p>
                </div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>时间</th>
                            <th>类型</th>
                            <th>金额</th>
                            <th>币种</th>
                            <th>操作员</th>
                        </tr>
                    </thead>
                    <tbody id="recordsTable">
                    </tbody>
                </table>
            </div>
        </div>

        <div id="loading" class="loading" style="display:none;">
            加载中...
        </div>

        <div id="error" class="error" style="display:none;"></div>
    </div>

    <script>
        async function searchRecords() {
            const groupId = document.getElementById('groupId').value;
            const dateRange = document.getElementById('dateRange').value;

            if (!groupId) {
                showError('请输入群组ID');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
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

        function displayRecords(data) {
            document.getElementById('result').style.display = 'block';

            // 更新统计数据
            document.getElementById('incomeTotal').textContent = data.income_total.toFixed(2);
            document.getElementById('expenseTotal').textContent = data.expense_total.toFixed(2);
            document.getElementById('balanceAdjust').textContent = data.balance_adjustments.toFixed(2);
            document.getElementById('currentBalance').textContent = data.balance.toFixed(2);

            // 更新记录表格
            const tbody = document.getElementById('recordsTable');
            tbody.innerHTML = '';

            if (data.records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#999;">暂无记录</td></tr>';
                return;
            }

            data.records.forEach(record => {
                const row = document.createElement('tr');

                let badgeClass = 'badge-income';
                let typeName = '入款';
                if (record.record_type === 'expense') {
                    badgeClass = 'badge-expense';
                    typeName = '出款';
                } else if (record.record_type === 'balance') {
                    badgeClass = 'badge-balance';
                    typeName = '余额调整';
                }

                row.innerHTML = `
                    <td>${new Date(record.created_at).toLocaleString('zh-CN')}</td>
                    <td><span class="badge ${badgeClass}">${typeName}</span></td>
                    <td><strong>${record.amount.toFixed(2)}</strong></td>
                    <td>${record.currency}</td>
                    <td>${record.username || 'ID:' + record.user_id}</td>
                `;
                tbody.appendChild(row);
            });
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
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


@app.route('/api/records')
@async_route
async def get_records():
    """获取记账记录API"""
    try:
        group_id = request.args.get('group_id', type=int)
        date_range = request.args.get('date_range', 'today')

        if not group_id:
            return jsonify({'success': False, 'message': '缺少群组ID'})

        # 获取群组
        async with db.async_session() as session:
            from sqlalchemy.future import select
            from database import GroupChat
            result = await session.execute(
                select(GroupChat).where(GroupChat.telegram_id == group_id)
            )
            group = result.scalar_one_or_none()

            if not group:
                return jsonify({'success': False, 'message': '群组不存在'})

            # 计算日期范围
            start_date = None
            if date_range == 'today':
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == 'yesterday':
                start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif date_range == 'month':
                start_date = datetime.now() - timedelta(days=30)

            # 获取记账汇总
            summary = await db.get_records_summary(group.id, start_date=start_date)

            # 格式化记录，添加用户名
            records_with_username = []
            for record in summary['records']:
                result = await session.execute(
                    select(db.User).where(db.User.id == record.user_id)
                )
                user = result.scalar_one_or_none()

                records_with_username.append({
                    'id': record.id,
                    'record_type': record.record_type,
                    'amount': record.amount,
                    'currency': record.currency,
                    'created_at': record.created_at.isoformat(),
                    'user_id': record.user_id,
                    'username': user.username if user else None
                })

            return jsonify({
                'success': True,
                'data': {
                    'income_total': summary['income_total'],
                    'expense_total': summary['expense_total'],
                    'balance_adjustments': summary['balance_adjustments'],
                    'balance': summary['balance'],
                    'records': records_with_username
                }
            })

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

    app.run(
        host=config.WEB_BILL_HOST,
        port=config.WEB_BILL_PORT,
        debug=False
    )
