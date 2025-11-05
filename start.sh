#!/bin/bash

# Telegram 记账机器人完整启动脚本

echo "========================================="
echo "  Telegram 记账机器人启动程序"
echo "========================================="

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "❌ 错误：.env 文件不存在！"
    echo "请复制 .env.example 为 .env 并配置相关参数"
    exit 1
fi

# 检查Python版本
echo ""
echo "📋 检查Python版本..."
python3 --version

# 安装依赖
echo ""
echo "📦 安装依赖..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt -q
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt -q
else
    echo "⚠️  警告：未找到 pip 或 pip3，跳过依赖安装"
    echo "请手动运行：python3 -m pip install -r requirements.txt"
fi

echo ""
echo "🚀 启动所有服务..."
echo ""

# 启动webhook服务器（后台运行）
echo "1️⃣  启动OKPAY回调服务器（端口8443）..."
nohup python3 webhook.py > logs/webhook.log 2>&1 &
WEBHOOK_PID=$!
echo "   ✅ Webhook服务器已启动 (PID: $WEBHOOK_PID)"

# 启动Web账单系统（后台运行）
echo "2️⃣  启动Web账单查询系统（端口52000）..."
nohup python3 web_bill.py > logs/web_bill.log 2>&1 &
WEB_BILL_PID=$!
echo "   ✅ Web账单系统已启动 (PID: $WEB_BILL_PID)"

# 启动Web后台管理（后台运行）
echo "3️⃣  启动Web后台管理系统（端口38888）..."
nohup python3 web_admin.py > logs/web_admin.log 2>&1 &
WEB_ADMIN_PID=$!
echo "   ✅ Web后台已启动 (PID: $WEB_ADMIN_PID)"

# 等待服务启动
sleep 3

echo "4️⃣  启动Telegram机器人..."
echo ""
echo "========================================="
echo "  所有服务已启动"
echo "========================================="
echo "📱 Telegram机器人: 运行中"
echo "🔗 OKPAY回调: http://localhost:8443"
echo "📊 Web账单: http://localhost:52000"
echo "🎛️  Web后台: http://localhost:38888"
echo "========================================="
echo ""

# 保存PID到文件
echo $WEBHOOK_PID > logs/webhook.pid
echo $WEB_BILL_PID > logs/web_bill.pid
echo $WEB_ADMIN_PID > logs/web_admin.pid

# 启动机器人（前台运行）
python3 bot.py

# 如果机器人退出，关闭所有后台服务
echo ""
echo "⚠️  机器人已停止，正在关闭所有服务..."
kill $WEBHOOK_PID 2>/dev/null
kill $WEB_BILL_PID 2>/dev/null
kill $WEB_ADMIN_PID 2>/dev/null
echo "✅ 所有服务已关闭"
