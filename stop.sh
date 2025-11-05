#!/bin/bash

# 停止所有服务

echo "正在停止所有服务..."

# 从PID文件读取进程ID并杀死
if [ -f logs/webhook.pid ]; then
    kill $(cat logs/webhook.pid) 2>/dev/null
    rm logs/webhook.pid
    echo "✅ Webhook服务器已停止"
fi

if [ -f logs/web_bill.pid ]; then
    kill $(cat logs/web_bill.pid) 2>/dev/null
    rm logs/web_bill.pid
    echo "✅ Web账单系统已停止"
fi

if [ -f logs/web_admin.pid ]; then
    kill $(cat logs/web_admin.pid) 2>/dev/null
    rm logs/web_admin.pid
    echo "✅ Web后台系统已停止"
fi

# 查找并杀死相关Python进程
pkill -f "python3 webhook.py" 2>/dev/null
pkill -f "python3 web_bill.py" 2>/dev/null
pkill -f "python3 web_admin.py" 2>/dev/null
pkill -f "python3 bot.py" 2>/dev/null

echo "🎉 所有服务已完全停止"
