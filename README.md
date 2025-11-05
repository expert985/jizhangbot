# Telegram 记账机器人

一个功能完整的 Telegram 记账机器人，支持多币种记账、会员管理、OKPAY支付集成、Web账单查询和后台管理等功能。

## 🎯 功能特性

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

- **套餐价格设置**（在 `.env` 文件中配置）：
  ```env
  MEMBERSHIP_PRICE_30_DAYS=10    # 30天套餐价格（USDT）
  MEMBERSHIP_PRICE_90_DAYS=25    # 90天套餐价格（USDT）
  MEMBERSHIP_PRICE_365_DAYS=80   # 365天套餐价格（USDT）
  ```

### 🌐 Web账单查询系统（端口52000）
- **访问地址**：`http://your-server:52000`
- **功能**：
  - 输入群组ID查询记账记录
  - 选择日期范围（今天/昨天/最近7天/最近30天/全部）
  - 实时显示统计数据（入款、出款、余额、调整）
  - 详细记录表格展示
  - 响应式设计，支持移动端

### 🎛️ Web后台管理系统（端口38888）
- **访问地址**：`http://your-server:38888`
- **默认账号**：
  ```
  用户名: admin
  密码: 123456
  ```
  （可在 `.env` 文件中修改）

- **管理功能**：
  - **统计面板**：总用户数、活跃会员、总群组数、今日记账数
  - **用户管理**：查看所有用户、会员状态、到期时间
  - **授权会员**：通过Web界面快速授权用户
  - **群组管理**：查看所有群组、记账数量
  - **套餐设置**：查看当前套餐价格配置

### 🔐 权限体系
- **管理员**：全部权限
- **操作员**：记账、参数设置、撤销自己的记录
- **会员用户**：使用记账功能、查看统计
- **普通用户**：需要购买会员或被授权

## 📦 安装部署

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

# Web账单系统
WEB_BILL_PORT=52000
WEB_BILL_HOST=0.0.0.0

# Web后台系统
WEB_ADMIN_PORT=38888
WEB_ADMIN_HOST=0.0.0.0
WEB_ADMIN_USERNAME=admin
WEB_ADMIN_PASSWORD=123456
```

### 4. 启动机器人

**方式一：使用启动脚本（推荐）**
```bash
chmod +x start.sh
./start.sh
```

启动后会自动运行以下服务：
- ✅ OKPAY回调服务器（端口8443）
- ✅ Web账单查询系统（端口52000）
- ✅ Web后台管理系统（端口38888）
- ✅ Telegram机器人

**方式二：手动启动各个服务**
```bash
# 终端1：启动webhook
python3 webhook.py

# 终端2：启动Web账单
python3 web_bill.py

# 终端3：启动Web后台
python3 web_admin.py

# 终端4：启动机器人
python3 bot.py
```

**停止所有服务**：
```bash
./stop.sh
```

### 5. 配置OKPAY回调
在OKPAY商户后台设置回调地址：
```
https://your_domain.com:8443/webhook/okpay
```

### 6. 访问Web服务

**Web账单查询**：
```
http://your-server-ip:52000
```

**Web后台管理**：
```
http://your-server-ip:38888
登录账号: admin
登录密码: 123456
```

## 📖 使用说明

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

### 管理员操作

**通过Telegram机器人授权**：
```
/authorize @jdccc 30      # 授权用户30天
/membership @jdccc        # 查询会员到期时间
```

**通过Web后台授权**：
1. 访问 `http://your-server:38888`
2. 登录后台
3. 点击"授权会员"标签
4. 输入用户名或ID和天数
5. 点击授权

### Web账单查询
1. 访问 `http://your-server:52000`
2. 输入群组ID（Telegram群组ID）
3. 选择日期范围
4. 点击查询账单
5. 查看详细统计和记录

### 群组管理
- 群组创建者自动成为操作员
- 管理员可以添加更多操作员
- 每个群组独立设置和记录

## 📂 项目结构

