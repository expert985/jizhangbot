# Telegram 记账机器人

一个功能完整的 Telegram 记账机器人，支持多币种记账、会员管理、OKPAY支付集成等功能。

## 功能特性

### 📝 核心记账功能
- **快速记账**：支持多种输入格式
  - 入款：`+100`、`入款100`、`上行100`
  - 出款：`-100`、`出款100`、`下发100`
  - 余额调整：`余额+100`、`余额-100`
  - USDT记账：金额后加`u`（如`+100u`）
  - 支持小数：`+100.5`、`-88.88`

### 📊 数据统计查询
- 发送 `查` 或 `c` 查看：
  - 入款总额及明细
  - 出款总额及明细
  - 余额调整记录
  - 当前余额
  - 未下发金额
  - 手续费自动计算

### ⚙️ 参数配置
- `设置汇率 7.2` - 设置汇率
- `设置费率 0.01` - 设置费率（1%手续费）
- `设置币种 JPY` - 切换币种
- `设置商户号 12345` - 设置商户号

### 💵 USDT价格查询
- `z0` - 支付宝收款价格
- `w0` - 微信收款价格
- `b0/k0` - 银行卡收款价格
- `t0` - 泰铢价格
- `e0` - 欧元价格
- `p0` - 比索价格
- `y0` - 英镑价格

### 🧮 计算器功能
- 直接发送数学表达式：`100*7.2+50`
- 支持：`+ - * / ^ ( )`
- 可通过 `开启计算器` / `关闭计算器` 控制

### 💎 会员系统
- **授权方式**：
  1. 管理员命令授权
  2. 用户自助购买（OKPAY支付）

- **管理员命令**：
  - `/authorize @用户名 30` - 授权用户30天
  - `/membership @用户名` - 查询会员到期时间

- **自助购买**：
  - `/buy` - 选择套餐购买
  - 支持30天、90天、365天套餐
  - 通过OKPAY支付USDT

### 🔐 权限体系
- **管理员**：全部权限
- **操作员**：记账、参数设置、撤销自己的记录
- **会员用户**：使用记账功能、查看统计
- **普通用户**：需要购买会员或被授权

## 安装部署

### 1. 环境要求
- Python 3.8+
- SQLite3
- 稳定的网络连接

### 2. 安装依赖
```bash
pip3 install -r requirements.txt
```

### 3. 配置环境变量
复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
nano .env
```

**必需配置**：
```env
# Telegram Bot Token（从 @BotFather 获取）
BOT_TOKEN=your_bot_token_here

# 管理员ID（逗号分隔多个）
ADMIN_IDS=123456789,987654321

# OKPAY配置
OKPAY_APP_ID=24805
OKPAY_SECRET=9d6fDkToUqglBCEGHIKMNPbchWp4JZan

# Webhook配置（用于接收支付回调）
WEBHOOK_HOST=your_domain.com
WEBHOOK_PORT=8443
```

**可选配置**：
```env
# 会员价格（USDT）
MEMBERSHIP_PRICE_30_DAYS=10
MEMBERSHIP_PRICE_90_DAYS=25
MEMBERSHIP_PRICE_365_DAYS=80
```

### 4. 启动机器人

**方式一：使用启动脚本**
```bash
chmod +x start.sh
./start.sh
```

**方式二：手动启动**
```bash
# 启动webhook服务器
python3 webhook.py &

# 启动机器人
python3 bot.py
```

### 5. 配置OKPAY回调
在OKPAY商户后台设置回调地址：
```
https://your_domain.com:8443/webhook/okpay
```

## 使用说明

### 基础使用
1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 开始使用
3. 将机器人添加到群组
4. 使用 `/buy` 购买会员或联系管理员授权
5. 开始记账！

### 记账示例
```
+1000          # 入款1000
-500           # 出款500
+100u          # 入款100 USDT
余额+50        # 余额增加50
设置汇率 7.2   # 设置汇率
查             # 查看统计
```

### 群组管理
- 群组创建者自动成为操作员
- 管理员可以添加更多操作员
- 每个群组独立设置和记录

## 支持的币种
CNY, USD, JPY, EUR, GBP, HKD, KRW, SGD, THB, PHP, MYR, IDR, VND, TWD, AUD, CAD, NZD, CHF, SEK, DKK, NOK, RUB, INR, BRL, MXN, ZAR, TRY, AED, SAR, USDT

## 数据库说明
项目使用 SQLite 数据库，所有数据存储在 `bookkeeping.db` 文件中。

**数据表**：
- `users` - 用户信息和会员状态
- `group_chats` - 群组信息
- `group_settings` - 群组配置
- `group_operators` - 群组操作员
- `bookkeeping_records` - 记账记录
- `payments` - 支付记录

## 常见问题

### Q: 如何获取 Bot Token？
A: 在 Telegram 中联系 @BotFather，使用 `/newbot` 命令创建机器人并获取 token。

### Q: 如何获取我的 Telegram ID？
A: 联系 @userinfobot 即可查看你的用户ID。

### Q: OKPAY支付回调不工作？
A: 确保：
1. 服务器防火墙开放了 webhook 端口
2. 在OKPAY后台正确配置了回调地址
3. webhook服务器正常运行

### Q: 如何备份数据？
A: 定期备份 `bookkeeping.db` 文件即可。

### Q: 支持多个管理员吗？
A: 支持，在 `.env` 中用逗号分隔多个管理员ID。

## 技术栈
- **语言**：Python 3.8+
- **Telegram库**：python-telegram-bot
- **数据库**：SQLAlchemy + SQLite
- **Web框架**：Flask（webhook服务）
- **HTTP客户端**：aiohttp
- **异步支持**：asyncio

## 安全建议
1. 妥善保管 `.env` 文件，不要泄露
2. 使用 HTTPS 配置 webhook
3. 定期备份数据库
4. 及时更新依赖包

## 开发计划
- [ ] Web管理后台
- [ ] 数据导出（Excel/CSV）
- [ ] 多语言支持
- [ ] 更多支付方式
- [ ] 图表统计分析

## 许可证
MIT License

## 联系方式
如有问题或建议，请通过 GitHub Issues 反馈。

## 致谢
- 参考项目：https://miha.uk/docs/tutor/telegram-bookkeeping-bot/
- OKPAY支付：@okpay
