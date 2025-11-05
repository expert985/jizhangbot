# Telegram 记账机器人

一个功能完整的 Telegram 记账机器人，支持多币种记账、单笔自定义汇率、会员管理、OKPAY支付集成、Web账单查询和后台管理等功能。

## 🎯 功能特性

### 📝 核心记账功能
- **快速记账**：支持多种输入格式
  - 入款：`+100`、`入款100`、`上行100`
  - 出款：`-100`、`出款100`、`下发100`
  - 余额调整：`余额+100`、`余额-100`
  - USDT记账：金额后加`u`（如`+100u`）
  - 支持小数：`+100.5`、`-88.88`

- **🆕 单笔自定义汇率**：
  - `+100 7.12` - 入款100，汇率7.12
  - `-200 7.15` - 出款200，汇率7.15
  - `+100u 7.12` - 入款100 USDT，汇率7.12
  - `余额+50 7.2` - 余额增加50，汇率7.2
  - 不指定汇率则使用群组默认汇率
  - 每笔交易独立记录汇率，方便追溯

### 📊 数据统计查询
- 发送 `查` 或 `c` 查看：
  - 入款总额及明细
  - 出款总额及明细
  - 余额调整记录
  - 当前余额
  - 未下发金额
  - 手续费自动计算
  - 显示默认汇率信息

### ⚙️ 参数配置
- `设置汇率 7.2` - 设置群组默认汇率
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

#### 授权方式
1. **用户申请试用**（🆕）
   - 用户发送 `申请试用` 或点击主菜单"🎁 申请试用"按钮
   - 管理员收到通知，包含用户详细信息和授权命令
   - 管理员审核后授权，用户自动收到通知

2. **管理员命令授权**
   - 英文命令：`/authorize @用户名 30` 或 `/authorize 用户ID 30`
   - 🆕 中文命令：`授权 用户ID 天数`（例如：`授权 123456789 30天`）
   - 授权后自动通知用户

3. **用户自助购买**
   - `/buy` 或点击"💎 购买会员"按钮
   - 支持30天、90天、365天套餐
   - 通过OKPAY支付USDT

#### 管理员命令
- **英文命令**：
  - `/authorize @用户名 30` - 授权用户30天
  - `/membership @用户名` - 查询会员到期时间

- **🆕 中文命令**：
  - `授权 123456789 30天` - 授权用户30天
  - `会员到期时间 123456789` - 查询会员到期时间
  - 显示格式：`27437天2小时`

#### 套餐价格设置
在 `.env` 文件中配置：
```env
MEMBERSHIP_PRICE_30_DAYS=10    # 30天套餐价格（USDT）
MEMBERSHIP_PRICE_90_DAYS=25    # 90天套餐价格（USDT）
MEMBERSHIP_PRICE_365_DAYS=80   # 365天套餐价格（USDT）
```

### 🎛️ 主菜单按钮（内联按钮）

#### 未开通会员用户菜单
- **🎁 申请试用** - 申请试用会员，通知管理员审核
- **💎 购买会员** - 选择套餐购买会员
- **📖 使用教程** - 查看详细使用说明
- **📊 查看统计** - 查看记账统计（需在群组中使用）
- **🌐 Web账单查询** - 访问Web账单查询系统
- **🎛️ 管理后台** - 访问Web后台管理系统

#### 已开通会员用户菜单
- **💎 续费会员** - 续费或升级套餐
- **👤 我的信息** - 查看会员状态、到期时间
- **📖 使用教程** - 查看详细使用说明
- **📊 查看统计** - 查看记账统计
- **🌐 Web账单查询** - 访问Web账单查询系统
- **🎛️ 管理后台** - 访问Web后台管理系统

#### 管理员专属菜单
- **⚙️ 管理员面板** - 进入管理员控制面板

### 🛠️ 管理员面板按钮