```
jizhangbot/
├── bot.py              # Telegram机器人主程序
├── database.py         # 数据库模型和操作
├── config.py           # 配置管理
├── okpay.py           # OKPAY支付集成
├── webhook.py         # OKPAY回调服务器（端口8443）
├── web_bill.py        # Web账单查询系统（端口52000）
├── web_admin.py       # Web后台管理系统（端口38888）
├── requirements.txt   # Python依赖包
├── start.sh          # 启动脚本
├── stop.sh           # 停止脚本
├── .env.example      # 环境变量示例
├── README.md         # 项目文档
└── logs/             # 日志目录
    ├── webhook.log
    ├── web_bill.log
    └── web_admin.log
```

## 🎨 支持的币种
CNY, USD, JPY, EUR, GBP, HKD, KRW, SGD, THB, PHP, MYR, IDR, VND, TWD, AUD, CAD, NZD, CHF, SEK, DKK, NOK, RUB, INR, BRL, MXN, ZAR, TRY, AED, SAR, USDT

## 💾 数据库说明
项目使用 SQLite 数据库，所有数据存储在 `bookkeeping.db` 文件中。

**数据表**：
- `users` - 用户信息和会员状态
- `group_chats` - 群组信息
- `group_settings` - 群组配置
- `group_operators` - 群组操作员
- `bookkeeping_records` - 记账记录
- `payments` - 支付记录

## ❓ 常见问题

### Q: 如何获取 Bot Token？
A: 在 Telegram 中联系 @BotFather，使用 `/newbot` 命令创建机器人并获取 token。

### Q: 如何获取我的 Telegram ID？
A: 联系 @userinfobot 即可查看你的用户ID。

### Q: 如何获取群组ID？
A: 
1. 将 @userinfobot 添加到群组
2. 机器人会显示群组ID（负数，如 -1001234567890）
3. 在Web账单查询时使用这个ID

### Q: Web后台无法访问？
A: 检查：
1. 服务是否正常启动（查看 logs/web_admin.log）
2. 防火墙是否开放38888端口
3. 是否使用正确的IP地址

### Q: OKPAY支付回调不工作？
A: 确保：
1. 服务器防火墙开放了8443端口
2. 在OKPAY后台正确配置了回调地址
3. webhook服务器正常运行（查看 logs/webhook.log）

### Q: 如何修改套餐价格？
A: 编辑 `.env` 文件中的以下配置：
```env
MEMBERSHIP_PRICE_30_DAYS=10
MEMBERSHIP_PRICE_90_DAYS=25
MEMBERSHIP_PRICE_365_DAYS=80
```
修改后重启机器人生效。

### Q: 如何备份数据？
A: 定期备份 `bookkeeping.db` 文件即可。

### Q: 支持多个管理员吗？
A: 支持，在 `.env` 中用逗号分隔多个管理员ID。

### Q: 忘记Web后台密码怎么办？
A: 在 `.env` 文件中修改 `WEB_ADMIN_PASSWORD` 配置，然后重启服务。

## 🔒 安全建议
1. 妥善保管 `.env` 文件，不要泄露
2. 使用强密码作为Web后台密码
3. 使用 HTTPS 配置 webhook
4. 定期备份数据库
5. 及时更新依赖包
6. 限制Web服务的访问IP（如使用nginx反向代理）

## 🛠️ 技术栈
- **语言**：Python 3.8+
- **Telegram库**：python-telegram-bot 20.7
- **数据库**：SQLAlchemy + SQLite
- **Web框架**：Flask
- **HTTP客户端**：aiohttp
- **异步支持**：asyncio

## 📊 开发计划
- [ ] 数据导出（Excel/CSV）
- [ ] 多语言支持
- [ ] 更多支付方式
- [ ] 图表统计分析
- [ ] API接口开放
- [ ] Docker部署支持

## 📜 许可证
MIT License

## 📞 联系方式
如有问题或建议，请通过 GitHub Issues 反馈。

## 🙏 致谢
- 参考项目：https://miha.uk/docs/tutor/telegram-bookkeeping-bot/
- OKPAY支付：@okpay

## 📸 截图预览

### Telegram机器人界面
- 支持快速记账
- 实时统计查询
- 会员购买流程

### Web账单查询
- 输入群组ID
- 选择日期范围
- 查看详细记录和统计

### Web后台管理
- 用户管理
- 授权会员
- 群组管理
- 套餐设置

---

**版本**: 1.0.0  
**最后更新**: 2025-11-05
