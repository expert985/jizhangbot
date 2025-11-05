#!/bin/bash

# Telegram 记账机器人启动脚本

echo "正在启动 Telegram 记账机器人..."

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "错误：.env 文件不存在！"
    echo "请复制 .env.example 为 .env 并配置相关参数"
    exit 1
fi

# 检查Python版本
python3 --version

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt

# 启动webhook服务器（后台运行）
echo "启动webhook服务器..."
nohup python3 webhook.py > webhook.log 2>&1 &
WEBHOOK_PID=$!
echo "Webhook服务器PID: $WEBHOOK_PID"

# 等待webhook服务器启动
sleep 2

# 启动机器人
echo "启动机器人..."
python3 bot.py

# 如果机器人退出，关闭webhook服务器
kill $WEBHOOK_PID 2>/dev/null