点击"⚙️ 管理员面板"后显示：
- **👥 用户列表** - 查看总用户数、活跃会员统计
- **💎 授权会员** - 查看授权命令格式和说明
- **🏢 群组列表** - 查看总群组数、总记账数统计
- **📊 统计数据** - 实时系统统计（用户、会员、群组、记账）
- **💰 支付记录** - 查看支付订单统计
- **⚙️ 系统设置** - 查看套餐价格、端口配置
- **🔙 返回主菜单** - 返回主菜单

### 🌐 Web账单查询系统（端口52000）

**访问地址**：`http://your-server:52000`

**专业设计特点**：
- **金黑配色主题**：金色渐变 + 黑色背景，专业商务风格
- **动态粒子背景**：飘动的金色粒子动画效果
- **闪光动画**：标题和未下发金额自动闪光提示
- **浮动动效**：统计卡片浮动动画
- **实时统计**：
  - 💰 入款总额
  - 💸 出款总额
  - 🔄 余额调整
  - 💵 当前余额
  - ⚠️ 未下发金额（红色警告，超过0自动弹窗提示）

**功能特性**：
- 输入群组ID查询记账记录
- 选择日期范围（今天/昨天/最近7天/最近30天/全部）
- 详细记录表格展示，序号格式：入1、入2、出1、出2
- 导出Excel/CSV功能
- 未下发金额警告弹窗（5秒自动关闭）
- 响应式设计，支持移动端
- URL参数支持：`?group=群组ID` 自动查询

### 🎛️ Web后台管理系统（端口38888）

**访问地址**：`http://your-server:38888`

**默认账号**：
```
用户名: admin
密码: 123456
```
（可在 `.env` 文件中修改）

**管理功能模块**：

#### 1. 📊 统计面板
- 总用户数
- 活跃会员数
- 总群组数
- 今日记账数
- 总支付订单数
- 实时统计时间

#### 2. 👥 用户管理
- 查看所有用户列表
- 用户会员状态
- 会员到期时间
- 剩余天数显示

#### 3. 💎 授权会员
- Web界面快速授权用户
- 支持用户名或用户ID搜索
- 输入授权天数
- 一键授权，自动通知用户
- 显示授权命令格式

#### 4. 🏢 群组管理
- 查看所有群组列表
- 群组名称、ID
- 群组记账数量
- 群组状态

#### 5. 💰 支付记录
- 所有支付订单
- 订单状态（待支付/已支付/失败）
- 订单金额、币种
- 购买套餐天数
- 支付用户ID

#### 6. ⚙️ 套餐设置
- 查看当前套餐价格配置
- 30天/90天/365天套餐价格
- Web服务端口配置
- 修改提示（修改.env文件）

### 🔐 权限体系
- **管理员**：全部权限，管理员面板访问权限
- **操作员**：记账、参数设置、撤销自己的记录
- **会员用户**：使用记账功能、查看统计
- **普通用户**：需要购买会员或申请试用

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

# 默认货币和汇率
DEFAULT_CURRENCY=CNY
DEFAULT_EXCHANGE_RATE=7.2
DEFAULT_FEE_RATE=0.01
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

### 基础使用流程
1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 开始使用
3. 点击"🎁 申请试用"或"💎 购买会员"
4. 等待管理员授权或完成支付
5. 将机器人添加到群组
6. 开始记账！

### 记账示例

**基本记账**：
```
+1000          # 入款1000（使用默认汇率）
-500           # 出款500（使用默认汇率）
+100u          # 入款100 USDT
余额+50        # 余额增加50
```

**自定义汇率记账**：
```
+1000 7.12     # 入款1000，本笔汇率7.12
-500 7.15      # 出款500，本笔汇率7.15
+100u 7.12     # 入款100 USDT，汇率7.12
余额+50 7.2    # 余额增加50，汇率7.2
入款1000 7.18  # 入款1000，汇率7.18
出款500 7.15   # 出款500，汇率7.15
```

**群组设置**：
```
设置汇率 7.2   # 设置默认汇率
设置费率 0.01  # 设置手续费率
设置币种 CNY   # 设置币种
查             # 查看统计
```

### 申请试用流程

**用户操作**：
1. 发送 `申请试用` 或点击"🎁 申请试用"按钮
2. 收到确认消息："✅ 您的试用申请已提交"
3. 等待管理员审核
4. 审核通过后收到通知："🎉 管理员已为您授权使用 X天"

**管理员操作**：
1. 收到试用申请通知：
   ```
   📋 申请试用
   用户ID：123456789
   用户名：username
   用户名称：User Name

   💡 授权命令：
   授权 123456789 天数
   ```
2. 发送中文授权命令：`授权 123456789 7天`
3. 用户自动收到授权通知

### 管理员操作

**通过Telegram机器人授权**：

英文命令：
```
/authorize @jdccc 30      # 授权用户30天
/membership @jdccc        # 查询会员到期时间
```

中文命令（🆕）：
```
授权 123456789 30天              # 授权用户30天
会员到期时间 123456789           # 查询会员到期时间
```

返回示例：
```
✅ 已成功授权用户 JDCCC (123456789) 30天
到期时间: 2025-12-05 23:59:59

剩余时间: 30天0小时
```

**通过Web后台授权**：
1. 访问 `http://your-server:38888`
2. 登录后台
3. 点击"授权会员"标签
4. 输入用户ID和天数
5. 点击授权
6. 用户自动收到授权通知

**通过管理员面板**：
1. 点击"⚙️ 管理员面板"按钮
2. 选择相应功能：
   - 👥 用户列表 - 查看用户统计
   - 💎 授权会员 - 查看授权命令
   - 🏢 群组列表 - 查看群组统计
   - 📊 统计数据 - 查看实时数据
   - 💰 支付记录 - 查看订单
   - ⚙️ 系统设置 - 查看配置

### Web账单查询使用

**方法一：手动查询**
1. 访问 `http://your-server:52000`
2. 输入群组ID（Telegram群组ID，负数）
3. 选择日期范围
4. 点击"查询账单"
5. 查看详细统计和记录列表

**方法二：URL直达**
```
http://your-server:52000/?group=-1001234567890
```
自动加载指定群组的账单

**查看未下发提醒**：
- 当未下发金额 > 0时，自动弹出警告窗口
- 5秒后自动关闭
- 未下发金额以红色闪光显示

**导出数据**：
- 点击"导出Excel"按钮
- 或点击"导出CSV"按钮
- 保存账单数据到本地

### 群组管理
- 群组创建者自动成为操作员
- 管理员可以添加更多操作员
- 每个群组独立设置和记录
- 群组ID可通过 @userinfobot 获取

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
├── .env              # 环境变量配置（需创建）
├── README.md         # 项目文档
├── bookkeeping.db    # SQLite数据库（自动生成）
└── logs/             # 日志目录（自动生成）
    ├── webhook.log
    ├── web_bill.log
    └── web_admin.log
```

## 💾 数据库说明

项目使用 SQLite 数据库，所有数据存储在 `bookkeeping.db` 文件中。

**数据表结构**：
- `users` - 用户信息和会员状态
  - telegram_id, username, membership_expires_at, is_admin
- `group_chats` - 群组信息
  - telegram_id, title, is_active, owner_id
- `group_settings` - 群组配置
  - currency, exchange_rate, fee_rate, merchant_id, calculator_enabled
- `group_operators` - 群组操作员
  - group_id, user_id
- `bookkeeping_records` - 记账记录
  - record_type, amount, currency, is_usdt, **exchange_rate** (🆕), message_id
- `payments` - 支付记录
  - order_id, unique_id, amount, days, status, pay_user_id

## 🎨 支持的币种

CNY, USD, JPY, EUR, GBP, HKD, KRW, SGD, THB, PHP, MYR, IDR, VND, TWD, AUD, CAD, NZD, CHF, SEK, DKK, NOK, RUB, INR, BRL, MXN, ZAR, TRY, AED, SAR, USDT

共支持 30+ 种货币

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

### Q: 单笔汇率和默认汇率有什么区别？
A:
- **默认汇率**：通过 `设置汇率 7.2` 设置，群组所有交易默认使用
- **单笔汇率**：在记账时指定（如 `+100 7.12`），仅对本笔交易有效
- **优先级**：单笔汇率 > 默认汇率
- **记录显示**：
  - 指定单笔汇率：显示"💱 汇率：7.12"
  - 使用默认汇率：显示"💱 汇率：7.2 (默认)"

### Q: 申请试用后多久能收到回复？
A: 管理员收到通知后会尽快审核，审核通过后您会立即收到授权通知。

### Q: Web后台无法访问？
A: 检查：
1. 服务是否正常启动（查看 logs/web_admin.log）
2. 防火墙是否开放38888端口
3. 是否使用正确的IP地址
4. 浏览器是否支持（建议使用Chrome/Firefox）

### Q: OKPAY支付回调不工作？
A: 确保：
1. 服务器防火墙开放了8443端口
2. 在OKPAY后台正确配置了回调地址
3. webhook服务器正常运行（查看 logs/webhook.log）
4. 回调地址使用HTTPS（生产环境）

### Q: 如何修改套餐价格？
A: 编辑 `.env` 文件中的以下配置：
```env
MEMBERSHIP_PRICE_30_DAYS=10
MEMBERSHIP_PRICE_90_DAYS=25
MEMBERSHIP_PRICE_365_DAYS=80
```
修改后重启机器人生效。

### Q: 如何备份数据？
A:
1. 停止所有服务：`./stop.sh`
2. 备份 `bookkeeping.db` 文件
3. 重新启动服务：`./start.sh`

建议定期自动备份：
```bash
# 添加到crontab
0 2 * * * cp /path/to/bookkeeping.db /path/to/backup/bookkeeping_$(date +\%Y\%m\%d).db
```

### Q: 支持多个管理员吗？
A: 支持，在 `.env` 中用逗号分隔多个管理员ID：
```env
ADMIN_IDS=123456789,987654321,456789123
```

### Q: 忘记Web后台密码怎么办？
A: 在 `.env` 文件中修改 `WEB_ADMIN_PASSWORD` 配置，然后重启服务：
```bash
./stop.sh
./start.sh
```

### Q: 如何查看运行日志？
A:
```bash
# 查看webhook日志
tail -f logs/webhook.log

# 查看Web账单日志
tail -f logs/web_bill.log

# 查看Web后台日志
tail -f logs/web_admin.log

# 查看机器人日志（如果使用start.sh启动）
tail -f logs/bot.log
```

### Q: 支持Docker部署吗？
A: 当前版本暂不支持，计划在后续版本中添加 Docker 支持。

## 🔒 安全建议

1. **保护配置文件**：妥善保管 `.env` 文件，不要泄露给他人
2. **使用强密码**：Web后台使用强密码（至少8位，包含字母数字符号）
3. **HTTPS配置**：生产环境使用HTTPS配置webhook
4. **定期备份**：设置自动定期备份数据库
5. **及时更新**：保持Python依赖包最新版本
6. **限制访问**：使用nginx反向代理限制Web服务的访问IP
7. **监控日志**：定期检查日志文件，发现异常及时处理
8. **密钥安全**：OKPAY密钥不要在代码中硬编码，使用环境变量

## 🛠️ 技术栈

- **语言**：Python 3.8+
- **Telegram库**：python-telegram-bot 20.7
- **数据库ORM**：SQLAlchemy (async)
- **数据库**：SQLite + aiosqlite
- **Web框架**：Flask
- **HTTP客户端**：aiohttp
- **异步支持**：asyncio
- **环境变量**：python-dotenv
- **支付集成**：OKPAY API

## 📊 开发计划

- [x] 核心记账功能
- [x] 会员管理系统
- [x] OKPAY支付集成
- [x] Web账单查询
- [x] Web后台管理
- [x] 单笔自定义汇率 (🆕)
- [x] 试用申请功能 (🆕)
- [x] 中文授权命令 (🆕)
- [x] 内联按钮界面 (🆕)
- [ ] 数据导出优化（详细Excel报表）
- [ ] 多语言支持（英文/中文切换）
- [ ] 更多支付方式（支付宝、微信）
- [ ] 图表统计分析（可视化图表）
- [ ] API接口开放
- [ ] Docker部署支持
- [ ] 移动端App

## 🆕 更新日志

### v2.0.0 (2025-11-05)
- ✨ 新增单笔交易自定义汇率功能
- ✨ 新增用户试用申请功能
- ✨ 新增中文授权命令（授权、会员到期时间）
- 🎨 重新设计主菜单，全面采用内联按钮
- 🎨 新增管理员面板按钮
- 💄 优化Web账单查询界面，金黑配色主题
- 💄 添加动态粒子背景和闪光动画
- 🐛 修复汇率显示问题
- 📝 更新完整文档

### v1.0.0 (2025-11-04)
- 🎉 初始版本发布
- ✨ 核心记账功能
- ✨ 会员管理系统
- ✨ OKPAY支付集成
- ✨ Web账单查询系统
- ✨ Web后台管理系统

## 📜 许可证

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## 📞 联系方式

如有问题或建议，请通过以下方式反馈：
- GitHub Issues: [提交问题](https://github.com/your-repo/issues)
- Telegram: @your_contact

## 🙏 致谢

- 参考项目：https://miha.uk/docs/tutor/telegram-bookkeeping-bot/
- OKPAY支付：@okpay (Telegram)
- OKPAY API文档：https://api.okaypay.me/
- Python Telegram Bot：https://python-telegram-bot.org/

## 📸 功能截图预览

### Telegram机器人界面
```
🎉 欢迎使用智能记账机器人！

👤 用户：User Name (@username)
💎 会员状态：❌ 未开通会员

📝 快速记账：
• 入款：+100 或 入款100
• 出款：-100 或 出款100
• 余额：余额+100
• USDT：+100u

📊 查看统计：发送"查"或"c"

💡 点击下方按钮探索更多功能

[🎁 申请试用] [💎 购买会员]
[📖 使用教程] [📊 查看统计]
[🌐 Web账单查询] [🎛️ 管理后台]
```

### 记账确认示例
```
✅ 入款记录已添加
💰 金额：1000 CNY
💱 汇率：7.12
```

### 查询统计示例
```
📊 今日记账统计

💰 入款总额：5000.00 CNY
💸 出款总额：3000.00 CNY
🔄 余额调整：+100.00 CNY
💵 当前余额：2100.00 CNY
🎯 未下发：2000.00 CNY
💳 手续费(1%)：30.00 CNY

⚙️ 当前设置：
• 币种：CNY
• 默认汇率：7.2
• 费率：1%

💡 单笔交易可使用自定义汇率（如：+100 7.12）
```

### Web账单查询界面
- 金色渐变标题
- 动态粒子背景
- 统计卡片浮动效果
- 未下发金额红色闪光警告
- 详细记录表格（入1、入2、出1、出2）
- 导出Excel/CSV按钮

### Web后台管理界面
- 简洁的登录页面
- 实时数据统计仪表盘
- 用户管理表格
- 授权操作界面
- 群组列表展示
- 支付记录查询

---

**当前版本**: v2.0.0
**最后更新**: 2025-11-05
**Python版本要求**: 3.8+
**数据库**: SQLite

**开发者**: Your Name
**项目地址**: https://github.com/your-repo/jizhangbot
